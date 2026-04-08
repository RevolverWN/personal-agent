"""Chat API routes."""

import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
import json

from app.models.database import get_db, User, Conversation, Message
from app.models.schemas import (
    ChatRequest, ChatResponse, ChatMessage,
    ConversationResponse, BaseResponse
)
from app.api.v1.auth import get_current_user
from app.agent.core import AgentCore
from app.config import settings

router = APIRouter()
agent_core = AgentCore()


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's conversations."""
    result = await db.execute(
        select(
            Conversation,
            func.count(Message.id).label("message_count")
        )
        .outerjoin(Message, Conversation.id == Message.conversation_id)
        .where(Conversation.user_id == current_user.id)
        .group_by(Conversation.id)
        .order_by(desc(Conversation.updated_at))
        .offset(skip)
        .limit(limit)
    )
    
    conversations = []
    for conv, msg_count in result.all():
        conversations.append(ConversationResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=msg_count
        ))
    
    return conversations


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    
    conversation = Conversation(
        id=conversation_id,
        user_id=current_user.id,
        title=None,
    )
    
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=0
    )


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get messages from a conversation."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    
    return [
        {
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.created_at.isoformat() if msg.created_at else None,
            "metadata": msg.metadata
        }
        for msg in messages
    ]


@router.delete("/conversations/{conversation_id}", response_model=BaseResponse)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    await db.delete(conversation)
    await db.commit()
    
    return BaseResponse(message="Conversation deleted")


async def stream_chat_response(
    message: str,
    conversation_id: str,
    model: str,
    temperature: float,
    history: list,
    db: AsyncSession
) -> AsyncGenerator[str, None]:
    """Stream chat response."""
    full_content = ""
    
    async for chunk in agent_core.chat_stream(
        message=message,
        model=model,
        temperature=temperature,
        history=history
    ):
        full_content += chunk
        data = {
            "type": "content",
            "content": chunk,
            "conversation_id": conversation_id
        }
        yield f"data: {json.dumps(data)}\n\n"
    
    # Save assistant message
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=full_content,
        model=model,
        metadata={"streaming": True}
    )
    db.add(assistant_message)
    await db.commit()
    
    # Send done event
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.post("/completions")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a chat message and get response."""
    # Create or use existing conversation
    if request.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        conversation_id = conversation.id
    else:
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            user_id=current_user.id,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message
        )
        db.add(conversation)
    
    # Save user message
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    await db.commit()
    
    # Get conversation history
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in result.scalars().all()
    ]
    
    model = request.model or settings.DEFAULT_MODEL
    temperature = request.temperature or settings.DEFAULT_TEMPERATURE
    
    if request.stream:
        return StreamingResponse(
            stream_chat_response(
                message=request.message,
                conversation_id=conversation_id,
                model=model,
                temperature=temperature,
                history=history,
                db=db
            ),
            media_type="text/event-stream"
        )
    
    # Non-streaming response with tool and memory support
    response_data = await agent_core.chat(
        message=request.message,
        model=model,
        temperature=temperature,
        history=history,
        enable_tools=True,
        user_id=current_user.id,
        db_session=db
    )
    
    # Save assistant message with tool call metadata
    metadata = None
    if response_data.get("tool_calls"):
        metadata = {"tool_calls": response_data["tool_calls"]}
    
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=response_data["content"],
        model=model,
        metadata=metadata
    )
    db.add(assistant_message)
    await db.commit()
    
    return {
        "message": ChatMessage(
            role="assistant",
            content=response_data["content"],
            timestamp=datetime.now(timezone.utc)
        ),
        "conversation_id": conversation_id,
        "model": model,
        "tool_calls": response_data.get("tool_calls", []),
        "extracted_memories": response_data.get("extracted_memories", []),
        "usage": response_data.get("usage")
    }


@router.get("/tools")
async def list_available_tools(
    current_user: User = Depends(get_current_user)
):
    """List all available tools."""
    tools = agent_core.get_available_tools()
    return {
        "tools": tools,
        "count": len(tools)
    }


@router.post("/tools/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    arguments: dict,
    current_user: User = Depends(get_current_user)
):
    """Execute a tool directly."""
    result = await agent_core.execute_tool_directly(tool_name, arguments)
    return result
