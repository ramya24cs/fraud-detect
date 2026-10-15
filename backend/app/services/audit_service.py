
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.audit_log import AuditLog


def record_audit_event(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str,
    user_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Add an audit event to the current database transaction."""
    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata,
    )
    db.add(audit_entry)
    db.flush()
    return audit_entry
