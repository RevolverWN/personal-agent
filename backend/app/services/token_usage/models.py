"""Pydantic models for token usage tracking."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class TokenUsageRecord(BaseModel):
    """Single token usage record (DB row / API response)."""

    id: Optional[int] = None
    user_id: int
    model: str
    provider: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    session_id: Optional[str] = None
    created_at: Optional[datetime] = None
    date: Optional[str] = None  # YYYY-MM-DD

    class Config:
        from_attributes = True


class TokenUsageByModel(BaseModel):
    """Aggregated stats for a single model."""

    model: str
    provider: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    call_count: int = 0
    cost: float = 0.0


class TokenUsageByDate(BaseModel):
    """Aggregated stats for a single date."""

    date: str  # YYYY-MM-DD
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    call_count: int = 0
    cost: float = 0.0


class TokenUsageByProvider(BaseModel):
    """Aggregated stats for a single provider."""

    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    call_count: int = 0
    cost: float = 0.0


class TokenUsageSummary(BaseModel):
    """Full token usage summary with breakdowns."""

    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_calls: int = 0
    total_cost: float = 0.0
    by_model: list[TokenUsageByModel] = []
    by_date: list[TokenUsageByDate] = []
    by_provider: list[TokenUsageByProvider] = []
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class ModelPricing(BaseModel):
    """Pricing for a single model (per 1K tokens)."""

    input: float
    output: float
