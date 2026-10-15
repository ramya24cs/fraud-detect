
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.audit_log import AuditLog


def get_audit_logs(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    action: str | None = None,
    user_id: UUID | None = None,
) -> tuple[list[AuditLog], int]:
    """Return filtered, paginated audit records, newest first."""
    query = select(AuditLog)

    if action:
        query = query.where(AuditLog.action == action.strip())

    if user_id is not None:
        query = query.where(AuditLog.user_id == user_id)

    total_query = (
        select(func.count())
        .select_from(query.subquery())
    )
    total = db.scalar(total_query) or 0

    logs = list(
        db.scalars(
            query.order_by(
                AuditLog.created_at.desc(),
                AuditLog.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        ).all()
    )

    return logs, int(total)
