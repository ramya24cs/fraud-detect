
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.feedback import (
    FeedbackListResponse,
    FeedbackRequest,
    FeedbackResponse,
)
from backend.app.services.feedback_service import (
    list_feedback,
    submit_feedback,
)

router = APIRouter(
    prefix="/feedback",
    tags=["Operator Feedback"],
)


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackResponse:
    feedback = submit_feedback(
        db=db,
        request=request,
        current_user=current_user,
    )

    return FeedbackResponse.model_validate(feedback)


@router.get(
    "",
    response_model=FeedbackListResponse,
)
def read_feedback(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    transaction_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackListResponse:
    """List the current user's feedback, optionally filtered by transaction."""

    rows, total = list_feedback(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        transaction_id=transaction_id,
    )

    return FeedbackListResponse(
        items=[FeedbackResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
