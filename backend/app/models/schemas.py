"""Pydantic schemas for API requests/responses."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# ============================================
# Base Schemas
# ============================================


class BaseResponse(BaseModel):
    """Base response schema."""

    success: bool = True
    message: str | None = None


# ============================================
# Auth Schemas
# ============================================


class UserCreate(BaseModel):
    """User registration schema."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """User login schema."""

    username: str
    password: str


class UserResponse(BaseModel):
    """User response schema."""

    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# ============================================
# Chat Schemas
# ============================================


class ChatMessage(BaseModel):
    """Chat message schema."""

    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: datetime | None = None
    metadata: dict[str, Any] | None = None


class ChatRequest(BaseModel):
    """Chat request schema."""

    message: str = Field(..., min_length=1)
    conversation_id: str | None = None
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)
    stream: bool = False


class ChatResponse(BaseModel):
    """Chat response schema."""

    message: ChatMessage
    conversation_id: str
    model: str
    usage: dict[str, int] | None = None


class ConversationResponse(BaseModel):
    """Conversation response schema."""

    id: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int


# ============================================
# Model Schemas
# ============================================


class ModelInfo(BaseModel):
    """Model information schema."""

    id: str
    name: str
    provider: str
    description: str | None = None
    max_tokens: int | None = None
    supports_vision: bool = False
    supports_streaming: bool = True


class ModelListResponse(BaseModel):
    """Model list response schema."""

    models: list[ModelInfo]
    default_model: str


# ============================================
# Agent Config Schemas
# ============================================


class AgentConfig(BaseModel):
    """Agent configuration schema."""

    model: str
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    system_prompt: str | None = None
    enable_tools: list[str] = Field(default_factory=list)
    enable_memory: bool = True


class AgentConfigResponse(BaseModel):
    """Agent config response schema."""

    config: AgentConfig
    updated_at: datetime


# ============================================
# File Schemas
# ============================================


class FileInfo(BaseModel):
    """File information schema."""

    id: str
    filename: str
    size: int
    content_type: str
    created_at: datetime


class FileListResponse(BaseModel):
    """File list response schema."""

    files: list[FileInfo]
    total: int
