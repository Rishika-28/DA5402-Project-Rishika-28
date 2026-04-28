from __future__ import annotations

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    store: int = Field(..., ge=1)
    date: str
    day_of_week: int = Field(..., ge=1, le=7)
    open: int = Field(1, ge=0, le=1)
    promo: int = Field(0, ge=0, le=1)
    state_holiday: str = Field("0")
    school_holiday: int = Field(0, ge=0, le=1)


class ForecastResponse(BaseModel):
    predicted_sales: float
    model_name: str
    model_run_id: str
    drift_detected: bool
    inference_latency_ms: float


class FeedbackRequest(BaseModel):
    store: int = Field(..., ge=1)
    date: str
    predicted_sales: float = Field(..., ge=0)
    actual_sales: float = Field(..., ge=0)

