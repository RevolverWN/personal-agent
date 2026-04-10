"""Agent manager for creating and managing agents."""

import uuid
from datetime import datetime

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import (
    BUILTIN_ROLES,
    AgentCollaborationRequest,
    AgentCollaborationResponse,
    AgentCreate,
    AgentInstance,
    AgentRole,
    AgentUpdate,
)


class AgentManager:
    """Manage agent roles and instances."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self._builtin_roles = {role.id: role for role in BUILTIN_ROLES}

    # ==================== Role Management ====================

    def get_builtin_roles(self) -> list[AgentRole]:
        """Get all built-in agent roles."""
        return list(self._builtin_roles.values())

    def get_role(self, role_id: str) -> AgentRole | None:
        """Get a built-in role by ID."""
        return self._builtin_roles.get(role_id)

    # ==================== Agent Instance Management ====================

    async def create_agent(self, user_id: int, agent_data: AgentCreate) -> AgentInstance:
        """Create a new agent instance."""
        from app.models.database import AgentInstance as AgentDB

        agent_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # If role_id provided, use role defaults
        role = None
        if agent_data.role_id:
            role = self.get_role(agent_data.role_id)

        db_agent = AgentDB(
            id=agent_id,
            user_id=user_id,
            role_id=agent_data.role_id,
            name=agent_data.name,
            description=agent_data.description or (role.description if role else ""),
            system_prompt=agent_data.system_prompt,
            icon=agent_data.icon,
            color=agent_data.color,
            model=agent_data.model,
            temperature=agent_data.temperature,
            tools=agent_data.tools,
            enable_memory=agent_data.enable_memory,
            is_active=True,
            created_at=now,
            updated_at=now,
            usage_count=0,
        )

        self.db.add(db_agent)
        await self.db.commit()
        await self.db.refresh(db_agent)

        return AgentInstance.model_validate(db_agent)

    async def create_agent_from_role(
        self, user_id: int, role_id: str, custom_name: str | None = None
    ) -> AgentInstance | None:
        """Create an agent from a built-in role."""
        role = self.get_role(role_id)
        if not role:
            return None

        agent_data = AgentCreate(
            role_id=role_id,
            name=custom_name or role.name,
            description=role.description,
            system_prompt=role.system_prompt,
            icon=role.icon,
            color=role.color,
            model=role.default_model,
            temperature=role.temperature,
            tools=role.tools,
        )

        return await self.create_agent(user_id, agent_data)

    async def get_agent(self, agent_id: str, user_id: int) -> AgentInstance | None:
        """Get an agent by ID."""
        from app.models.database import AgentInstance as AgentDB

        result = await self.db.execute(
            select(AgentDB).where(and_(AgentDB.id == agent_id, AgentDB.user_id == user_id))
        )
        db_agent = result.scalar_one_or_none()

        if db_agent:
            return AgentInstance.model_validate(db_agent)
        return None

    async def get_user_agents(
        self, user_id: int, include_builtin: bool = True
    ) -> list[AgentInstance]:
        """Get all agents for a user."""
        from app.models.database import AgentInstance as AgentDB

        result = await self.db.execute(
            select(AgentDB).where(AgentDB.user_id == user_id).order_by(desc(AgentDB.usage_count))
        )

        agents = [AgentInstance.model_validate(a) for a in result.scalars().all()]

        # Add built-in role agents if requested
        if include_builtin:
            for role in self.get_builtin_roles():
                # Check if user already has this role
                if not any(a.role_id == role.id for a in agents):
                    agents.append(
                        AgentInstance(
                            id=role.id,  # Use role ID for built-ins
                            user_id=user_id,
                            role_id=role.id,
                            name=role.name,
                            description=role.description,
                            system_prompt=role.system_prompt,
                            icon=role.icon,
                            color=role.color,
                            model=role.default_model,
                            temperature=role.temperature,
                            tools=role.tools,
                            enable_memory=True,
                            is_active=True,
                            created_at=role.created_at,
                            updated_at=role.created_at,
                            usage_count=0,
                        )
                    )

        return agents

    async def update_agent(
        self, agent_id: str, user_id: int, update_data: AgentUpdate
    ) -> AgentInstance | None:
        """Update an agent."""
        from app.models.database import AgentInstance as AgentDB

        result = await self.db.execute(
            select(AgentDB).where(and_(AgentDB.id == agent_id, AgentDB.user_id == user_id))
        )
        db_agent = result.scalar_one_or_none()

        if not db_agent:
            return None

        # Update fields
        if update_data.name is not None:
            db_agent.name = update_data.name
        if update_data.description is not None:
            db_agent.description = update_data.description
        if update_data.system_prompt is not None:
            db_agent.system_prompt = update_data.system_prompt
        if update_data.icon is not None:
            db_agent.icon = update_data.icon
        if update_data.color is not None:
            db_agent.color = update_data.color
        if update_data.model is not None:
            db_agent.model = update_data.model
        if update_data.temperature is not None:
            db_agent.temperature = update_data.temperature
        if update_data.tools is not None:
            db_agent.tools = update_data.tools
        if update_data.enable_memory is not None:
            db_agent.enable_memory = update_data.enable_memory
        if update_data.is_active is not None:
            db_agent.is_active = update_data.is_active

        db_agent.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(db_agent)

        return AgentInstance.model_validate(db_agent)

    async def delete_agent(self, agent_id: str, user_id: int) -> bool:
        """Delete an agent."""
        from app.models.database import AgentInstance as AgentDB

        result = await self.db.execute(
            select(AgentDB).where(and_(AgentDB.id == agent_id, AgentDB.user_id == user_id))
        )
        db_agent = result.scalar_one_or_none()

        if not db_agent:
            return False

        await self.db.delete(db_agent)
        await self.db.commit()

        return True

    async def increment_usage(self, agent_id: str) -> None:
        """Increment agent usage count."""
        from app.models.database import AgentInstance as AgentDB

        result = await self.db.execute(select(AgentDB).where(AgentDB.id == agent_id))
        db_agent = result.scalar_one_or_none()

        if db_agent:
            db_agent.usage_count += 1
            db_agent.updated_at = datetime.utcnow()
            await self.db.commit()

    # ==================== Collaboration ====================

    async def collaborate(
        self, request: AgentCollaborationRequest, user_id: int
    ) -> AgentCollaborationResponse:
        """Execute multi-agent collaboration."""
        from app.agent.core import AgentCore

        agent_core = AgentCore()
        responses = []

        if request.mode == "sequential":
            # Each agent builds on previous responses
            context = request.message
            for agent_id in request.agent_ids:
                agent = await self.get_agent(agent_id, user_id)
                if not agent:
                    continue

                # Add previous responses to context
                if responses:
                    context += "\n\nPrevious insights:\n"
                    for r in responses:
                        context += f"- {r['agent_name']}: {r['response'][:200]}...\n"

                response_data = await agent_core.chat(
                    message=context,
                    model=agent.model,
                    temperature=agent.temperature,
                    system_prompt=agent.system_prompt,
                    enable_tools=True,
                )

                responses.append(
                    {
                        "agent_id": agent_id,
                        "agent_name": agent.name,
                        "response": response_data["content"],
                        "tool_calls": response_data.get("tool_calls", []),
                    }
                )

        elif request.mode == "parallel":
            # All agents respond independently
            import asyncio

            async def get_agent_response(agent_id: str):
                agent = await self.get_agent(agent_id, user_id)
                if not agent:
                    return None

                response_data = await agent_core.chat(
                    message=request.message,
                    model=agent.model,
                    temperature=agent.temperature,
                    system_prompt=agent.system_prompt,
                    enable_tools=True,
                )

                return {
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "response": response_data["content"],
                    "tool_calls": response_data.get("tool_calls", []),
                }

            # Execute all in parallel
            tasks = [get_agent_response(aid) for aid in request.agent_ids]
            results = await asyncio.gather(*tasks)
            responses = [r for r in results if r]

        elif request.mode == "debate":
            # Agents debate a topic
            debate_rounds = 2
            debate_context = f"Topic: {request.message}\n\n"

            for round_num in range(debate_rounds):
                debate_context += f"\n--- Round {round_num + 1} ---\n"

                for agent_id in request.agent_ids:
                    agent = await self.get_agent(agent_id, user_id)
                    if not agent:
                        continue

                    prompt = f"{debate_context}\nAs {agent.name}, provide your perspective on this topic. Consider previous arguments and either support or challenge them."

                    response_data = await agent_core.chat(
                        message=prompt,
                        model=agent.model,
                        temperature=agent.temperature + 0.2,  # Increase creativity for debate
                        system_prompt=agent.system_prompt,
                        enable_tools=True,
                    )

                    debate_context += f"\n{agent.name}: {response_data['content']}\n"

                    if round_num == debate_rounds - 1:
                        responses.append(
                            {
                                "agent_id": agent_id,
                                "agent_name": agent.name,
                                "response": response_data["content"],
                                "tool_calls": response_data.get("tool_calls", []),
                            }
                        )

        # Generate synthesis if multiple responses
        synthesis = None
        if len(responses) > 1:
            synthesis_prompt = f"Synthesize the following perspectives on: {request.message}\n\n"
            for r in responses:
                synthesis_prompt += f"{r['agent_name']}: {r['response'][:500]}...\n\n"
            synthesis_prompt += "\nProvide a balanced synthesis that highlights key insights and areas of agreement/disagreement."

            synthesis_data = await agent_core.chat(
                message=synthesis_prompt, model="gpt-4o-mini", temperature=0.5, enable_tools=False
            )
            synthesis = synthesis_data["content"]

        return AgentCollaborationResponse(
            responses=responses, synthesis=synthesis, collaboration_id=str(uuid.uuid4())
        )
