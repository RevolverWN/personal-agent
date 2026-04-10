"""Scheduler & heartbeat API endpoints."""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.scheduler.engine import scheduler_engine
from app.scheduler.heartbeat import heartbeat_service
from app.scheduler.types import TaskCreate, TaskResponse, TaskRun

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Tasks ──────────────────────────────────────────────────────────────────


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(data: TaskCreate):
    """Create a new scheduled task."""
    return await scheduler_engine.add_task(data)


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks():
    """List all scheduled tasks."""
    return await scheduler_engine.list_tasks()


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: str):
    """Remove a task by ID."""
    removed = await scheduler_engine.remove_task(task_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/tasks/{task_id}/run", response_model=TaskRun)
async def run_task(task_id: str):
    """Manually trigger a task execution."""
    try:
        return await scheduler_engine.run_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")


@router.get("/tasks/{task_id}/runs", response_model=List[TaskRun])
async def get_task_runs(task_id: str):
    """Get execution history for a task."""
    task = await scheduler_engine.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return await scheduler_engine.get_task_runs(task_id)


# ── Heartbeat ──────────────────────────────────────────────────────────────


@router.get("/heartbeat/status")
async def heartbeat_status():
    """Get current heartbeat status."""
    return await heartbeat_service.get_status()


@router.post("/heartbeat/check")
async def heartbeat_check():
    """Trigger an immediate health check."""
    return await heartbeat_service.check()
