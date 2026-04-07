"""Agent core implementation using LiteLLM for multi-model support."""

from typing import AsyncGenerator, List, Dict, Any, Optional
import litellm
from litellm import acompletion

from app.config import settings
from app.agent.tools import ToolManager


class AgentCore:
    """Core agent implementation."""
    
    def __init__(self):
        """Initialize the agent."""
        self.tool_manager = ToolManager()
        self._setup_api_keys()
    
    def _setup_api_keys(self):
        """Setup API keys for different providers."""
        if settings.OPENAI_API_KEY:
            litellm.api_key = settings.OPENAI_API_KEY
        
        # Set other API keys in environment or litellm params
        self.provider_keys = {
            "openai": settings.OPENAI_API_KEY,
            "anthropic": settings.ANTHROPIC_API_KEY,
            "deepseek": settings.DEEPSEEK_API_KEY,
            "moonshot": settings.MOONSHOT_API_KEY,
            "openrouter": settings.OPENROUTER_API_KEY,
        }
    
    def _get_model_name(self, model: str) -> str:
        """Convert model ID to LiteLLM format."""
        # Map model IDs to LiteLLM format
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
    
    def _get_api_key(self, model: str) -> Optional[str]:
        """Get API key for a specific model."""
        if "claude" in model:
            return settings.ANTHROPIC_API_KEY
        elif "deepseek" in model:
            return settings.DEEPSEEK_API_KEY
        elif "moonshot" in model:
            return settings.MOONSHOT_API_KEY
        elif "openrouter" in model:
            return settings.OPENROUTER_API_KEY
        else:
            return settings.OPENAI_API_KEY
    
    async def chat(
        self,
        message: str,
        model: str = None,
        temperature: float = 0.7,
        history: List[Dict[str, str]] = None,
        system_prompt: str = None
    ) -> str:
        """Send a chat message and get response."""
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
        
        # Make request
        try:
            response = await acompletion(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                api_key=api_key
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def chat_stream(
        self,
        message: str,
        model: str = None,
        temperature: float = 0.7,
        history: List[Dict[str, str]] = None,
        system_prompt: str = None
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
        
        # Make streaming request
        try:
            response = await acompletion(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                api_key=api_key,
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error: {str(e)}"
    
    async def chat_with_tools(
        self,
        message: str,
        tools: List[str],
        model: str = None,
        temperature: float = 0.7,
        history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Send a chat message with tool support."""
        model = model or settings.DEFAULT_MODEL
        model_name = self._get_model_name(model)
        api_key = self._get_api_key(model)
        
        # Get tool definitions
        tool_definitions = self.tool_manager.get_tool_definitions(tools)
        
        # Build messages
        messages = []
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": message})
        
        # Make request with tools
        try:
            response = await acompletion(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                api_key=api_key,
                tools=tool_definitions if tool_definitions else None
            )
            
            message = response.choices[0].message
            
            # Check if tool calls are needed
            if hasattr(message, 'tool_calls') and message.tool_calls:
                # Execute tools
                tool_results = []
                for tool_call in message.tool_calls:
                    result = await self.tool_manager.execute_tool(
                        tool_call.function.name,
                        tool_call.function.arguments
                    )
                    tool_results.append({
                        "tool": tool_call.function.name,
                        "result": result
                    })
                
                return {
                    "content": message.content,
                    "tool_calls": tool_results
                }
            
            return {
                "content": message.content,
                "tool_calls": []
            }
        except Exception as e:
            return {
                "content": f"Error: {str(e)}",
                "tool_calls": []
            }
