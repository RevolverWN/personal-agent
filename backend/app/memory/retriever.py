"""Memory retrieval for conversation context."""

from sqlalchemy import select

from app.memory.models import Memory, MemoryContext
from app.memory.store import MemoryStore
from app.models.database import Memory as MemoryDB


class MemoryRetriever:
    """Retrieve relevant memories for conversation context."""

    def __init__(self, memory_store: MemoryStore):
        """Initialize retriever with memory store."""
        self.store = memory_store
        self.max_context_memories = 10
        self.max_context_tokens = 1500  # Approximate token limit

    async def get_context_for_conversation(
        self, user_id: int, current_message: str, recent_memories: bool = True
    ) -> MemoryContext:
        """Get relevant memories to inject into conversation."""
        memories = []

        # 1. Search for memories related to current message
        related = await self.store.find_similar(user_id, current_message, limit=5)
        memories.extend(related)

        # 2. Get high importance memories if we have space
        if len(memories) < self.max_context_memories:
            important_result = await self.store.db.execute(
                select(MemoryDB)
                .where(MemoryDB.user_id == user_id, MemoryDB.importance >= 4)
                .order_by(MemoryDB.access_count.desc())
                .limit(3)
            )
            important = important_result.scalars().all()

            for mem in important:
                if mem.id not in [m.id for m in memories]:
                    memories.append(mem)

        # 3. Get recent memories if enabled
        if recent_memories and len(memories) < self.max_context_memories:
            from datetime import datetime, timedelta

            week_ago = datetime.utcnow() - timedelta(days=7)

            recent_result = await self.store.db.execute(
                select(MemoryDB)
                .where(MemoryDB.user_id == user_id, MemoryDB.created_at >= week_ago)
                .order_by(MemoryDB.created_at.desc())
                .limit(3)
            )
            recent = recent_result.scalars().all()

            for mem in recent:
                if mem.id not in [m.id for m in memories]:
                    memories.append(mem)

        # Limit to max memories
        memories = memories[: self.max_context_memories]

        # Build context string
        context_string = self._build_context_string(memories)

        # Update access counts
        for mem in memories:
            await self.store.increment_access(mem.id)

        return MemoryContext(
            memories=memories,
            context_string=context_string,
            total_tokens=len(context_string.split()),  # Rough estimate
        )

    def _build_context_string(self, memories: list[Memory]) -> str:
        """Build a context string from memories."""
        if not memories:
            return ""

        lines = ["# Relevant information about the user:"]

        for mem in memories:
            prefix = ""
            if mem.category == "preference":
                prefix = "[Preference] "
            elif mem.category == "fact":
                prefix = "[Fact] "
            elif mem.category == "goal":
                prefix = "[Goal] "
            elif mem.category == "task":
                prefix = "[Task] "

            lines.append(f"- {prefix}{mem.content}")

        return "\n".join(lines)

    async def get_system_prompt_with_memory(
        self, user_id: int, current_message: str, base_system_prompt: str | None = None
    ) -> str:
        """Get system prompt enhanced with relevant memories."""
        context = await self.get_context_for_conversation(user_id, current_message)

        if not context.memories:
            return base_system_prompt or "You are a helpful AI assistant."

        # Build enhanced system prompt
        parts = []

        if base_system_prompt:
            parts.append(base_system_prompt)
        else:
            parts.append("You are a helpful AI assistant.")

        parts.append("\n" + context.context_string)
        parts.append(
            "\nUse the above information to personalize your responses, but don't explicitly mention that you remember unless relevant."
        )

        return "\n".join(parts)

    def estimate_memory_relevance(self, memory: Memory, query: str) -> float:
        """Estimate relevance of a memory to a query."""
        memory_words = set(memory.content.lower().split())
        query_words = set(query.lower().split())

        if not memory_words or not query_words:
            return 0.0

        # Calculate word overlap
        overlap = len(memory_words.intersection(query_words))
        total_unique = len(memory_words.union(query_words))

        if total_unique == 0:
            return 0.0

        base_score = overlap / total_unique

        # Boost by importance
        importance_boost = (memory.importance - 1) * 0.1  # 0 to 0.4 boost

        # Boost by access frequency (popularity)
        access_boost = min(memory.access_count * 0.01, 0.1)  # Up to 0.1 boost

        return min(base_score + importance_boost + access_boost, 1.0)
