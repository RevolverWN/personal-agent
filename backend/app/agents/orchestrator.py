"""Agent orchestrator for processing messages."""

from collections.abc import AsyncGenerator
from typing import Any


class AgentOrchestrator:
    """Orchestrates message processing through the agent system."""

    async def process(
        self, user_id: int, message: str, conversation_id: str | None = None
    ) -> dict[str, Any]:
        """
        Process a message synchronously.

        Args:
            user_id: The user ID
            message: The user message
            conversation_id: Optional conversation ID

        Returns:
            Response dictionary with content, model, tokens_used
        """
        # For now, return a simple echo response
        # In production, this would call the LLM and agent system
        return {
            "content": f"Echo: {message}",
            "model": "test-model",
            "tokens_used": len(message.split()),
        }

    async def stream_process(
        self, user_id: int, message: str, conversation_id: str | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Process a message with streaming response.

        Args:
            user_id: The user ID
            message: The user message
            conversation_id: Optional conversation ID

        Yields:
            Chunks of the response
        """
        # For now, yield a simple streaming response
        # In production, this would stream from the LLM
        response = f"Echo: {message}"
        words = response.split()

        for i, word in enumerate(words):
            if i < len(words) - 1:
                yield word + " "
            else:
                yield word


# Global orchestrator instance
orchestrator = AgentOrchestrator()
