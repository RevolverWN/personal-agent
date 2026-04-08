"""WebSocket connection manager."""

import json
import uuid
from typing import Dict, List, Optional
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        # Map client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Map user_id -> List[client_id]
        self.user_connections: Dict[int, List[str]] = {}
        # Map conversation_id -> List[client_id]
        self.conversation_rooms: Dict[str, List[str]] = {}
    
    async def connect(
        self, 
        websocket: WebSocket, 
        user_id: int,
        conversation_id: Optional[str] = None
    ) -> str:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        # Generate unique client ID
        client_id = str(uuid.uuid4())
        
        # Store connection
        self.active_connections[client_id] = websocket
        
        # Track by user
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(client_id)
        
        # Join conversation room if specified
        if conversation_id:
            if conversation_id not in self.conversation_rooms:
                self.conversation_rooms[conversation_id] = []
            self.conversation_rooms[conversation_id].append(client_id)
        
        return client_id
    
    def disconnect(self, client_id: str, user_id: int) -> None:
        """Remove a WebSocket connection."""
        # Remove from active connections
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove from user connections
        if user_id in self.user_connections:
            if client_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(client_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove from all conversation rooms
        for room in self.conversation_rooms.values():
            if client_id in room:
                room.remove(client_id)
    
    async def send_message(self, client_id: str, message: dict) -> bool:
        """Send message to a specific client."""
        if client_id not in self.active_connections:
            return False
        
        try:
            await self.active_connections[client_id].send_json(message)
            return True
        except Exception:
            return False
    
    async def broadcast_to_user(self, user_id: int, message: dict) -> int:
        """Broadcast message to all connections of a user."""
        if user_id not in self.user_connections:
            return 0
        
        sent_count = 0
        for client_id in self.user_connections[user_id]:
            if await self.send_message(client_id, message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_conversation(
        self, 
        conversation_id: str, 
        message: dict,
        exclude_client: Optional[str] = None
    ) -> int:
        """Broadcast message to all clients in a conversation."""
        if conversation_id not in self.conversation_rooms:
            return 0
        
        sent_count = 0
        for client_id in self.conversation_rooms[conversation_id]:
            if exclude_client and client_id == exclude_client:
                continue
            if await self.send_message(client_id, message):
                sent_count += 1
        
        return sent_count
    
    async def send_stream_chunk(
        self,
        client_id: str,
        chunk: str,
        message_id: str
    ) -> bool:
        """Send a streaming response chunk."""
        return await self.send_message(client_id, {
            "type": "stream_chunk",
            "content": chunk,
            "message_id": message_id
        })
    
    async def send_stream_end(
        self,
        client_id: str,
        message_id: str,
        full_content: str
    ) -> bool:
        """Signal end of streaming response."""
        return await self.send_message(client_id, {
            "type": "stream_end",
            "message_id": message_id,
            "full_content": full_content
        })
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.active_connections)
    
    def get_user_connection_count(self, user_id: int) -> int:
        """Get number of connections for a user."""
        return len(self.user_connections.get(user_id, []))


# Global connection manager instance
manager = ConnectionManager()
