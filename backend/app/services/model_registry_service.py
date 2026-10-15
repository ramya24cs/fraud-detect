
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.audit_log import AuditLog
from backend.app.models.model_registry import ModelRegistry
from backend.app.models.user import User

# Member 1 final held-out test metrics for model version xgb-cost-v1
# (42,721 test transactions). Source: ml/reports/final_test_results.csv
# and ml/reports/member1_handoff.md. Do not recompute or substitute.
XGB_COST_V1_VERSION = "xgb-cost-v1"
XGB_COST_V1_METRICS: dict[str, float] = {
    "precision": 0.8125,
    "recall": 0.7500,
    "f1_score": 0.7800,
    "pr_auc": 0.768924,
    "roc_auc": 0.978265,
}


def get_current_model(db: Session) -> ModelRegistry | None:
    return db.scalar(
        select(ModelRegistry)
        .where(ModelRegistry.active.is_(True))
        .order_by(ModelRegistry.trained_at.desc())
    )


def ensure_model_metrics(
    db: Session,
    version: str,
    metrics: dict[str, Any],
) -> ModelRegistry:
    """Idempotently set metrics_json for an existing registry version.

    Does not create rows, change active flags, or modify other versions.
    """
    model = db.scalar(
        select(ModelRegistry).where(ModelRegistry.version == version)
    )

    if model is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model version '{version}' is not registered.",
        )

    if model.metrics_json == metrics:
        return model

    was_active = model.active
    model.metrics_json = dict(metrics)
    db.flush()

    # Guard against accidental active-flag drift during the update.
    if model.active != was_active:
        model.active = was_active
        db.flush()

    db.commit()
    db.refresh(model)
    return model


def ensure_xgb_cost_v1_metrics(db: Session) -> ModelRegistry:
    """Populate Member 1 evaluation metrics for the production baseline."""
    return ensure_model_metrics(
        db=db,
        version=XGB_COST_V1_VERSION,
        metrics=XGB_COST_V1_METRICS,
    )


def register_model(
    db: Session,
    version: str,
    artifact_path: str,
    metrics: dict[str, Any] | None,
    current_user: User,
) -> ModelRegistry:
    version = version.strip()
    artifact_path = artifact_path.strip()

    if not version or not artifact_path:
        raise HTTPException(
            status_code=422,
            detail="Model version and artifact path are required.",
        )

    existing = db.scalar(
        select(ModelRegistry).where(ModelRegistry.version == version)
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="This model version is already registered.",
        )

    try:
        model = ModelRegistry(
            version=version,
            artifact_path=artifact_path,
            trained_at=datetime.now(timezone.utc),
            metrics_json=metrics,
            active=False,
        )

        db.add(model)
        db.flush()

        db.add(
            AuditLog(
                user_id=current_user.id,
                action="REGISTER_MODEL",
                entity_type="model_registry",
                entity_id=str(model.id),
                metadata_json={"version": version},
            )
        )

        db.commit()
        db.refresh(model)
        return model

    except Exception:
        db.rollback()
        raise


def activate_model(
    db: Session,
    version: str,
    current_user: User,
) -> ModelRegistry:
    model = db.scalar(
        select(ModelRegistry).where(ModelRegistry.version == version)
    )

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Model version is not registered.",
        )

    artifact = Path(model.artifact_path)

    if not artifact.is_absolute():
        artifact = Path(settings.MODEL_DIR) / artifact

    if not artifact.is_file():
        raise HTTPException(
            status_code=409,
            detail="The registered model artifact does not exist.",
        )

    try:
        active_models = db.scalars(
            select(ModelRegistry)
            .where(ModelRegistry.active.is_(True))
            .with_for_update()
        ).all()

        for active_model in active_models:
            active_model.active = False

        model.active = True
        db.flush()

        db.add(
            AuditLog(
                user_id=current_user.id,
                action="ACTIVATE_MODEL",
                entity_type="model_registry",
                entity_id=str(model.id),
                metadata_json={"version": version},
            )
        )

        db.commit()
        db.refresh(model)
        return model

    except Exception:
        db.rollback()
        raise
