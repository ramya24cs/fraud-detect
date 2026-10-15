
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.db.session import get_db
from backend.app.models.model_registry import ModelRegistry
from backend.app.models.user import User
from backend.app.services.model_registry_service import get_current_model


router = APIRouter(prefix="/models", tags=["Models"])


class CurrentModelResponse(BaseModel):
    id: UUID
    version: str
    artifact_path: str
    trained_at: datetime
    metrics_json: dict[str, Any] | None
    active: bool

    model_config = ConfigDict(from_attributes=True)


class ModelListItem(BaseModel):
    id: UUID
    version: str
    artifact_path: str
    trained_at: datetime
    metrics_json: dict[str, Any] | None
    active: bool

    model_config = ConfigDict(from_attributes=True)


class ModelListResponse(BaseModel):
    items: list[ModelListItem]
    total: int
    limit: int
    offset: int


@router.get("/current", response_model=CurrentModelResponse)
def current_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CurrentModelResponse:
    model = get_current_model(db)

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="No active model is registered.",
        )

    return CurrentModelResponse.model_validate(model)


@router.get("", response_model=ModelListResponse)
def list_models(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    # Read-only history for operators; register/activate stay ADMIN-only.
    current_user: User = Depends(require_roles("ADMIN", "OPERATOR")),
) -> ModelListResponse:
    if not 1 <= limit <= 200:
        raise HTTPException(
            status_code=422,
            detail="limit must be between 1 and 200.",
        )

    if offset < 0:
        raise HTTPException(
            status_code=422,
            detail="offset must be non-negative.",
        )

    total = db.scalar(
        select(__import__("sqlalchemy").func.count())
        .select_from(ModelRegistry)
    ) or 0

    models = db.scalars(
        select(ModelRegistry)
        .order_by(
            ModelRegistry.trained_at.desc(),
            ModelRegistry.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    ).all()

    return ModelListResponse(
        items=[ModelListItem.model_validate(model) for model in models],
        total=int(total),
        limit=limit,
        offset=offset,
    )
