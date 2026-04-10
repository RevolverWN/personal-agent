"""Task scheduler manager."""

import uuid
from datetime import datetime, timedelta
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.scheduler.models import (
    ScheduleConfig,
    ScheduledTask,
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
    TaskAction,
    TaskStats,
    TaskStatus,
)


class TaskScheduler:
    """Manage and execute scheduled tasks."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.scheduler = AsyncIOScheduler()
            self._initialized = True

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()

    # ==================== Task Management ====================

    async def create_task(
        self, db: AsyncSession, user_id: int, task_data: ScheduledTaskCreate
    ) -> ScheduledTask:
        """Create a new scheduled task."""
        from app.models.database import ScheduledTask as TaskDB

        task_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Calculate next run time
        next_run = self._calculate_next_run(task_data.schedule, now)

        db_task = TaskDB(
            id=task_id,
            user_id=user_id,
            name=task_data.name,
            description=task_data.description,
            task_type=task_data.task_type,
            schedule_type=task_data.schedule.type,
            schedule_config=task_data.schedule.model_dump(),
            action_type=task_data.action.type,
            action_params=task_data.action.params,
            enabled=task_data.enabled,
            created_at=now,
            updated_at=now,
            next_run_at=next_run,
            run_count=0,
        )

        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)

        # Schedule the job if enabled
        if task_data.enabled:
            self._schedule_job(task_id, user_id, task_data.schedule, task_data.action)

        return await self._to_model(db_task)

    async def get_task(self, db: AsyncSession, task_id: str, user_id: int) -> ScheduledTask | None:
        """Get a task by ID."""
        from app.models.database import ScheduledTask as TaskDB

        result = await db.execute(
            select(TaskDB).where(and_(TaskDB.id == task_id, TaskDB.user_id == user_id))
        )
        db_task = result.scalar_one_or_none()

        if db_task:
            return await self._to_model(db_task)
        return None

    async def get_user_tasks(
        self, db: AsyncSession, user_id: int, enabled_only: bool = False
    ) -> list[ScheduledTask]:
        """Get all tasks for a user."""
        from app.models.database import ScheduledTask as TaskDB

        query = select(TaskDB).where(TaskDB.user_id == user_id)

        if enabled_only:
            query = query.where(TaskDB.enabled == True)

        query = query.order_by(desc(TaskDB.created_at))

        result = await db.execute(query)
        tasks = result.scalars().all()

        return [await self._to_model(t) for t in tasks]

    async def update_task(
        self, db: AsyncSession, task_id: str, user_id: int, update_data: ScheduledTaskUpdate
    ) -> ScheduledTask | None:
        """Update a task."""
        from app.models.database import ScheduledTask as TaskDB

        result = await db.execute(
            select(TaskDB).where(and_(TaskDB.id == task_id, TaskDB.user_id == user_id))
        )
        db_task = result.scalar_one_or_none()

        if not db_task:
            return None

        # Update fields
        if update_data.name is not None:
            db_task.name = update_data.name
        if update_data.description is not None:
            db_task.description = update_data.description
        if update_data.schedule is not None:
            db_task.schedule_type = update_data.schedule.type
            db_task.schedule_config = update_data.schedule.model_dump()
        if update_data.action is not None:
            db_task.action_type = update_data.action.type
            db_task.action_params = update_data.action.params
        if update_data.enabled is not None:
            db_task.enabled = update_data.enabled

        db_task.updated_at = datetime.utcnow()

        # Recalculate next run if schedule changed
        if update_data.schedule is not None:
            db_task.next_run_at = self._calculate_next_run(update_data.schedule, datetime.utcnow())

        await db.commit()
        await db.refresh(db_task)

        # Reschedule job
        self._remove_job(task_id)
        if db_task.enabled:
            schedule = ScheduleConfig(**db_task.schedule_config)
            action = TaskAction(type=db_task.action_type, params=db_task.action_params)
            self._schedule_job(task_id, user_id, schedule, action)

        return await self._to_model(db_task)

    async def delete_task(self, db: AsyncSession, task_id: str, user_id: int) -> bool:
        """Delete a task."""
        from app.models.database import ScheduledTask as TaskDB

        result = await db.execute(
            select(TaskDB).where(and_(TaskDB.id == task_id, TaskDB.user_id == user_id))
        )
        db_task = result.scalar_one_or_none()

        if not db_task:
            return False

        # Remove scheduled job
        self._remove_job(task_id)

        await db.delete(db_task)
        await db.commit()

        return True

    # ==================== Task Execution ====================

    async def execute_task(self, db: AsyncSession, task_id: str, user_id: int) -> dict[str, Any]:
        """Execute a task immediately."""
        task = await self.get_task(db, task_id, user_id)
        if not task:
            return {"success": False, "error": "Task not found"}

        try:
            result = await self._execute_action(task.action, user_id)

            # Update task stats
            from app.models.database import ScheduledTask as TaskDB

            result_db = await db.execute(select(TaskDB).where(TaskDB.id == task_id))
            db_task = result_db.scalar_one()
            db_task.last_run_at = datetime.utcnow()
            db_task.run_count += 1
            db_task.last_status = TaskStatus.COMPLETED

            # Calculate next run
            schedule = ScheduleConfig(**db_task.schedule_config)
            db_task.next_run_at = self._calculate_next_run(schedule, datetime.utcnow())

            await db.commit()

            return {"success": True, "result": result}

        except Exception as e:
            # Update failure status
            from app.models.database import ScheduledTask as TaskDB

            result_db = await db.execute(select(TaskDB).where(TaskDB.id == task_id))
            db_task = result_db.scalar_one()
            db_task.last_run_at = datetime.utcnow()
            db_task.last_status = TaskStatus.FAILED
            db_task.last_error = str(e)
            await db.commit()

            return {"success": False, "error": str(e)}

    async def _execute_action(self, action: TaskAction, user_id: int) -> Any:
        """Execute a task action."""
        if action.type == "chat":
            # Execute chat action
            from app.agent.core import AgentCore

            agent = AgentCore()

            response = await agent.chat(
                message=action.params.get("message", ""),
                model=action.params.get("model"),
                system_prompt=action.params.get("system_prompt"),
                enable_tools=True,
            )
            return response

        elif action.type == "notify":
            # For notifications, just return the message
            # In production, could integrate with push notifications
            return {
                "notification": action.params.get("message", ""),
                "timestamp": datetime.utcnow().isoformat(),
            }

        elif action.type == "skill":
            # Execute skill action
            from app.skills.manager import skill_manager

            result = await skill_manager.execute_skill(
                action.params.get("skill_name"),
                action.params.get("action"),
                action.params.get("params", {}),
            )
            return result.to_dict()

        else:
            return {"error": f"Unknown action type: {action.type}"}

    # ==================== Scheduler Internals ====================

    def _schedule_job(
        self, task_id: str, user_id: int, schedule: ScheduleConfig, action: TaskAction
    ):
        """Schedule a job with APScheduler."""
        job_id = f"task_{task_id}"

        # Create trigger based on schedule type
        trigger = self._create_trigger(schedule)

        if trigger:
            self.scheduler.add_job(
                func=self._run_scheduled_job,
                trigger=trigger,
                id=job_id,
                args=[task_id, user_id],
                replace_existing=True,
            )

    def _remove_job(self, task_id: str):
        """Remove a scheduled job."""
        job_id = f"task_{task_id}"
        try:
            self.scheduler.remove_job(job_id)
        except:
            pass

    def _create_trigger(self, schedule: ScheduleConfig):
        """Create APScheduler trigger from schedule config."""
        if schedule.type == "once" and schedule.run_at:
            return DateTrigger(run_date=schedule.run_at)

        elif schedule.type == "daily" and schedule.time_of_day:
            hour, minute = map(int, schedule.time_of_day.split(":"))
            return CronTrigger(hour=hour, minute=minute)

        elif schedule.type == "weekly" and schedule.day_of_week is not None:
            hour, minute = map(int, schedule.time_of_day.split(":"))
            return CronTrigger(day_of_week=schedule.day_of_week, hour=hour, minute=minute)

        elif schedule.type == "cron" and schedule.cron_expression:
            # Parse cron expression
            parts = schedule.cron_expression.split()
            if len(parts) == 5:
                return CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4],
                )

        elif schedule.type == "interval" and schedule.interval_minutes:
            return IntervalTrigger(minutes=schedule.interval_minutes)

        return None

    async def _run_scheduled_job(self, task_id: str, user_id: int):
        """Wrapper for scheduled job execution."""
        # Create new DB session for this job
        from app.models.database import async_session_maker

        async with async_session_maker() as db:
            await self.execute_task(db, task_id, user_id)

    def _calculate_next_run(self, schedule: ScheduleConfig, base_time: datetime) -> datetime | None:
        """Calculate next run time for a schedule."""
        if schedule.type == "once":
            return schedule.run_at

        elif schedule.type == "daily":
            hour, minute = map(int, schedule.time_of_day.split(":"))
            next_run = base_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= base_time:
                next_run += timedelta(days=1)
            return next_run

        elif schedule.type == "weekly":
            # This is simplified - proper implementation would calculate next occurrence
            return base_time + timedelta(days=7)

        elif schedule.type == "interval" and schedule.interval_minutes:
            return base_time + timedelta(minutes=schedule.interval_minutes)

        return None

    async def _to_model(self, db_task) -> ScheduledTask:
        """Convert DB task to model."""
        return ScheduledTask(
            id=db_task.id,
            user_id=db_task.user_id,
            name=db_task.name,
            description=db_task.description,
            task_type=db_task.task_type,
            schedule=ScheduleConfig(**db_task.schedule_config),
            action=TaskAction(type=db_task.action_type, params=db_task.action_params),
            enabled=db_task.enabled,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at,
            last_run_at=db_task.last_run_at,
            next_run_at=db_task.next_run_at,
            run_count=db_task.run_count,
            last_status=db_task.last_status,
            last_error=db_task.last_error,
        )

    # ==================== Stats ====================

    async def get_stats(self, db: AsyncSession, user_id: int) -> TaskStats:
        """Get task statistics."""
        from app.models.database import ScheduledTask as TaskDB

        # Total tasks
        total_result = await db.execute(select(TaskDB).where(TaskDB.user_id == user_id))
        tasks = total_result.scalars().all()

        # Active tasks
        active = len([t for t in tasks if t.enabled])

        # By type
        by_type = {}
        for task in tasks:
            by_type[task.task_type] = by_type.get(task.task_type, 0) + 1

        return TaskStats(
            total_tasks=len(tasks),
            active_tasks=active,
            by_type=by_type,
            today_executions=0,  # Would need TaskExecution table
            recent_failures=0,
        )


# Global scheduler instance
task_scheduler = TaskScheduler()
