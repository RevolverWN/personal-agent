"""Short-term memory: conversation cache with fixed-size window."""

from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Dict, List


class ShortTermMemory:
    """Current-session conversation cache with a sliding window.

    Each entry is a dict ``{"role": ..., "content": ...}``.  When the buffer
    exceeds *window_size*, the oldest entries are silently dropped.
    """

    def __init__(self, window_size: int = 20) -> None:
        self._buffer: deque[Dict[str, str]] = deque(maxlen=window_size)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, role: str, content: str) -> None:
        """Append a conversation turn (user / assistant / system)."""
        self._buffer.append(
            {"role": role, "content": content, "timestamp": datetime.utcnow().isoformat()}
        )

    def get_recent(self, n: int = 10) -> List[Dict[str, str]]:
        """Return the most recent *n* entries (newest last)."""
        items = list(self._buffer)
        return items[-n:] if n < len(items) else items

    def get_context(self) -> str:
        """Return a formatted string of all buffered turns."""
        if not self._buffer:
            return ""
        lines: List[str] = []
        for entry in self._buffer:
            lines.append(f"[{entry['role'].upper()}] {entry['content']}")
        return "\n".join(lines)

    def clear(self) -> None:
        """Empty the buffer."""
        self._buffer.clear()

    @property
    def size(self) -> int:
        """Number of entries currently in the buffer."""
        return len(self._buffer)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self.size

    def __repr__(self) -> str:
        return f"ShortTermMemory(size={self.size})"
