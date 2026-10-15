
from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    total_transactions: int = Field(ge=0)
    total_predictions: int = Field(ge=0)
    review_count: int = Field(ge=0)
    blocked_count: int = Field(ge=0)
    approved_count: int = Field(ge=0)
    feedback_count: int = Field(ge=0)


class DashboardCost(BaseModel):
    total_expected_cost: float
    average_expected_cost: float
    prediction_count: int = Field(ge=0)
