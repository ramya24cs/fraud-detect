
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.review_queue import ReviewQueueResponse
from backend.app.services.review_queue_service import get_review_queue


router = APIRouter(
    prefix="/review-queue",
    tags=["Review Queue"],
)


@router.get(
    "",
    response_model=ReviewQueueResponse,
)
def read_review_queue(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewQueueResponse:
    return get_review_queue(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
