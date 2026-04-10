"""MCP manager for handling multiple MCP servers."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp.client import MCPClient
from app.mcp.models import (
    MCPServer,
    MCPServerCreate,
    MCPServerStats,
    MCPServerStatus,
    MCPServerUpdate,
    MCPTool,
    MCPToolResult,
)


class MCPManager:
    """Manage MCP servers and clients."""

    def __init__(self):
        """Initialize MCP manager."""
        self._clients: dict[str, MCPClient] = {}

    async def create_server(
        self, db: AsyncSession, user_id: int, server_data: MCPServerCreate
    ) -> MCPServer:
        """Create a new MCP server configuration."""
        from app.models.database import MCPServer as MCPServerDB

        server_id = str(uuid.uuid4())
        now = datetime.utcnow()

        db_server = MCPServerDB(
            id=server_id,
            user_id=user_id,
            name=server_data.name,
            description=server_data.description,
            server_type=server_data.server_type,
            config=server_data.config.model_dump(),
            enabled=server_data.enabled,
            icon=server_data.icon,
            status=MCPServerStatus.DISCONNECTED.value,
            tools=[],
            created_at=now,
            updated_at=now,
            usage_count=0,
        )

        db.add(db_server)
        await db.commit()
        await db.refresh(db_server)

        # Convert to model
        server = self._to_model(db_server)

        # Auto-connect if enabled
        if server.enabled:
            await self.connect_server(server)

        return server

    async def get_server(self, db: AsyncSession, server_id: str, user_id: int) -> MCPServer | None:
        """Get an MCP server."""
        from app.models.database import MCPServer as MCPServerDB

        result = await db.execute(
            select(MCPServerDB).where(
                and_(MCPServerDB.id == server_id, MCPServerDB.user_id == user_id)
            )
        )
        db_server = result.scalar_one_or_none()

        if db_server:
            return self._to_model(db_server)
        return None

    async def get_user_servers(self, db: AsyncSession, user_id: int) -> list[MCPServer]:
        """Get all MCP servers for a user."""
        from app.models.database import MCPServer as MCPServerDB

        result = await db.execute(
            select(MCPServerDB)
            .where(MCPServerDB.user_id == user_id)
            .order_by(desc(MCPServerDB.created_at))
        )

        return [self._to_model(s) for s in result.scalars().all()]

    async def update_server(
        self, db: AsyncSession, server_id: str, user_id: int, update_data: MCPServerUpdate
    ) -> MCPServer | None:
        """Update an MCP server."""
        from app.models.database import MCPServer as MCPServerDB

        result = await db.execute(
            select(MCPServerDB).where(
                and_(MCPServerDB.id == server_id, MCPServerDB.user_id == user_id)
            )
        )
        db_server = result.scalar_one_or_none()

        if not db_server:
            return None

        # Disconnect if currently connected
        if server_id in self._clients:
            await self.disconnect_server(server_id)

        # Update fields
        if update_data.name is not None:
            db_server.name = update_data.name
        if update_data.description is not None:
            db_server.description = update_data.description
        if update_data.config is not None:
            db_server.config = update_data.config.model_dump()
        if update_data.enabled is not None:
            db_server.enabled = update_data.enabled
        if update_data.icon is not None:
            db_server.icon = update_data.icon

        db_server.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(db_server)

        server = self._to_model(db_server)

        # Reconnect if enabled
        if server.enabled:
            await self.connect_server(server)

        return server

    async def delete_server(self, db: AsyncSession, server_id: str, user_id: int) -> bool:
        """Delete an MCP server."""
        from app.models.database import MCPServer as MCPServerDB

        # Disconnect first
        await self.disconnect_server(server_id)

        result = await db.execute(
            select(MCPServerDB).where(
                and_(MCPServerDB.id == server_id, MCPServerDB.user_id == user_id)
            )
        )
        db_server = result.scalar_one_or_none()

        if not db_server:
            return False

        await db.delete(db_server)
        await db.commit()

        return True

    # ==================== Connection Management ====================

    async def connect_server(self, server: MCPServer) -> bool:
        """Connect to an MCP server."""
        # Disconnect if already connected
        if server.id in self._clients:
            await self.disconnect_server(server.id)

        # Create client and connect
        client = MCPClient(server)

        try:
            success = await client.connect()
            if success:
                self._clients[server.id] = client
                return True
        except Exception as e:
            server.status = MCPServerStatus.ERROR
            server.last_error = str(e)

        return False

    async def disconnect_server(self, server_id: str):
        """Disconnect from an MCP server."""
        if server_id in self._clients:
            client = self._clients.pop(server_id)
            await client.disconnect()

    async def reconnect_server(self, server: MCPServer) -> bool:
        """Reconnect to an MCP server."""
        await self.disconnect_server(server.id)
        return await self.connect_server(server)

    # ==================== Tool Execution ====================

    async def call_tool(
        self, server_id: str, tool_name: str, parameters: dict[str, Any]
    ) -> MCPToolResult:
        """Call a tool on a specific server."""
        if server_id not in self._clients:
            return MCPToolResult(success=False, data=None, error="Server not connected")

        client = self._clients[server_id]
        result = await client.call_tool(tool_name, parameters)

        # Update usage count
        if result.success:
            # This would need to be persisted to DB
            pass

        return result

    async def find_and_call_tool(
        self, full_tool_name: str, parameters: dict[str, Any]
    ) -> MCPToolResult:
        """Find server by tool name and call tool."""
        # Parse tool name: "mcp_{server_id}_{tool_name}" or "{tool_name}"
        server_id = None
        tool_name = full_tool_name

        if full_tool_name.startswith("mcp_"):
            parts = full_tool_name.split("_", 2)
            if len(parts) >= 3:
                server_id = parts[1]
                tool_name = parts[2]

        if server_id and server_id in self._clients:
            return await self.call_tool(server_id, tool_name, parameters)

        # Try all connected servers
        for sid, client in self._clients.items():
            tools = client.get_tools()
            if any(t.name == tool_name for t in tools):
                return await self.call_tool(sid, tool_name, parameters)

        return MCPToolResult(
            success=False, data=None, error=f"Tool '{tool_name}' not found on any connected server"
        )

    # ==================== Tool Discovery ====================

    def get_all_tools(self) -> list[MCPTool]:
        """Get all tools from all connected servers."""
        tools = []
        for client in self._clients.values():
            tools.extend(client.get_tools())
        return tools

    def get_tools_for_server(self, server_id: str) -> list[MCPTool]:
        """Get tools for a specific server."""
        if server_id in self._clients:
            return self._clients[server_id].get_tools()
        return []

    def get_all_schemas(self) -> list[dict[str, Any]]:
        """Get OpenAI function schemas for all tools."""
        schemas = []
        for tool in self.get_all_tools():
            schemas.append(tool.to_openai_schema())
        return schemas

    # ==================== Stats ====================

    async def get_stats(self, db: AsyncSession, user_id: int) -> MCPServerStats:
        """Get MCP statistics."""
        servers = await self.get_user_servers(db, user_id)

        total = len(servers)
        connected = len([s for s in servers if s.status == MCPServerStatus.CONNECTED])
        total_tools = sum(len(s.tools) for s in servers)

        return MCPServerStats(
            total_servers=total,
            connected_servers=connected,
            total_tools=total_tools,
            today_calls=0,  # Would need call tracking
            failed_calls=0,
        )

    # ==================== Helper Methods ====================

    def _to_model(self, db_server) -> MCPServer:
        """Convert DB model to Pydantic model."""
        from app.mcp.models import MCPServerConfig

        return MCPServer(
            id=db_server.id,
            user_id=db_server.user_id,
            name=db_server.name,
            description=db_server.description,
            server_type=db_server.server_type,
            config=MCPServerConfig(**db_server.config),
            enabled=db_server.enabled,
            status=MCPServerStatus(db_server.status),
            icon=db_server.icon,
            tools=[MCPTool(**t) for t in db_server.tools] if db_server.tools else [],
            created_at=db_server.created_at,
            updated_at=db_server.updated_at,
            last_connected_at=db_server.last_connected_at,
            last_error=db_server.last_error,
            usage_count=db_server.usage_count,
        )

    async def cleanup(self):
        """Disconnect all servers."""
        for server_id in list(self._clients.keys()):
            await self.disconnect_server(server_id)


# Global MCP manager instance
mcp_manager = MCPManager()
