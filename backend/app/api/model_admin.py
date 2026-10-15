
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.services.model_registry_service import (
    activate_model,
    register_model,
)


router = APIRouter(
    prefix="/models",
    tags=["Model Administration"],
)


class ModelRegistrationRequest(BaseModel):
    version: str = Field(min_length=1, max_length=100)
    artifact_path: str = Field(min_length=1, max_length=500)
    metrics: dict[str, Any] | None = None


class ModelActivationRequest(BaseModel):
    version: str = Field(min_length=1, max_length=100)


class ModelAdministrationResponse(BaseModel):
    id: str
    version: str
    artifact_path: str
    active: bool


@router.post(
    "/register",
    response_model=ModelAdministrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_model_endpoint(
    request: ModelRegistrationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
) -> ModelAdministrationResponse:
    model = register_model(
        db=db,
        version=request.version.strip(),
        artifact_path=request.artifact_path.strip(),
        metrics=request.metrics,
        current_user=current_user,
    )

    return ModelAdministrationResponse(
        id=str(model.id),
        version=model.version,
        artifact_path=model.artifact_path,
        active=model.active,
    )


@router.post(
    "/activate",
    response_model=ModelAdministrationResponse,
)
def activate_model_endpoint(
    request: ModelActivationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
) -> ModelAdministrationResponse:
    model = activate_model(
        db=db,
        version=request.version.strip(),
        current_user=current_user,
    )

    return ModelAdministrationResponse(
        id=str(model.id),
        version=model.version,
        artifact_path=model.artifact_path,
        active=model.active,
    )
