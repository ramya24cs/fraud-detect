from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TransactionAssessmentRequest(BaseModel):
    amount: float = Field(gt=0, le=1_000_000_000_000)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    occurred_at: datetime
    transaction_type: str = Field(min_length=1, max_length=50)
    merchant: str | None = Field(default=None, max_length=150)
    channel: str = Field(min_length=1, max_length=50)
    reference: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=150)
    remarks: str | None = Field(default=None, max_length=500)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("Currency must be a 3-letter code.")
        return normalized

    @field_validator(
        "merchant",
        "reference",
        "location",
        "remarks",
    )
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("transaction_type", "channel")
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("This field cannot be empty.")
        return normalized


class TransactionAssessmentResponse(BaseModel):
    assessment_id: UUID
    transaction_id: UUID
    amount: float
    currency: str
    occurred_at: datetime
    anomaly_score: int | None
    risk_level: str
    reasons: list[str]
    history_count: int
    review_required: bool
    alert_created: bool
    policy_version: str
    review_notification_status: Literal[
        "NOT_REQUIRED",
        "SENT",
        "NOT_CONFIGURED",
        "FAILED",
    ]
    review_notification_message: str | None
    review_notification_recipient: str | None = None
    review_notification_subject: str | None = None
    review_notification_content: str | None = None
    created_at: datetime


class TransactionAssessmentBatchRequest(BaseModel):
    transactions: list[TransactionAssessmentRequest] = Field(
        min_length=1,
        max_length=100,
    )


class TransactionAssessmentBatchResponse(BaseModel):
    assessments: list[TransactionAssessmentResponse]
    overall_risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    review_notification_status: Literal[
        "NOT_REQUIRED",
        "SENT",
        "NOT_CONFIGURED",
        "FAILED",
    ]
    review_notification_message: str | None
    review_notification_recipient: str | None = None
    review_notification_subject: str | None = None
    review_notification_content: str | None = None


class PendingReviewItem(BaseModel):
    assessment_id: UUID
    transaction_id: UUID
    amount: float
    currency: str
    occurred_at: datetime
    transaction_type: str
    merchant: str | None
    channel: str
    reference: str | None
    location: str | None
    anomaly_score: int
    risk_level: str
    reasons: list[str]
    history_count: int
    created_at: datetime


class PendingReviewList(BaseModel):
    items: list[PendingReviewItem]
    total: int


class AssessmentHistoryItem(PendingReviewItem):
    review_required: bool
    alert_created: bool
    review_decision: Literal["AGREE", "DISAGREE"] | None
    review_comment: str | None
    reviewed_at: datetime | None
    policy_version: str


class AssessmentHistoryList(BaseModel):
    items: list[AssessmentHistoryItem]
    total: int


class ReviewDecisionRequest(BaseModel):
    decision: Literal["AGREE", "DISAGREE"]
    comment: str | None = Field(default=None, max_length=2000)

    @field_validator("comment")
    @classmethod
    def trim_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ReviewDecisionResponse(BaseModel):
    assessment_id: UUID
    transaction_id: UUID
    decision: Literal["AGREE", "DISAGREE"]
    comment: str | None
    reviewed_at: datetime


class RiskAlertItem(BaseModel):
    assessment_id: UUID
    transaction_id: UUID
    reference: str | None
    amount: float
    currency: str
    anomaly_score: int
    risk_level: str
    reasons: list[str]
    created_at: datetime


class RiskAlertList(BaseModel):
    items: list[RiskAlertItem]
    total: int
