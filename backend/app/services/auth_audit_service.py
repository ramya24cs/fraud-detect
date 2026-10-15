
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.services.audit_service import record_audit_event


def record_auth_event(
    db: Session,
    action: str,
    user_id: UUID,
) -> None:
    """Record an authentication event in the current transaction."""
    allowed_actions = {"USER_REGISTERED", "USER_LOGIN"}

    if action not in allowed_actions:
        raise ValueError("Unsupported authentication audit action.")

    record_audit_event(
        db=db,
        action=action,
        entity_type="user",
        entity_id=str(user_id),
        user_id=user_id,
        metadata={"event": action},
    )
