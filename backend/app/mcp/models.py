"""MCP data models."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, HttpUrl


class MCPServerStatus(str, Enum):
    """MCP server connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class MCPServerType(str, Enum):
    """MCP server type."""
    STDIO = "stdio"  # Local process
    SSE = "sse"      # Server-Sent Events over HTTP
    WEBSOCKET = "websocket"


class MCPTool(BaseModel):
    """MCP tool definition."""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    server_id: Optional[str] = None
    
    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI function schema."""
        return {
            "type": "function",
            "function": {
                "name": f"mcp_{self.server_id}_{self.name}" if self.server_id else f"mcp_{self.name}",
                "description": self.description,
                "parameters": self.parameters
            }
        }


class MCPServerConfig(BaseModel):
    """MCP server configuration."""
    command: Optional[str] = None  # For STDIO type
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    url: Optional[str] = None  # For SSE/WebSocket type
    timeout: int = 30
    reconnect_interval: int = 5
    max_retries: int = 3


class MCPServerCreate(BaseModel):
    """Create MCP server."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    server_type: MCPServerType = MCPServerType.STDIO
    config: MCPServerConfig
    enabled: bool = True
    icon: str = "🔌"


class MCPServerUpdate(BaseModel):
    """Update MCP server."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    config: Optional[MCPServerConfig] = None
    enabled: Optional[bool] = None
    icon: Optional[str] = None


class MCPServer(BaseModel):
    """MCP server model."""
    id: str
    user_id: int
    name: str
    description: str
    server_type: MCPServerType
    config: MCPServerConfig
    enabled: bool
    status: MCPServerStatus = MCPServerStatus.DISCONNECTED
    icon: str = "🔌"
    tools: List[MCPTool] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    last_connected_at: Optional[datetime] = None
    last_error: Optional[str] = None
    usage_count: int = 0
    
    class Config:
        from_attributes = True


class MCPToolCall(BaseModel):
    """MCP tool call request."""
    server_id: str
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class MCPToolResult(BaseModel):
    """MCP tool call result."""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None


class MCPServerStats(BaseModel):
    """MCP server statistics."""
    total_servers: int
    connected_servers: int
    total_tools: int
    today_calls: int
    failed_calls: int
