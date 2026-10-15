
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.dashboard import DashboardCost, DashboardSummary
from backend.app.services.dashboard_service import (
    get_dashboard_cost,
    get_dashboard_summary,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummary:
    return get_dashboard_summary(db, current_user.id)


@router.get("/cost", response_model=DashboardCost)
def dashboard_cost(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardCost:
    return get_dashboard_cost(db, current_user.id)
