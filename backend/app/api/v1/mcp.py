"""MCP API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.mcp.manager import mcp_manager
from app.mcp.models import MCPServer, MCPServerCreate, MCPServerStats, MCPServerUpdate
from app.models.database import User, get_db
from app.models.schemas import BaseResponse

router = APIRouter()


@router.get("/servers", response_model=list[MCPServer])
async def list_servers(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """List all MCP servers for the user."""
    servers = await mcp_manager.get_user_servers(db, current_user.id)
    return servers


@router.post("/servers", response_model=MCPServer)
async def create_server(
    server_data: MCPServerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new MCP server."""
    server = await mcp_manager.create_server(db, current_user.id, server_data)
    return server


@router.get("/servers/{server_id}", response_model=MCPServer)
async def get_server(
    server_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get an MCP server."""
    server = await mcp_manager.get_server(db, server_id, current_user.id)

    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    return server


@router.put("/servers/{server_id}", response_model=MCPServer)
async def update_server(
    server_id: str,
    update_data: MCPServerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an MCP server."""
    server = await mcp_manager.update_server(db, server_id, current_user.id, update_data)

    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    return server


@router.delete("/servers/{server_id}", response_model=BaseResponse)
async def delete_server(
    server_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an MCP server."""
    deleted = await mcp_manager.delete_server(db, server_id, current_user.id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Server not found")

    return BaseResponse(message="Server deleted successfully")


@router.post("/servers/{server_id}/connect")
async def connect_server(
    server_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Connect to an MCP server."""
    server = await mcp_manager.get_server(db, server_id, current_user.id)

    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    success = await mcp_manager.connect_server(server)

    if success:
        # Refresh to get updated status
        server = await mcp_manager.get_server(db, server_id, current_user.id)
        return {"success": True, "message": "Connected successfully", "server": server}
    else:
        return {"success": False, "message": "Failed to connect", "error": server.last_error}


@router.post("/servers/{server_id}/disconnect")
async def disconnect_server(
    server_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect from an MCP server."""
    server = await mcp_manager.get_server(db, server_id, current_user.id)

    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    await mcp_manager.disconnect_server(server_id)

    return {"success": True, "message": "Disconnected successfully"}


@router.post("/servers/{server_id}/tools/{tool_name}/call")
async def call_tool(
    server_id: str,
    tool_name: str,
    parameters: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Call a tool on an MCP server."""
    # Verify server belongs to user
    server = await mcp_manager.get_server(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    result = await mcp_manager.call_tool(server_id, tool_name, parameters)

    return {
        "success": result.success,
        "data": result.data,
        "error": result.error,
        "execution_time_ms": result.execution_time_ms,
    }


@router.get("/tools", response_model=list[dict])
async def list_all_tools(current_user: User = Depends(get_current_user)):
    """List all tools from all connected MCP servers."""
    tools = mcp_manager.get_all_tools()

    return [
        {
            "name": tool.name,
            "description": tool.description,
            "server_id": tool.server_id,
            "parameters": tool.parameters,
        }
        for tool in tools
    ]


@router.get("/tools/schemas")
async def get_tool_schemas(current_user: User = Depends(get_current_user)):
    """Get OpenAI function schemas for all MCP tools."""
    schemas = mcp_manager.get_all_schemas()
    return {"schemas": schemas, "count": len(schemas)}


@router.get("/stats", response_model=MCPServerStats)
async def get_stats(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get MCP statistics."""
    stats = await mcp_manager.get_stats(db, current_user.id)
    return stats
