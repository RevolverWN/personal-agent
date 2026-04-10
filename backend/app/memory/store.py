"""Memory storage and management."""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.models import Memory, MemoryCreate, MemoryStats, MemoryUpdate
from app.models.database import Memory as MemoryModel


class MemoryStore:
    """Store and manage memories in database."""

    def __init__(self, db: AsyncSession):
        """Initialize store with database session."""
        self.db = db

    async def create(self, user_id: int, memory_data: MemoryCreate) -> Memory:
        """Create a new memory."""
        memory_id = str(uuid.uuid4())
        now = datetime.utcnow()

        db_memory = MemoryModel(
            id=memory_id,
            user_id=user_id,
            content=memory_data.content,
            category=memory_data.category,
            importance=memory_data.importance,
            source_conversation_id=memory_data.source_conversation_id,
            created_at=now,
            updated_at=now,
            access_count=0,
            meta_data=memory_data.meta_data,
        )

        self.db.add(db_memory)
        await self.db.commit()
        await self.db.refresh(db_memory)

        return Memory.model_validate(db_memory)

    async def get(self, memory_id: str, user_id: int) -> Memory | None:
        """Get a memory by ID."""
        result = await self.db.execute(
            select(MemoryModel).where(
                and_(MemoryModel.id == memory_id, MemoryModel.user_id == user_id)
            )
        )
        db_memory = result.scalar_one_or_none()

        if db_memory:
            return Memory.model_validate(db_memory)
        return None

    async def get_all(
        self, user_id: int, category: str | None = None, skip: int = 0, limit: int = 100
    ) -> list[Memory]:
        """Get all memories for a user."""
        query = select(MemoryModel).where(MemoryModel.user_id == user_id)

        if category:
            query = query.where(MemoryModel.category == category)

        query = query.order_by(desc(MemoryModel.importance), desc(MemoryModel.created_at))
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        memories = result.scalars().all()

        return [Memory.model_validate(m) for m in memories]

    async def update(
        self, memory_id: str, user_id: int, update_data: MemoryUpdate
    ) -> Memory | None:
        """Update a memory."""
        result = await self.db.execute(
            select(MemoryModel).where(
                and_(MemoryModel.id == memory_id, MemoryModel.user_id == user_id)
            )
        )
        db_memory = result.scalar_one_or_none()

        if not db_memory:
            return None

        # Update fields
        if update_data.content is not None:
            db_memory.content = update_data.content
        if update_data.category is not None:
            db_memory.category = update_data.category
        if update_data.importance is not None:
            db_memory.importance = update_data.importance
        if update_data.meta_data is not None:
            db_memory.meta_data = update_data.meta_data

        db_memory.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(db_memory)

        return Memory.model_validate(db_memory)

    async def delete(self, memory_id: str, user_id: int) -> bool:
        """Delete a memory."""
        result = await self.db.execute(
            select(MemoryModel).where(
                and_(MemoryModel.id == memory_id, MemoryModel.user_id == user_id)
            )
        )
        db_memory = result.scalar_one_or_none()

        if not db_memory:
            return False

        await self.db.delete(db_memory)
        await self.db.commit()

        return True

    async def increment_access(self, memory_id: str) -> None:
        """Increment access count for a memory."""
        result = await self.db.execute(select(MemoryModel).where(MemoryModel.id == memory_id))
        db_memory = result.scalar_one_or_none()

        if db_memory:
            db_memory.access_count += 1
            db_memory.last_accessed = datetime.utcnow()
            await self.db.commit()

    async def search(self, user_id: int, query: str, limit: int = 10) -> list[Memory]:
        """Search memories by content (simple contains search)."""
        result = await self.db.execute(
            select(MemoryModel)
            .where(and_(MemoryModel.user_id == user_id, MemoryModel.content.ilike(f"%{query}%")))
            .order_by(desc(MemoryModel.importance))
            .limit(limit)
        )

        memories = result.scalars().all()
        return [Memory.model_validate(m) for m in memories]

    async def get_stats(self, user_id: int) -> MemoryStats:
        """Get memory statistics for a user."""
        # Total count
        total_result = await self.db.execute(
            select(func.count(MemoryModel.id)).where(MemoryModel.user_id == user_id)
        )
        total = total_result.scalar() or 0

        # By category
        category_result = await self.db.execute(
            select(MemoryModel.category, func.count(MemoryModel.id))
            .where(MemoryModel.user_id == user_id)
            .group_by(MemoryModel.category)
        )
        by_category = {cat: count for cat, count in category_result.all()}

        # Recent additions (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_result = await self.db.execute(
            select(func.count(MemoryModel.id)).where(
                and_(MemoryModel.user_id == user_id, MemoryModel.created_at >= week_ago)
            )
        )
        recent = recent_result.scalar() or 0

        # Most important memories
        important_result = await self.db.execute(
            select(MemoryModel)
            .where(and_(MemoryModel.user_id == user_id, MemoryModel.importance >= 4))
            .order_by(desc(MemoryModel.importance), desc(MemoryModel.created_at))
            .limit(5)
        )
        important = [Memory.model_validate(m) for m in important_result.scalars().all()]

        return MemoryStats(
            total_memories=total,
            by_category=by_category,
            recent_additions=recent,
            most_important=important,
        )

    async def find_similar(self, user_id: int, content: str, limit: int = 5) -> list[Memory]:
        """Find memories similar to given content (keyword-based)."""
        # Extract keywords (simple approach)
        words = [w.lower() for w in content.split() if len(w) > 3]

        if not words:
            return []

        # Build query with OR conditions
        conditions = [
            MemoryModel.content.ilike(f"%{word}%")
            for word in words[:5]  # Use first 5 significant words
        ]

        result = await self.db.execute(
            select(MemoryModel)
            .where(and_(MemoryModel.user_id == user_id, func.or_(*conditions)))
            .order_by(desc(MemoryModel.importance), desc(MemoryModel.access_count))
            .limit(limit)
        )

        memories = result.scalars().all()
        return [Memory.model_validate(m) for m in memories]

    async def merge_similar(self, user_id: int, new_memory: MemoryCreate) -> Memory | None:
        """Try to merge with existing similar memory, or create new."""
        # Find similar memories
        similar = await self.find_similar(user_id, new_memory.content, limit=3)

        for mem in similar:
            # Simple similarity check - if >70% words match, consider merging
            existing_words = set(mem.content.lower().split())
            new_words = set(new_memory.content.lower().split())

            if existing_words and new_words:
                overlap = len(existing_words.intersection(new_words))
                similarity = overlap / max(len(existing_words), len(new_words))

                if similarity > 0.7:
                    # Update existing memory with new info
                    return await self.update(
                        mem.id,
                        user_id,
                        MemoryUpdate(
                            content=new_memory.content,
                            importance=max(mem.importance, new_memory.importance),
                        ),
                    )

        # No similar memory found, create new
        return await self.create(user_id, new_memory)
