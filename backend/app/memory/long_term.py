"""Long-term memory layer built on top of the existing MemoryStore."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import litellm
from litellm import acompletion

from app.memory.models import Memory, MemoryCreate, MemoryStats
from app.memory.short_term import ShortTermMemory
from app.memory.store import MemoryStore

logger = logging.getLogger(__name__)

# Threshold: trigger auto-summarise when short-term buffer exceeds this count
AUTO_SUMMARIZE_THRESHOLD = 15

# System prompt used by the LLM to produce a summary
_SUMMARY_SYSTEM_PROMPT = (
    "You are a concise summariser. Given the conversation history below, "
    "produce a single short paragraph that captures the key information "
    "worth remembering (facts, preferences, decisions, tasks).  "
    "Output ONLY the summary paragraph — no preamble, no bullet points."
)


class LongTermMemory:
    """Persistent long-term memory, backed by an existing ``MemoryStore``."""

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------

    async def store(
        self,
        user_id: int,
        content: str,
        category: str = "general",
        importance: int = 3,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """Create (or merge) a long-term memory entry."""
        data = MemoryCreate(
            content=content,
            category=category,
            importance=importance,
            metadata=meta,
        )
        return await self._store.merge_similar(user_id, data)

    async def search(self, user_id: int, query: str, limit: int = 5) -> List[Memory]:
        """Keyword-search long-term memories (delegates to MemoryStore)."""
        return await self._store.search(user_id, query, limit)

    async def get_stats(self, user_id: int) -> MemoryStats:
        """Return aggregate memory statistics for a user."""
        return await self._store.get_stats(user_id)

    # ------------------------------------------------------------------
    # Auto-summarisation
    # ------------------------------------------------------------------

    async def auto_summarize(
        self,
        user_id: int,
        short_term: ShortTermMemory,
    ) -> Optional[str]:
        """If *short_term* exceeds the threshold, summarise and persist.

        Returns the generated summary string, or ``None`` if summarisation
        was not triggered (buffer too small).
        """
        if short_term.size < AUTO_SUMMARIZE_THRESHOLD:
            return None

        context = short_term.get_context()
        if not context.strip():
            return None

        summary = await self._generate_summary(context)
        if not summary:
            return None

        await self.store(
            user_id=user_id,
            content=summary,
            category="conversation_summary",
            importance=3,
            meta={"source": "auto_summarize", "timestamp": datetime.utcnow().isoformat()},
        )

        logger.info("Auto-summarized %d turns for user %s", short_term.size, user_id)
        return summary

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _generate_summary(self, conversation_context: str) -> Optional[str]:
        """Call an LLM via LiteLLM to produce a one-paragraph summary."""
        try:
            resp = await acompletion(
                model="gpt-4o-mini",  # MVP: fixed lightweight model
                messages=[
                    {"role": "system", "content": _SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": conversation_context},
                ],
                temperature=0.3,
                max_tokens=256,
            )
            return (resp.choices[0].message.content or "").strip() or None
        except Exception:
            logger.exception("Failed to generate conversation summary")
            return None
