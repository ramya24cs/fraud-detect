
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.models.audit_log import AuditLog
from backend.app.services.audit_log_service import get_audit_logs


router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


class AuditLogItem(BaseModel):
    id: UUID
    user_id: UUID | None
    action: str
    entity_type: str
    entity_id: str
    metadata_json: dict[str, Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogPage(BaseModel):
    items: list[AuditLogItem]
    total: int
    limit: int
    offset: int


@router.get("", response_model=AuditLogPage)
def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    action: str | None = Query(default=None, max_length=100),
    user_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
) -> AuditLogPage:
    logs, total = get_audit_logs(
        db=db,
        limit=limit,
        offset=offset,
        action=action,
        user_id=user_id,
    )

    return AuditLogPage(
        items=logs,
        total=total,
        limit=limit,
        offset=offset,
    )
