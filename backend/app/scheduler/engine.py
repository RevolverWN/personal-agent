"""In-memory scheduler engine built on APScheduler."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.scheduler.types import (
    RunStatus,
    ScheduleCreate,
    ScheduleKind,
    TaskCreate,
    TaskResponse,
    TaskRun,
)

logger = logging.getLogger(__name__)


class SchedulerEngine:
    """In-memory task scheduler backed by APScheduler.

    All state lives in dicts — no database required (MVP).
    """

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler(timezone=timezone.utc)
        # task_id -> TaskResponse
        self._tasks: Dict[str, TaskResponse] = {}
        # task_id -> list of TaskRun
        self._runs: Dict[str, List[TaskRun]] = {}

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("SchedulerEngine started")

    async def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("SchedulerEngine stopped")

    # ── Task CRUD ──────────────────────────────────────────────────────────

    async def add_task(self, data: TaskCreate) -> TaskResponse:
        import uuid

        task_id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc)

        task = TaskResponse(
            id=task_id,
            name=data.name,
            schedule=data.schedule,
            payload=data.payload,
            enabled=data.enabled,
            created_at=now,
            updated_at=now,
        )
        self._tasks[task_id] = task
        self._runs[task_id] = []

        if data.enabled:
            self._schedule_job(task_id, data.schedule)

        logger.info("Task added: %s (%s)", task_id, data.name)
        return task

    async def remove_task(self, task_id: str) -> bool:
        task = self._tasks.pop(task_id, None)
        if task is None:
            return False
        self._runs.pop(task_id, None)
        self._unschedule_job(task_id)
        logger.info("Task removed: %s", task_id)
        return True

    async def list_tasks(self) -> List[TaskResponse]:
        return list(self._tasks.values())

    async def get_task(self, task_id: str) -> Optional[TaskResponse]:
        return self._tasks.get(task_id)

    # ── Execution ──────────────────────────────────────────────────────────

    async def run_task(self, task_id: str) -> TaskRun:
        """Manually trigger a task and return the execution record."""
        task = self._tasks.get(task_id)
        if task is None:
            raise KeyError(f"Task {task_id} not found")

        return await self._execute(task_id)

    async def get_task_runs(self, task_id: str) -> List[TaskRun]:
        return list(self._runs.get(task_id, []))

    # ── Internal ───────────────────────────────────────────────────────────

    def _schedule_job(self, task_id: str, schedule: ScheduleCreate) -> None:
        trigger = self._build_trigger(schedule)
        if trigger is None:
            logger.warning("Cannot build trigger for task %s", task_id)
            return

        job_id = f"task_{task_id}"
        self._scheduler.add_job(
            self._fire,
            trigger=trigger,
            id=job_id,
            args=[task_id],
            replace_existing=True,
        )

    def _unschedule_job(self, task_id: str) -> None:
        job_id = f"task_{task_id}"
        try:
            self._scheduler.remove_job(job_id)
        except Exception:
            pass

    def _build_trigger(self, schedule: ScheduleCreate):
        tz = schedule.timezone or "UTC"

        if schedule.kind == ScheduleKind.AT and schedule.at:
            return DateTrigger(run_date=schedule.at, timezone=tz)

        if schedule.kind == ScheduleKind.EVERY and schedule.interval_seconds:
            return IntervalTrigger(
                seconds=schedule.interval_seconds, timezone=tz
            )

        if schedule.kind == ScheduleKind.CRON and schedule.cron_expr:
            # APScheduler expects: minute hour day month day_of_week
            parts = schedule.cron_expr.strip().split()
            if len(parts) == 5:
                return CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4],
                    timezone=tz,
                )

        return None

    async def _fire(self, task_id: str) -> None:
        """Callback from APScheduler — runs in the async loop."""
        try:
            await self._execute(task_id)
        except Exception:
            logger.exception("Error firing task %s", task_id)

    async def _execute(self, task_id: str) -> TaskRun:
        task = self._tasks.get(task_id)
        if task is None:
            raise KeyError(f"Task {task_id} not found")

        run = TaskRun(task_id=task_id, status=RunStatus.RUNNING)
        self._runs[task_id].append(run)

        try:
            # --- MVP payload execution placeholder -------------------------
            # In production, dispatch based on payload["type"] (chat, notify,
            # skill, webhook, etc.). For now just record success.
            result: Dict[str, Any] = {
                "message": f"Task '{task.name}' executed successfully",
                "payload": task.payload,
            }
            # ----------------------------------------------------------------

            run.status = RunStatus.SUCCESS
            run.result = result
        except Exception as exc:
            run.status = RunStatus.FAILED
            run.error = str(exc)
        finally:
            run.finished_at = datetime.now(timezone.utc)
            task.last_status = run.status
            task.last_run_at = run.started_at
            task.run_count += 1
            task.updated_at = datetime.now(timezone.utc)

        return run


# ── Singleton ──────────────────────────────────────────────────────────────

scheduler_engine = SchedulerEngine()
