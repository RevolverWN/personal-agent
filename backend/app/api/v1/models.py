"""Model management API routes."""

from fastapi import APIRouter

from app.config import settings
from app.models.schemas import ModelInfo, ModelListResponse

router = APIRouter()


# Available models configuration
AVAILABLE_MODELS = [
    ModelInfo(
        id="gpt-4o",
        name="GPT-4o",
        provider="openai",
        description="OpenAI's most capable multimodal model",
        max_tokens=128000,
        supports_vision=True,
        supports_streaming=True,
    ),
    ModelInfo(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider="openai",
        description="Fast, affordable small model for focused tasks",
        max_tokens=128000,
        supports_vision=True,
        supports_streaming=True,
    ),
    ModelInfo(
        id="claude-3-opus-20240229",
        name="Claude 3 Opus",
        provider="anthropic",
        description="Anthropic's most powerful model for complex tasks",
        max_tokens=200000,
        supports_vision=True,
        supports_streaming=True,
    ),
    ModelInfo(
        id="claude-3-sonnet-20240229",
        name="Claude 3 Sonnet",
        provider="anthropic",
        description="Balanced performance and speed",
        max_tokens=200000,
        supports_vision=True,
        supports_streaming=True,
    ),
    ModelInfo(
        id="deepseek-chat",
        name="DeepSeek Chat",
        provider="deepseek",
        description="DeepSeek's conversational AI model",
        max_tokens=64000,
        supports_vision=False,
        supports_streaming=True,
    ),
    ModelInfo(
        id="deepseek-reasoner",
        name="DeepSeek Reasoner",
        provider="deepseek",
        description="DeepSeek's reasoning model",
        max_tokens=64000,
        supports_vision=False,
        supports_streaming=True,
    ),
    ModelInfo(
        id="moonshot-v1-8k",
        name="Moonshot Kimi",
        provider="moonshot",
        description="Moonshot AI's conversational model",
        max_tokens=8192,
        supports_vision=False,
        supports_streaming=True,
    ),
]


@router.get("", response_model=ModelListResponse)
async def list_models():
    """List all available models."""
    return ModelListResponse(models=AVAILABLE_MODELS, default_model=settings.DEFAULT_MODEL)


@router.get("/supported", response_model=list[str])
async def list_supported_providers():
    """List all supported model providers."""
    providers = list(set(model.provider for model in AVAILABLE_MODELS))
    return providers
