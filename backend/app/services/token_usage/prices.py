"""Model pricing table (per 1K tokens, USD)."""

MODEL_PRICES: dict[str, dict[str, float]] = {
    # OpenAI
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    # Anthropic
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku-20241022": {"input": 0.001, "output": 0.005},
    # DeepSeek
    "deepseek-chat": {"input": 0.001, "output": 0.002},
    "deepseek-reasoner": {"input": 0.004, "output": 0.016},
    # Moonshot / Kimi
    "moonshot-v1-8k": {"input": 0.012, "output": 0.012},
    "moonshot-v1-32k": {"input": 0.024, "output": 0.024},
    # Default fallback
    "default": {"input": 0.001, "output": 0.001},
}


def get_model_price(model: str) -> dict[str, float]:
    """Get pricing for a model, falling back to default."""
    # Strip provider prefix (e.g. "deepseek/deepseek-chat" -> "deepseek-chat")
    clean = model.split("/")[-1] if "/" in model else model
    return MODEL_PRICES.get(clean, MODEL_PRICES["default"])


def _infer_provider(model: str) -> str:
    """Infer provider from model name."""
    model_lower = model.lower()
    if "claude" in model_lower:
        return "anthropic"
    if "deepseek" in model_lower:
        return "deepseek"
    if "moonshot" in model_lower:
        return "moonshot"
    if "gpt" in model_lower or model_lower.startswith("o1") or model_lower.startswith("o3"):
        return "openai"
    return "unknown"


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate cost in USD for a given token usage."""
    prices = get_model_price(model)
    input_cost = (prompt_tokens / 1000) * prices["input"]
    output_cost = (completion_tokens / 1000) * prices["output"]
    return round(input_cost + output_cost, 6)
