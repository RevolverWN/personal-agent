"""Tests for WebSocket functionality using proper FastAPI test client."""

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_token():
    """Create auth token for testing."""
    return create_access_token(data={"sub": "1"})


class TestWebSocketConnection:
    """Test WebSocket connection establishment."""

    def test_websocket_auth_required(self, client):
        """Test that WebSocket requires authentication."""
        # Should reject connection without token
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/chat") as ws:
                pass

    def test_websocket_connect_with_token(self, client, auth_token):
        """Test WebSocket connection with valid token."""
        # This will fail until we implement WebSocket endpoint
        try:
            with client.websocket_connect(f"/ws/chat?token={auth_token}") as ws:
                # Should receive connection confirmation
                data = ws.receive_json()
                assert data["type"] == "connected"
                assert "client_id" in data
        except Exception as e:
            pytest.fail(f"WebSocket connection failed: {e}")


class TestWebSocketMessaging:
    """Test WebSocket message handling."""

    def test_send_message(self, client, auth_token):
        """Test sending message via WebSocket."""
        try:
            with client.websocket_connect(f"/ws/chat?token={auth_token}") as ws:
                # Skip connection message
                ws.receive_json()

                # Send a message
                ws.send_json({"type": "chat", "message": "Hello, AI!", "conversation_id": None})

                # Should receive acknowledgment
                response = ws.receive_json()
                assert response["type"] == "ack"
                assert "message_id" in response
        except Exception as e:
            pytest.fail(f"Message sending failed: {e}")

    def test_receive_streaming_response(self, client, auth_token):
        """Test receiving streaming response via WebSocket."""
        try:
            with client.websocket_connect(f"/ws/chat?token={auth_token}") as ws:
                # Skip connection message
                ws.receive_json()

                # Send message
                ws.send_json(
                    {"type": "chat", "message": "Hi", "conversation_id": None, "stream": True}
                )

                # Should receive streaming response
                chunks = []
                for _ in range(10):  # Max 10 chunks
                    data = ws.receive_json()
                    if data["type"] == "stream_chunk":
                        chunks.append(data["content"])
                    elif data["type"] == "stream_end":
                        break

                assert len(chunks) > 0

        except Exception as e:
            pytest.fail(f"Streaming failed: {e}")


class TestWebSocketRoomManagement:
    """Test WebSocket room/conversation management."""

    def test_join_conversation(self, client, auth_token):
        """Test joining a specific conversation room."""
        conversation_id = "test-conv-123"

        try:
            with client.websocket_connect(
                f"/ws/chat?token={auth_token}&conversation_id={conversation_id}"
            ) as ws:
                # Should receive connection confirmation with room info
                data = ws.receive_json()
                assert data["type"] == "connected"
                assert data.get("conversation_id") == conversation_id
        except Exception as e:
            pytest.fail(f"Join room failed: {e}")

    def test_typing_indicator(self, client, auth_token):
        """Test typing indicator functionality."""
        try:
            with client.websocket_connect(f"/ws/chat?token={auth_token}") as ws:
                # Skip connection message
                ws.receive_json()

                # Send typing indicator
                ws.send_json({"type": "typing", "is_typing": True})

                # Server should acknowledge
                data = ws.receive_json()
                assert data["type"] == "typing_ack"
        except Exception as e:
            pytest.fail(f"Typing indicator failed: {e}")


class TestWebSocketErrorHandling:
    """Test WebSocket error handling."""

    def test_invalid_message_format(self, client, auth_token):
        """Test handling of invalid message format."""
        try:
            with client.websocket_connect(f"/ws/chat?token={auth_token}") as ws:
                # Skip connection message
                ws.receive_json()

                # Send invalid JSON
                ws.send_text("not valid json")

                # Should receive error
                data = ws.receive_json()
                assert data["type"] == "error"
                assert "message" in data
        except Exception as e:
            pytest.fail(f"Error handling failed: {e}")

    def test_unknown_message_type(self, client, auth_token):
        """Test handling of unknown message type."""
        try:
            with client.websocket_connect(f"/ws/chat?token={auth_token}") as ws:
                # Skip connection message
                ws.receive_json()

                # Send unknown type
                ws.send_json({"type": "unknown_type", "data": "test"})

                # Should receive error
                data = ws.receive_json()
                assert data["type"] == "error"
                assert "Unknown message type" in data["message"]
        except Exception as e:
            pytest.fail(f"Unknown type handling failed: {e}")
