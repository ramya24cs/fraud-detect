
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReviewQueueItem(BaseModel):
    prediction_id: UUID
    transaction_id: UUID
    external_id: str
    amount: float
    fraud_probability: float
    risk_level: str
    decision: str
    expected_cost: float
    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewQueueResponse(BaseModel):
    items: list[ReviewQueueItem]
    total: int
    limit: int
    offset: int
