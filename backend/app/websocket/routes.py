"""WebSocket routes for real-time chat."""

import json
import uuid
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse

from app.websocket.manager import manager
from app.core.security import decode_token
from app.agents.orchestrator import orchestrator

router = APIRouter()


@router.websocket("/ws/chat")
async def chat_websocket(
    websocket: WebSocket,
    token: str = Query(...),
    conversation_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time chat.
    
    Query Parameters:
        token: JWT access token for authentication
        conversation_id: Optional conversation ID to join
    """
    # Verify token and get user_id
    user_id = verify_token_for_websocket(token)
    if user_id is None:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return
    
    # Accept connection
    client_id = await manager.connect(
        websocket=websocket,
        user_id=user_id,
        conversation_id=conversation_id
    )
    
    try:
        # Send connection confirmation
        await manager.send_message(client_id, {
            "type": "connected",
            "client_id": client_id,
            "conversation_id": conversation_id,
            "user_id": user_id
        })
        
        # Handle incoming messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                
                # Parse JSON
                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError:
                    await manager.send_message(client_id, {
                        "type": "error",
                        "message": "Invalid JSON format"
                    })
                    continue
                
                # Process message based on type
                await handle_message(
                    client_id=client_id,
                    user_id=user_id,
                    message_data=message_data,
                    conversation_id=conversation_id
                )
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                await manager.send_message(client_id, {
                    "type": "error",
                    "message": f"Internal error: {str(e)}"
                })
    
    finally:
        # Clean up on disconnect
        manager.disconnect(client_id, user_id)


def verify_token_for_websocket(token: str) -> Optional[int]:
    """Verify JWT token and return user_id."""
    try:
        payload = decode_token(token)
        if payload is None:
            return None
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except Exception:
        return None


async def handle_message(
    client_id: str,
    user_id: int,
    message_data: dict,
    conversation_id: Optional[str]
):
    """Handle incoming WebSocket message."""
    message_type = message_data.get("type")
    
    if message_type == "chat":
        await handle_chat_message(
            client_id=client_id,
            user_id=user_id,
            message_data=message_data,
            conversation_id=conversation_id
        )
    elif message_type == "typing":
        await handle_typing_indicator(
            client_id=client_id,
            user_id=user_id,
            message_data=message_data,
            conversation_id=conversation_id
        )
    else:
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        })


async def handle_chat_message(
    client_id: str,
    user_id: int,
    message_data: dict,
    conversation_id: Optional[str]
):
    """Handle chat message."""
    message_content = message_data.get("message", "")
    should_stream = message_data.get("stream", True)
    
    if not message_content:
        await manager.send_message(client_id, {
            "type": "error",
            "message": "Message content is required"
        })
        return
    
    # Generate message ID
    message_id = str(uuid.uuid4())
    
    # Send acknowledgment
    await manager.send_message(client_id, {
        "type": "ack",
        "message_id": message_id,
        "status": "processing"
    })
    
    # Process through orchestrator with streaming
    if should_stream:
        await process_streaming_response(
            client_id=client_id,
            user_id=user_id,
            message=message_content,
            message_id=message_id,
            conversation_id=conversation_id
        )
    else:
        await process_sync_response(
            client_id=client_id,
            user_id=user_id,
            message=message_content,
            message_id=message_id,
            conversation_id=conversation_id
        )


async def process_streaming_response(
    client_id: str,
    user_id: int,
    message: str,
    message_id: str,
    conversation_id: Optional[str]
):
    """Process streaming response from orchestrator."""
    full_response = ""
    
    try:
        async for chunk in orchestrator.stream_process(
            user_id=user_id,
            message=message,
            conversation_id=conversation_id
        ):
            full_response += chunk
            
            # Send chunk to client
            await manager.send_stream_chunk(
                client_id=client_id,
                chunk=chunk,
                message_id=message_id
            )
        
        # Send end of stream
        await manager.send_stream_end(
            client_id=client_id,
            message_id=message_id,
            full_content=full_response
        )
        
    except Exception as e:
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"Streaming error: {str(e)}"
        })


async def process_sync_response(
    client_id: str,
    user_id: int,
    message: str,
    message_id: str,
    conversation_id: Optional[str]
):
    """Process synchronous response from orchestrator."""
    try:
        response = await orchestrator.process(
            user_id=user_id,
            message=message,
            conversation_id=conversation_id
        )
        
        await manager.send_message(client_id, {
            "type": "response",
            "message_id": message_id,
            "content": response.get("content", ""),
            "model": response.get("model"),
            "tokens_used": response.get("tokens_used")
        })
        
    except Exception as e:
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"Processing error: {str(e)}"
        })


async def handle_typing_indicator(
    client_id: str,
    user_id: int,
    message_data: dict,
    conversation_id: Optional[str]
):
    """Handle typing indicator."""
    is_typing = message_data.get("is_typing", False)
    
    # Send acknowledgment
    await manager.send_message(client_id, {
        "type": "typing_ack",
        "is_typing": is_typing,
        "timestamp": message_data.get("timestamp")
    })
    
    # Broadcast to conversation if in a room
    if conversation_id:
        await manager.broadcast_to_conversation(
            conversation_id=conversation_id,
            message={
                "type": "user_typing",
                "user_id": user_id,
                "is_typing": is_typing
            },
            exclude_client=client_id
        )
