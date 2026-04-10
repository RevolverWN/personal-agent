"""Agent core implementation using LiteLLM for multi-model support."""

import json
from collections.abc import AsyncGenerator
from typing import Any

import litellm
from litellm import acompletion

from app.config import settings
from app.memory.extractor import MemoryExtractor
from app.tools.manager import tool_manager


class AgentCore:
    """Core agent implementation."""

    def __init__(self):
        """Initialize the agent."""
        self._setup_api_keys()
        self.memory_extractor = MemoryExtractor()

    def _setup_api_keys(self):
        """Setup API keys for different providers."""
        if settings.OPENAI_API_KEY:
            litellm.api_key = settings.OPENAI_API_KEY

    def _get_model_name(self, model: str) -> str:
        """Convert model ID to LiteLLM format."""
        model_map = {
            "gpt-4o": "gpt-4o",
            "gpt-4o-mini": "gpt-4o-mini",
            "claude-3-opus-20240229": "claude-3-opus-20240229",
            "claude-3-sonnet-20240229": "claude-3-sonnet-20240229",
            "deepseek-chat": "deepseek/deepseek-chat",
            "deepseek-reasoner": "deepseek/deepseek-reasoner",
            "moonshot-v1-8k": "moonshot/moonshot-v1-8k",
        }
        return model_map.get(model, model)

    def _get_api_key(self, model: str) -> str | None:
        """Get API key for a specific model."""
        if "claude" in model:
            return settings.ANTHROPIC_API_KEY
        elif "deepseek" in model:
            return settings.DEEPSEEK_API_KEY
        elif "moonshot" in model:
            return settings.MOONSHOT_API_KEY
        else:
            return settings.OPENAI_API_KEY

    async def chat(
        self,
        message: str,
        model: str = None,
        temperature: float = 0.7,
        history: list[dict[str, str]] = None,
        system_prompt: str = None,
        enable_tools: bool = True,
        user_id: int = None,
        db_session=None,
    ) -> dict[str, Any]:
        """Send a chat message and get response with optional tool support."""
        model = model or settings.DEFAULT_MODEL
        model_name = self._get_model_name(model)
        api_key = self._get_api_key(model)

        # Enhance system prompt with memories if available
        enhanced_system_prompt = system_prompt or "You are a helpful AI assistant."
        if user_id and db_session and settings.ENABLE_MEMORY:
            from app.memory.retriever import MemoryRetriever
            from app.memory.store import MemoryStore

            store = MemoryStore(db_session)
            retriever = MemoryRetriever(store)

            enhanced_system_prompt = await retriever.get_system_prompt_with_memory(
                user_id=user_id, current_message=message, base_system_prompt=system_prompt
            )

        # Build messages
        messages = []
        if enhanced_system_prompt:
            messages.append({"role": "system", "content": enhanced_system_prompt})

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": message})

        # Get available tools
        tools = tool_manager.get_all_schemas() if enable_tools else None

        try:
            # Make request
            response = await acompletion(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                api_key=api_key,
                tools=tools if tools else None,
            )

            message_response = response.choices[0].message
            content = message_response.content or ""

            # Check for tool calls
            tool_calls = []
            if hasattr(message_response, "tool_calls") and message_response.tool_calls:
                for tool_call in message_response.tool_calls:
                    # Execute tool
                    result = await tool_manager.execute_tool(
                        tool_call.function.name, tool_call.function.arguments
                    )

                    tool_calls.append(
                        {
                            "tool": tool_call.function.name,
                            "arguments": json.loads(tool_call.function.arguments),
                            "result": result.to_dict(),
                        }
                    )

            # Extract memories from conversation if enabled
            extracted_memories = []
            if user_id and db_session and settings.ENABLE_MEMORY:
                conversation_messages = history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": content},
                ]

                from app.memory.models import MemoryCreate
                from app.memory.store import MemoryStore

                memories = await self.memory_extractor.extract_memories(conversation_messages)
                store = MemoryStore(db_session)

                for mem in memories:
                    memory_data = MemoryCreate(
                        content=mem.content, category=mem.category, importance=mem.importance
                    )
                    # Try to merge with existing or create new
                    created_mem = await store.merge_similar(user_id, memory_data)
                    if created_mem:
                        extracted_memories.append(
                            {
                                "id": created_mem.id,
                                "content": created_mem.content,
                                "category": created_mem.category,
                            }
                        )

            return {
                "content": content,
                "tool_calls": tool_calls,
                "extracted_memories": extracted_memories,
                "model": model,
                "usage": response.usage.dict() if response.usage else None,
            }

        except Exception as e:
            return {
                "content": f"Error: {str(e)}",
                "tool_calls": [],
                "extracted_memories": [],
                "model": model,
                "usage": None,
            }

    async def chat_stream(
        self,
        message: str,
        model: str = None,
        temperature: float = 0.7,
        history: list[dict[str, str]] = None,
        system_prompt: str = None,
        enable_tools: bool = False,  # Disable tools for streaming
    ) -> AsyncGenerator[str, None]:
        """Send a chat message and get streaming response."""
        model = model or settings.DEFAULT_MODEL
        model_name = self._get_model_name(model)
        api_key = self._get_api_key(model)

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": message})

        try:
            response = await acompletion(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                api_key=api_key,
                stream=True,
            )

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"Error: {str(e)}"

    async def execute_tool_directly(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a tool directly without LLM."""
        result = await tool_manager.execute_tool(tool_name, arguments)
        return result.to_dict()

    def get_available_tools(self) -> list[dict[str, Any]]:
        """Get list of available tools."""
        return tool_manager.get_all_tools_info()
