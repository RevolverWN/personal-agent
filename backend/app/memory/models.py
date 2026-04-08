"""Memory data models."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Memory(BaseModel):
    """A single memory entry."""
    id: str
    user_id: int
    content: str
    category: str = "general"  # general, preference, fact, task
    importance: int = Field(default=3, ge=1, le=5)
    source_conversation_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class MemoryCreate(BaseModel):
    """Create a new memory."""
    content: str = Field(..., min_length=1, max_length=2000)
    category: str = "general"
    importance: int = Field(default=3, ge=1, le=5)
    source_conversation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MemoryUpdate(BaseModel):
    """Update an existing memory."""
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    category: Optional[str] = None
    importance: Optional[int] = Field(None, ge=1, le=5)
    metadata: Optional[Dict[str, Any]] = None


class MemorySearchResult(BaseModel):
    """Memory search result with relevance score."""
    memory: Memory
    relevance_score: float


class MemoryStats(BaseModel):
    """Memory statistics for a user."""
    total_memories: int
    by_category: Dict[str, int]
    recent_additions: int  # Last 7 days
    most_important: List[Memory]


class ExtractedMemory(BaseModel):
    """Memory extracted from conversation."""
    content: str
    category: str
    importance: int
    confidence: float  # Extraction confidence (0-1)


class MemoryContext(BaseModel):
    """Memory context to inject into conversation."""
    memories: List[Memory]
    context_string: str
    total_tokens: int
