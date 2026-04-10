"""Base skill class and utilities."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


class SkillMetadata(BaseModel):
    """Skill metadata."""

    name: str
    description: str
    version: str = "1.0.0"
    author: str = "system"
    tags: list[str] = field(default_factory=list)
    icon: str = "🔧"
    category: str = "general"
    requirements: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] | None = None


@dataclass
class SkillResult:
    """Result of skill execution."""

    success: bool
    data: Any
    message: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "error": self.error,
        }


class BaseSkill(ABC):
    """Base class for all skills."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize skill with optional config."""
        self.config = config or {}
        self.metadata = self._get_metadata()
        self._initialized = False

    @abstractmethod
    def _get_metadata(self) -> SkillMetadata:
        """Get skill metadata."""
        pass

    @abstractmethod
    async def execute(self, action: str, params: dict[str, Any]) -> SkillResult:
        """Execute a skill action."""
        pass

    async def initialize(self) -> bool:
        """Initialize the skill. Override if needed."""
        self._initialized = True
        return True

    async def cleanup(self):
        """Cleanup resources. Override if needed."""
        pass

    def get_actions(self) -> list[dict[str, Any]]:
        """Get available actions for this skill."""
        return []

    def get_schema(self) -> dict[str, Any]:
        """Get OpenAI function schema for this skill."""
        actions = self.get_actions()
        schemas = []

        for action in actions:
            schema = {
                "type": "function",
                "function": {
                    "name": f"{self.metadata.name}.{action['name']}",
                    "description": action.get("description", ""),
                    "parameters": action.get("parameters", {"type": "object", "properties": {}}),
                },
            }
            schemas.append(schema)

        return schemas

    def is_initialized(self) -> bool:
        """Check if skill is initialized."""
        return self._initialized
