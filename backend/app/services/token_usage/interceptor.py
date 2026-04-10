"""LiteLLM interceptor — auto-record token usage from responses."""

from __future__ import annotations

import logging
from typing import Optional, Any

from app.services.token_usage.prices import calculate_cost, _infer_provider

logger = logging.getLogger(__name__)


class TokenUsageInterceptor:
    """Intercept LiteLLM responses and extract token usage for recording.

    Usage in the calling code (e.g. AgentCore):
        interceptor = TokenUsageInterceptor()
        usage_data = interceptor.extract_usage(response, model="gpt-4o")
        # then pass usage_data to TokenUsageService.record()
    """

    def extract_usage(
        self,
        response: Any,
        model: str,
        session_id: Optional[str] = None,
    ) -> dict:
        """Extract token usage from a LiteLLM / OpenAI-style response.

        Returns a dict with: model, prompt_tokens, completion_tokens,
        total_tokens, provider, cost — or empty dict if usage unavailable.
        """
        try:
            usage = getattr(response, "usage", None)
            if usage is None:
                logger.debug("No usage object on response")
                return {}

            prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(usage, "completion_tokens", 0) or 0
            total_tokens = getattr(usage, "total_tokens", 0) or 0

            if total_tokens == 0:
                total_tokens = prompt_tokens + completion_tokens

            provider = _infer_provider(model)
            cost = calculate_cost(model, prompt_tokens, completion_tokens)

            return {
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "provider": provider,
                "cost": cost,
                "session_id": session_id,
            }
        except Exception as exc:
            logger.warning("Failed to extract token usage: %s", exc)
            return {}
