
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.app.schemas.feedback import FeedbackRequest
from backend.app.services.audit_log_service import get_audit_logs
from backend.app.services.feedback_service import submit_feedback
from backend.app.services.model_registry_service import (
    activate_model,
    register_model,
)


def test_register_model_rejects_blank_version():
    db = MagicMock()
    user = SimpleNamespace(id=uuid4())

    with pytest.raises(HTTPException) as exc_info:
        register_model(
            db=db,
            version="   ",
            artifact_path="model.pkl",
            metrics=None,
            current_user=user,
        )

    assert exc_info.value.status_code == 422
    db.commit.assert_not_called()


def test_register_model_rejects_duplicate_version():
    db = MagicMock()
    db.scalar.return_value = SimpleNamespace(version="v1")
    user = SimpleNamespace(id=uuid4())

    with pytest.raises(HTTPException) as exc_info:
        register_model(
            db=db,
            version="v1",
            artifact_path="model.pkl",
            metrics=None,
            current_user=user,
        )

    assert exc_info.value.status_code == 409
    db.commit.assert_not_called()


def test_activate_model_rejects_unknown_version():
    db = MagicMock()
    db.scalar.return_value = None
    user = SimpleNamespace(id=uuid4())

    with pytest.raises(HTTPException) as exc_info:
        activate_model(
            db=db,
            version="missing-version",
            current_user=user,
        )

    assert exc_info.value.status_code == 404
    db.commit.assert_not_called()


def test_feedback_rejects_unknown_transaction():
    db = MagicMock()
    db.scalar.return_value = None
    user = SimpleNamespace(id=uuid4())

    request = FeedbackRequest(
        transaction_id=uuid4(),
        operator_decision="CONFIRMED_FRAUD",
        reason_code="MANUAL_REVIEW",
    )

    with pytest.raises(HTTPException) as exc_info:
        submit_feedback(
            db=db,
            request=request,
            current_user=user,
        )

    assert exc_info.value.status_code == 404
    db.commit.assert_not_called()


def test_audit_log_listing_returns_logs_and_total():
    db = MagicMock()
    db.scalar.return_value = 0
    db.scalars.return_value.all.return_value = []

    logs, total = get_audit_logs(
        db=db,
        limit=10,
        offset=0,
        action=None,
        user_id=None,
    )

    assert logs == []
    assert total == 0
    db.scalar.assert_called_once()
    db.scalars.assert_called_once()

from pathlib import Path


def test_activate_model_rejects_missing_artifact(monkeypatch, tmp_path):
    from backend.app.services import model_registry_service

    db = MagicMock()
    user = SimpleNamespace(id=uuid4())
    model = SimpleNamespace(
        version="test-v2",
        artifact_path="missing-model.pkl",
        active=False,
    )
    db.scalar.return_value = model

    monkeypatch.setattr(
        model_registry_service.settings,
        "MODEL_DIR",
        str(tmp_path),
    )

    with pytest.raises(HTTPException) as exc_info:
        activate_model(
            db=db,
            version="test-v2",
            current_user=user,
        )

    assert exc_info.value.status_code == 409
    db.commit.assert_not_called()


def test_register_model_rolls_back_when_flush_fails():
    db = MagicMock()
    db.scalar.return_value = None
    db.flush.side_effect = RuntimeError("Simulated database failure")
    user = SimpleNamespace(id=uuid4())

    with pytest.raises(RuntimeError, match="Simulated database failure"):
        register_model(
            db=db,
            version="test-v3",
            artifact_path="model.pkl",
            metrics=None,
            current_user=user,
        )

    db.rollback.assert_called_once()
    db.commit.assert_not_called()
