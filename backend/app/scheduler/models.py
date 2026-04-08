"""Scheduler data models."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
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
    cron_expression: Optional[str] = None  # For cron type
    run_at: Optional[datetime] = None  # For once type
    time_of_day: Optional[str] = None  # HH:MM format for daily/weekly
    day_of_week: Optional[int] = None  # 0-6 for weekly (0=Monday)
    day_of_month: Optional[int] = None  # 1-31 for monthly
    interval_minutes: Optional[int] = None  # For interval-based


class TaskAction(BaseModel):
    """Action to execute when task runs."""
    type: str  # chat, tool, skill, notify
    params: Dict[str, Any] = Field(default_factory=dict)


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
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    schedule: Optional[ScheduleConfig] = None
    action: Optional[TaskAction] = None
    enabled: Optional[bool] = None


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
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    last_status: Optional[TaskStatus] = None
    last_error: Optional[str] = None
    
    class Config:
        from_attributes = True


class TaskExecution(BaseModel):
    """Task execution record."""
    id: str
    task_id: str
    user_id: int
    status: TaskStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskStats(BaseModel):
    """Task statistics."""
    total_tasks: int
    active_tasks: int
    by_type: Dict[str, int]
    today_executions: int
    recent_failures: int
