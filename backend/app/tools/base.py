"""Base tool class and utilities."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """Result of a tool execution."""

    success: bool
    data: Any
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {"success": self.success, "data": self.data, "error": self.error}


class BaseTool(ABC):
    """Base class for all tools."""

    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = {}

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass

    def get_schema(self) -> dict[str, Any]:
        """Get OpenAI function schema for this tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
