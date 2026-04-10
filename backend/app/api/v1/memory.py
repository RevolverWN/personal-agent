"""Memory management API routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, User
from app.models.schemas import BaseResponse
from app.api.v1.auth import get_current_user
from app.memory.store import MemoryStore
from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory
from app.memory.retriever import MemoryRetriever
from app.memory.models import Memory, MemoryCreate, MemoryUpdate, MemoryStats

# Shared short-term memory instance per user (MVP: in-memory)
_short_term_memories: dict[int, ShortTermMemory] = {}
_long_term_memories: dict[int, LongTermMemory] = {}

router = APIRouter()


@router.get("", response_model=list[Memory])
async def list_memories(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's memories."""
    store = MemoryStore(db)
    memories = await store.get_all(
        user_id=current_user.id,
        category=category,
        skip=skip,
        limit=limit
    )
    return memories


@router.post("", response_model=Memory)
async def create_memory(
    memory_data: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new memory manually."""
    store = MemoryStore(db)
    memory = await store.create(current_user.id, memory_data)
    return memory


@router.get("/search")
async def search_memories(
    query: str = Query(..., min_length=1),
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search memories by content."""
    store = MemoryStore(db)
    memories = await store.search(current_user.id, query, limit)
    return {"memories": memories, "count": len(memories)}


@router.get("/stats", response_model=MemoryStats)
async def get_memory_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get memory statistics."""
    store = MemoryStore(db)
    stats = await store.get_stats(current_user.id)
    return stats


@router.get("/{memory_id}", response_model=Memory)
async def get_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific memory."""
    store = MemoryStore(db)
    memory = await store.get(memory_id, current_user.id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return memory


@router.put("/{memory_id}", response_model=Memory)
async def update_memory(
    memory_id: str,
    update_data: MemoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a memory."""
    store = MemoryStore(db)
    memory = await store.update(memory_id, current_user.id, update_data)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return memory


@router.delete("/{memory_id}", response_model=BaseResponse)
async def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a memory."""
    store = MemoryStore(db)
    deleted = await store.delete(memory_id, current_user.id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return BaseResponse(message="Memory deleted successfully")


@router.delete("", response_model=BaseResponse)
async def clear_all_memories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clear all memories for the user."""
    store = MemoryStore(db)
    memories = await store.get_all(current_user.id)
    
    for memory in memories:
        await store.delete(memory.id, current_user.id)
    
    return BaseResponse(message=f"Deleted {len(memories)} memories")


# ── Short-term / Long-term memory API ─────────────────────────────────────


@router.post("/summarize")
async def summarize_short_term(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger summarisation of short-term memory into long-term."""
    store = MemoryStore(db)
    ltm = LongTermMemory(store)
    stm = _short_term_memories.setdefault(current_user.id, ShortTermMemory())
    summary = await ltm.auto_summarize(current_user.id, stm)
    if summary:
        stm.clear()
    return {"summary": summary, "triggered": summary is not None}


@router.get("/context")
async def get_memory_context(
    query: str = Query("", description="Search query for long-term memory"),
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current context: short-term buffer + relevant long-term memories."""
    store = MemoryStore(db)
    ltm = LongTermMemory(store)
    stm = _short_term_memories.setdefault(current_user.id, ShortTermMemory())
    retriever = MemoryRetriever(store)
    context = await retriever.get_context_for_conversation(current_user.id, query, limit)
    short_term_context = stm.get_context()
    return {
        "short_term": {
            "size": stm.size,
            "context": short_term_context,
        },
        "long_term": {
            "count": len(context.memories),
            "memories": context.memories,
        },
    }
