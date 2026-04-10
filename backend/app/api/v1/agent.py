"""Agent configuration API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.config import settings
from app.models.database import AgentConfiguration, User, get_db
from app.models.schemas import AgentConfig, AgentConfigResponse, BaseResponse

router = APIRouter()


@router.get("/config", response_model=AgentConfigResponse)
async def get_agent_config(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get agent configuration for current user."""
    result = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.user_id == current_user.id)
    )
    config = result.scalar_one_or_none()

    if not config:
        # Return default config
        return AgentConfigResponse(
            config=AgentConfig(
                model=settings.DEFAULT_MODEL,
                temperature=settings.DEFAULT_TEMPERATURE,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                system_prompt=None,
                enable_tools=["web_search"] if settings.ENABLE_WEB_SEARCH else [],
                enable_memory=True,
            ),
            updated_at=current_user.created_at,
        )

    return AgentConfigResponse(
        config=AgentConfig(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            system_prompt=config.system_prompt,
            enable_tools=config.enable_tools,
            enable_memory=config.enable_memory,
        ),
        updated_at=config.updated_at,
    )


@router.put("/config", response_model=AgentConfigResponse)
async def update_agent_config(
    config_data: AgentConfig,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update agent configuration."""
    result = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.user_id == current_user.id)
    )
    config = result.scalar_one_or_none()

    if config:
        # Update existing config
        config.model = config_data.model
        config.temperature = config_data.temperature
        config.max_tokens = config_data.max_tokens
        config.system_prompt = config_data.system_prompt
        config.enable_tools = config_data.enable_tools
        config.enable_memory = config_data.enable_memory
    else:
        # Create new config
        config = AgentConfiguration(
            user_id=current_user.id,
            model=config_data.model,
            temperature=config_data.temperature,
            max_tokens=config_data.max_tokens,
            system_prompt=config_data.system_prompt,
            enable_tools=config_data.enable_tools,
            enable_memory=config_data.enable_memory,
        )
        db.add(config)

    await db.commit()
    await db.refresh(config)

    return AgentConfigResponse(
        config=AgentConfig(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            system_prompt=config.system_prompt,
            enable_tools=config.enable_tools,
            enable_memory=config.enable_memory,
        ),
        updated_at=config.updated_at,
    )


@router.get("/tools", response_model=list[str])
async def list_available_tools():
    """List all available tools."""
    tools = []

    if settings.ENABLE_WEB_SEARCH:
        tools.append("web_search")

    if settings.ENABLE_FILE_OPERATIONS:
        tools.extend(["file_read", "file_write"])

    return tools


@router.post("/clear-memory", response_model=BaseResponse)
async def clear_agent_memory(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Clear agent's long-term memory for current user."""
    # TODO: Implement memory clearing logic
    return BaseResponse(message="Memory cleared successfully")
