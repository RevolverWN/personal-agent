"""Heartbeat service — periodic backend health check (MVP)."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class HeartbeatService:
    """Periodically checks backend availability and returns a status dict.

    MVP: simply records liveness. Can be extended to read HEARTBEAT.md,
    check external services, disk space, etc.
    """

    def __init__(self, interval_seconds: int = 1800) -> None:
        self._interval = interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._started_at: Optional[datetime] = None
        self._last_check: Optional[datetime] = None
        self._check_count: int = 0
        self._is_healthy: bool = True

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._started_at = datetime.now(timezone.utc)
        self._task = asyncio.create_task(self._loop())
        logger.info(
            "HeartbeatService started (interval=%ds)", self._interval
        )

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("HeartbeatService stopped")

    async def check(self) -> Dict[str, Any]:
        """Run one health-check cycle and return results."""
        now = datetime.now(timezone.utc)
        self._last_check = now
        self._check_count += 1

        # Basic liveness check — the fact this function returns means the
        # event loop and scheduler are alive.
        self._is_healthy = True

        return {
            "status": "healthy" if self._is_healthy else "unhealthy",
            "timestamp": now.isoformat(),
            "check_count": self._check_count,
            "uptime_seconds": (
                (now - self._started_at).total_seconds()
                if self._started_at
                else 0
            ),
            "interval_seconds": self._interval,
        }

    async def get_status(self) -> Dict[str, Any]:
        """Return current status without running a new check."""
        return {
            "healthy": self._is_healthy,
            "started_at": (
                self._started_at.isoformat() if self._started_at else None
            ),
            "last_check": (
                self._last_check.isoformat() if self._last_check else None
            ),
            "check_count": self._check_count,
            "interval_seconds": self._interval,
        }

    # ── Internal ───────────────────────────────────────────────────────────

    async def _loop(self) -> None:
        while True:
            try:
                result = await self.check()
                logger.debug("Heartbeat check #%s: %s", self._check_count, result.get("status"))
            except Exception:
                logger.exception("Heartbeat check failed")
                self._is_healthy = False
            await asyncio.sleep(self._interval)


# ── Singleton ──────────────────────────────────────────────────────────────

heartbeat_service = HeartbeatService()
