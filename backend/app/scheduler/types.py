"""Scheduler data models (Pydantic, in-memory MVP)."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────


class ScheduleKind(str, Enum):
    AT = "at"  # one-shot at timestamp
    EVERY = "every"  # fixed interval
    CRON = "cron"  # cron expression


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


# ── Schemas ────────────────────────────────────────────────────────────────


class ScheduleCreate(BaseModel):
    """User input to describe a schedule."""

    kind: ScheduleKind
    at: Optional[datetime] = Field(None, description="Absolute time (for 'at' kind)")
    interval_seconds: Optional[int] = Field(
        None, description="Interval in seconds (for 'every' kind)"
    )
    cron_expr: Optional[str] = Field(
        None, description="Cron expression, e.g. '0 9 * * *' (for 'cron' kind)"
    )
    timezone: Optional[str] = Field(
        None, description="IANA timezone, e.g. 'Asia/Shanghai'"
    )


class TaskCreate(BaseModel):
    """Create a new scheduled task."""

    name: str = Field(..., min_length=1, max_length=200)
    schedule: ScheduleCreate
    payload: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class TaskUpdate(BaseModel):
    """Update fields of an existing task."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    enabled: Optional[bool] = None


class TaskResponse(BaseModel):
    """Full task representation returned by the API."""

    id: str
    name: str
    enabled: bool
    schedule: ScheduleCreate
    payload: Dict[str, Any]
    next_run_at: Optional[datetime] = None
    last_status: Optional[RunStatus] = None
    last_run_at: Optional[datetime] = None
    run_count: int = 0
    created_at: datetime
    updated_at: datetime


class TaskRun(BaseModel):
    """Single execution record."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    task_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    status: RunStatus = RunStatus.RUNNING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
