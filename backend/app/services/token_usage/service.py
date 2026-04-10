"""Token usage service — record, query, aggregate."""

from __future__ import annotations

from datetime import date, datetime, timezone, timedelta
from collections import defaultdict
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import TokenUsage
from app.services.token_usage.models import (
    TokenUsageRecord,
    TokenUsageSummary,
    TokenUsageByModel,
    TokenUsageByDate,
    TokenUsageByProvider,
)
from app.services.token_usage.prices import calculate_cost, _infer_provider


class TokenUsageService:
    """Service for recording and querying token usage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        user_id: int,
        session_id: Optional[str] = None,
    ) -> TokenUsageRecord:
        """Record a single token usage event."""
        total_tokens = prompt_tokens + completion_tokens
        provider = _infer_provider(model)
        cost = calculate_cost(model, prompt_tokens, completion_tokens)

        row = TokenUsage(
            user_id=user_id,
            model=model,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            session_id=session_id,
            cost=cost,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)

        return TokenUsageRecord.model_validate(row)

    async def get_summary(
        self,
        user_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> TokenUsageSummary:
        """Get aggregated summary for a user within a date range."""
        conditions = [TokenUsage.user_id == user_id]

        if start_date:
            conditions.append(TokenUsage.created_at >= f"{start_date}T00:00:00Z")
        if end_date:
            conditions.append(TokenUsage.created_at <= f"{end_date}T23:59:59Z")

        result = await self.db.execute(
            select(TokenUsage).where(and_(*conditions))
        )
        rows = result.scalars().all()

        # Aggregate totals
        total_prompt = 0
        total_completion = 0
        total_calls = 0
        total_cost = 0.0

        by_model_map: dict[str, dict] = defaultdict(lambda: {
            "prompt_tokens": 0, "completion_tokens": 0,
            "total_tokens": 0, "call_count": 0, "cost": 0.0, "provider": "",
        })
        by_date_map: dict[str, dict] = defaultdict(lambda: {
            "prompt_tokens": 0, "completion_tokens": 0,
            "total_tokens": 0, "call_count": 0, "cost": 0.0,
        })
        by_provider_map: dict[str, dict] = defaultdict(lambda: {
            "prompt_tokens": 0, "completion_tokens": 0,
            "total_tokens": 0, "call_count": 0, "cost": 0.0,
        })

        for row in rows:
            total_prompt += row.prompt_tokens
            total_completion += row.completion_tokens
            total_calls += 1
            total_cost += row.cost or 0.0

            day = row.created_at.strftime("%Y-%m-%d") if row.created_at else "unknown"

            # by model
            bm = by_model_map[row.model]
            bm["prompt_tokens"] += row.prompt_tokens
            bm["completion_tokens"] += row.completion_tokens
            bm["total_tokens"] += row.total_tokens
            bm["call_count"] += 1
            bm["cost"] += row.cost or 0.0
            bm["provider"] = row.provider

            # by date
            bd = by_date_map[day]
            bd["prompt_tokens"] += row.prompt_tokens
            bd["completion_tokens"] += row.completion_tokens
            bd["total_tokens"] += row.total_tokens
            bd["call_count"] += 1
            bd["cost"] += row.cost or 0.0

            # by provider
            bp = by_provider_map[row.provider]
            bp["prompt_tokens"] += row.prompt_tokens
            bp["completion_tokens"] += row.completion_tokens
            bp["total_tokens"] += row.total_tokens
            bp["call_count"] += 1
            bp["cost"] += row.cost or 0.0

        return TokenUsageSummary(
            total_prompt_tokens=total_prompt,
            total_completion_tokens=total_completion,
            total_tokens=total_prompt + total_completion,
            total_calls=total_calls,
            total_cost=round(total_cost, 4),
            by_model=[
                TokenUsageByModel(
                    model=m, provider=v["provider"],
                    prompt_tokens=v["prompt_tokens"],
                    completion_tokens=v["completion_tokens"],
                    total_tokens=v["total_tokens"],
                    call_count=v["call_count"],
                    cost=round(v["cost"], 4),
                )
                for m, v in sorted(by_model_map.items(), key=lambda x: -x[1]["cost"])
            ],
            by_date=[
                TokenUsageByDate(
                    date=d, prompt_tokens=v["prompt_tokens"],
                    completion_tokens=v["completion_tokens"],
                    total_tokens=v["total_tokens"],
                    call_count=v["call_count"],
                    cost=round(v["cost"], 4),
                )
                for d, v in sorted(by_date_map.items())
            ],
            by_provider=[
                TokenUsageByProvider(
                    provider=p, prompt_tokens=v["prompt_tokens"],
                    completion_tokens=v["completion_tokens"],
                    total_tokens=v["total_tokens"],
                    call_count=v["call_count"],
                    cost=round(v["cost"], 4),
                )
                for p, v in sorted(by_provider_map.items(), key=lambda x: -x[1]["cost"])
            ],
            period_start=start_date,
            period_end=end_date,
        )

    async def get_daily(
        self,
        user_id: int,
        days: int = 30,
    ) -> list[TokenUsageRecord]:
        """Get daily records for the last N days."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(TokenUsage)
            .where(
                and_(
                    TokenUsage.user_id == user_id,
                    TokenUsage.created_at >= since,
                )
            )
            .order_by(TokenUsage.created_at.desc())
        )
        rows = result.scalars().all()
        return [TokenUsageRecord.model_validate(r) for r in rows]

    async def get_cost(
        self,
        user_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> float:
        """Get total cost for a user within a date range."""
        conditions = [TokenUsage.user_id == user_id]
        if start_date:
            conditions.append(TokenUsage.created_at >= f"{start_date}T00:00:00Z")
        if end_date:
            conditions.append(TokenUsage.created_at <= f"{end_date}T23:59:59Z")

        result = await self.db.execute(
            select(func.coalesce(func.sum(TokenUsage.cost), 0)).where(and_(*conditions))
        )
        return round(float(result.scalar()), 4)
