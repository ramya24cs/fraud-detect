"""Model monitoring metrics and authorization tests."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.api.deps import get_current_user, get_db, require_roles
from backend.app.main import app
from backend.app.models.model_registry import ModelRegistry
from backend.app.services.model_registry_service import (
    XGB_COST_V1_METRICS,
    XGB_COST_V1_VERSION,
    ensure_model_metrics,
    ensure_xgb_cost_v1_metrics,
    get_current_model,
)


client = TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def _auth_as(role: str):
    user = MagicMock()
    user.id = uuid4()
    user.email = f"{role.lower()}@example.com"
    user.role = role
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: MagicMock()
    return user


def test_ensure_model_metrics_updates_existing_version_only():
    model = ModelRegistry(
        version=XGB_COST_V1_VERSION,
        artifact_path="xgboost_baseline.joblib",
        trained_at=datetime.now(timezone.utc),
        metrics_json={},
        active=True,
    )
    model.id = uuid4()

    db = MagicMock()
    db.scalar.return_value = model

    result = ensure_model_metrics(
        db=db,
        version=XGB_COST_V1_VERSION,
        metrics=XGB_COST_V1_METRICS,
    )

    assert result is model
    assert model.metrics_json == XGB_COST_V1_METRICS
    assert model.active is True
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(model)


def test_ensure_model_metrics_is_idempotent_when_unchanged():
    model = ModelRegistry(
        version=XGB_COST_V1_VERSION,
        artifact_path="xgboost_baseline.joblib",
        trained_at=datetime.now(timezone.utc),
        metrics_json=dict(XGB_COST_V1_METRICS),
        active=True,
    )
    model.id = uuid4()

    db = MagicMock()
    db.scalar.return_value = model

    ensure_model_metrics(
        db=db,
        version=XGB_COST_V1_VERSION,
        metrics=XGB_COST_V1_METRICS,
    )

    db.commit.assert_not_called()


def test_ensure_model_metrics_rejects_unknown_version():
    db = MagicMock()
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        ensure_model_metrics(
            db=db,
            version="unknown-v9",
            metrics=XGB_COST_V1_METRICS,
        )

    assert exc_info.value.status_code == 404


def test_ensure_xgb_cost_v1_metrics_uses_member1_values(monkeypatch):
    captured = {}

    def fake_ensure(db, version, metrics):
        captured["version"] = version
        captured["metrics"] = metrics
        return SimpleNamespace(version=version, metrics_json=metrics)

    monkeypatch.setattr(
        "backend.app.services.model_registry_service.ensure_model_metrics",
        fake_ensure,
    )

    ensure_xgb_cost_v1_metrics(MagicMock())

    assert captured["version"] == "xgb-cost-v1"
    assert captured["metrics"] == {
        "precision": 0.8125,
        "recall": 0.7500,
        "f1_score": 0.7800,
        "pr_auc": 0.768924,
        "roc_auc": 0.978265,
    }


def test_current_model_returns_metrics_json(monkeypatch):
    _auth_as("OPERATOR")

    model = ModelRegistry(
        version=XGB_COST_V1_VERSION,
        artifact_path="xgboost_baseline.joblib",
        trained_at=datetime.now(timezone.utc),
        metrics_json=dict(XGB_COST_V1_METRICS),
        active=True,
    )
    model.id = uuid4()

    from backend.app.api import models as models_api

    monkeypatch.setattr(models_api, "get_current_model", lambda db: model)

    response = client.get("/models/current")

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "xgb-cost-v1"
    assert body["active"] is True
    assert body["metrics_json"] == XGB_COST_V1_METRICS


def test_list_models_allows_operator(monkeypatch):
    _auth_as("OPERATOR")

    model = ModelRegistry(
        version=XGB_COST_V1_VERSION,
        artifact_path="xgboost_baseline.joblib",
        trained_at=datetime.now(timezone.utc),
        metrics_json=dict(XGB_COST_V1_METRICS),
        active=True,
    )
    model.id = uuid4()

    db = MagicMock()
    db.scalar.return_value = 1
    db.scalars.return_value.all.return_value = [model]
    app.dependency_overrides[get_db] = lambda: db

    response = client.get("/models")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["version"] == "xgb-cost-v1"
    assert body["items"][0]["metrics_json"]["precision"] == 0.8125


def test_list_models_rejects_unauthenticated():
    response = client.get("/models")
    assert response.status_code == 401


def test_list_models_role_dependency_accepts_operator_and_admin():
    checker = require_roles("ADMIN", "OPERATOR")
    assert checker(current_user=SimpleNamespace(role="OPERATOR")).role == "OPERATOR"
    assert checker(current_user=SimpleNamespace(role="ADMIN")).role == "ADMIN"


def test_list_models_role_dependency_rejects_unknown_role():
    checker = require_roles("ADMIN", "OPERATOR")
    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=SimpleNamespace(role="GUEST"))
    assert exc_info.value.status_code == 403


def test_register_and_activate_remain_admin_only(monkeypatch):
    _auth_as("OPERATOR")

    register = client.post(
        "/models/register",
        json={
            "version": "other-v1",
            "artifact_path": "other.joblib",
            "metrics": {},
        },
    )
    activate = client.post(
        "/models/activate",
        json={"version": "xgb-cost-v1"},
    )

    assert register.status_code == 403
    assert activate.status_code == 403


def test_active_registry_version_matches_inference_contract():
    """Prediction decision engine and registry share xgb-cost-v1."""
    from ml.src.decision.decision_engine import evaluate_transaction
    from ml.src.decision.defaults import approved_cost_matrix
    from unittest.mock import patch

    tx = {
        "Time": 1.0,
        "Amount": 1.0,
        **{f"V{i}": 0.0 for i in range(1, 29)},
    }

    with patch(
        "ml.src.decision.decision_engine.predict_fraud",
        return_value=0.01,
    ), patch(
        "ml.src.decision.decision_engine.explain_transaction",
        return_value=[],
    ):
        result = evaluate_transaction(
            tx,
            approved_cost_matrix(),
            top_k=1,
        )

    assert result["model_version"] == XGB_COST_V1_VERSION
    assert XGB_COST_V1_VERSION == "xgb-cost-v1"
