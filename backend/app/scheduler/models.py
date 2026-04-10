"""Scheduler data models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Types of scheduled tasks."""

    REMINDER = "reminder"
    HEARTBEAT = "heartbeat"
    REPORT = "report"
    CUSTOM = "custom"
    AGENT_TASK = "agent_task"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduleConfig(BaseModel):
    """Schedule configuration."""

    type: str = "once"  # once, daily, weekly, monthly, cron
    cron_expression: str | None = None  # For cron type
    run_at: datetime | None = None  # For once type
    time_of_day: str | None = None  # HH:MM format for daily/weekly
    day_of_week: int | None = None  # 0-6 for weekly (0=Monday)
    day_of_month: int | None = None  # 1-31 for monthly
    interval_minutes: int | None = None  # For interval-based


class TaskAction(BaseModel):
    """Action to execute when task runs."""

    type: str  # chat, tool, skill, notify
    params: dict[str, Any] = Field(default_factory=dict)


class ScheduledTaskCreate(BaseModel):
    """Create a scheduled task."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    task_type: TaskType = TaskType.REMINDER
    schedule: ScheduleConfig
    action: TaskAction
    enabled: bool = True


class ScheduledTaskUpdate(BaseModel):
    """Update a scheduled task."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    schedule: ScheduleConfig | None = None
    action: TaskAction | None = None
    enabled: bool | None = None


class ScheduledTask(BaseModel):
    """Scheduled task model."""

    id: str
    user_id: int
    name: str
    description: str
    task_type: TaskType
    schedule: ScheduleConfig
    action: TaskAction
    enabled: bool
    created_at: datetime
    updated_at: datetime
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    run_count: int = 0
    last_status: TaskStatus | None = None
    last_error: str | None = None

    class Config:
        from_attributes = True


class TaskExecution(BaseModel):
    """Task execution record."""

    id: str
    task_id: str
    user_id: int
    status: TaskStatus
    started_at: datetime
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


class TaskStats(BaseModel):
    """Task statistics."""

    total_tasks: int
    active_tasks: int
    by_type: dict[str, int]
    today_executions: int
    recent_failures: int
