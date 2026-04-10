"""Token usage API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, User
from app.api.v1.auth import get_current_user
from app.services.token_usage.service import TokenUsageService
from app.services.token_usage.models import (
    TokenUsageSummary,
    TokenUsageRecord,
    TokenUsageByModel,
)

router = APIRouter()


@router.get("/summary", response_model=TokenUsageSummary)
async def get_summary(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated token usage summary."""
    service = TokenUsageService(db)
    return await service.get_summary(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/daily", response_model=list[TokenUsageRecord])
async def get_daily(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get daily token usage records."""
    service = TokenUsageService(db)
    return await service.get_daily(user_id=current_user.id, days=days)


@router.get("/models", response_model=list[TokenUsageByModel])
async def get_by_models(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get token usage broken down by model."""
    service = TokenUsageService(db)
    summary = await service.get_summary(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )
    return summary.by_model


@router.get("/cost")
async def get_cost(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get total cost for a date range."""
    service = TokenUsageService(db)
    cost = await service.get_cost(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )
    return {"cost": cost, "currency": "USD"}
