"""Agent management API routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, User
from app.models.schemas import BaseResponse
from app.api.v1.auth import get_current_user
from app.agents.manager import AgentManager
from app.agents.models import (
    AgentRole, AgentInstance, AgentCreate, AgentUpdate,
    AgentCollaborationRequest, AgentCollaborationResponse,
    BUILTIN_ROLES
)

router = APIRouter()


@router.get("/roles", response_model=List[AgentRole])
async def list_builtin_roles(
    current_user: User = Depends(get_current_user)
):
    """List all built-in agent roles."""
    manager = AgentManager(None)
    return manager.get_builtin_roles()


@router.get("/roles/{role_id}", response_model=AgentRole)
async def get_role(
    role_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific built-in role."""
    manager = AgentManager(None)
    role = manager.get_role(role_id)
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return role


@router.get("", response_model=List[AgentInstance])
async def list_agents(
    include_builtin: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all agents for the user."""
    manager = AgentManager(db)
    agents = await manager.get_user_agents(
        user_id=current_user.id,
        include_builtin=include_builtin
    )
    return agents


@router.post("", response_model=AgentInstance)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new custom agent."""
    manager = AgentManager(db)
    agent = await manager.create_agent(current_user.id, agent_data)
    return agent


@router.post("/from-role/{role_id}", response_model=AgentInstance)
async def create_agent_from_role(
    role_id: str,
    custom_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create an agent from a built-in role."""
    manager = AgentManager(db)
    agent = await manager.create_agent_from_role(
        user_id=current_user.id,
        role_id=role_id,
        custom_name=custom_name
    )
    
    if not agent:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return agent


@router.get("/{agent_id}", response_model=AgentInstance)
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific agent."""
    manager = AgentManager(db)
    agent = await manager.get_agent(agent_id, current_user.id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent


@router.put("/{agent_id}", response_model=AgentInstance)
async def update_agent(
    agent_id: str,
    update_data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an agent."""
    manager = AgentManager(db)
    agent = await manager.update_agent(agent_id, current_user.id, update_data)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent


@router.delete("/{agent_id}", response_model=BaseResponse)
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an agent."""
    manager = AgentManager(db)
    deleted = await manager.delete_agent(agent_id, current_user.id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return BaseResponse(message="Agent deleted successfully")


@router.post("/{agent_id}/clone", response_model=AgentInstance)
async def clone_agent(
    agent_id: str,
    new_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clone an existing agent."""
    manager = AgentManager(db)
    
    # Get original agent
    original = await manager.get_agent(agent_id, current_user.id)
    if not original:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Create clone
    clone_data = AgentCreate(
        role_id=original.role_id,
        name=new_name,
        description=f"Cloned from {original.name}: {original.description}",
        system_prompt=original.system_prompt,
        icon=original.icon,
        color=original.color,
        model=original.model,
        temperature=original.temperature,
        tools=original.tools,
        enable_memory=original.enable_memory
    )
    
    clone = await manager.create_agent(current_user.id, clone_data)
    return clone


@router.post("/collaborate", response_model=AgentCollaborationResponse)
async def collaborate(
    request: AgentCollaborationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute multi-agent collaboration."""
    manager = AgentManager(db)
    result = await manager.collaborate(request, current_user.id)
    return result


@router.get("/{agent_id}/stats")
async def get_agent_stats(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get usage statistics for an agent."""
    manager = AgentManager(db)
    agent = await manager.get_agent(agent_id, current_user.id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "agent_id": agent_id,
        "name": agent.name,
        "usage_count": agent.usage_count,
        "created_at": agent.created_at,
        "updated_at": agent.updated_at,
        "is_active": agent.is_active
    }
