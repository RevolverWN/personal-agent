"""Tool management for the agent."""

import json
from typing import Any

from duckduckgo_search import DDGS

from app.config import settings


class ToolManager:
    """Manager for agent tools."""

    def __init__(self):
        """Initialize tool manager."""
        self.tools = {
            "web_search": self._web_search,
            "file_read": self._file_read,
            "file_write": self._file_write,
        }

        self.tool_definitions = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query"},
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 5,
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "file_read",
                    "description": "Read content from a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {"type": "string", "description": "Path to the file"}
                        },
                        "required": ["filepath"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "file_write",
                    "description": "Write content to a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {"type": "string", "description": "Path to the file"},
                            "content": {"type": "string", "description": "Content to write"},
                        },
                        "required": ["filepath", "content"],
                    },
                },
            },
        ]

    def get_tool_definitions(self, tool_names: list[str]) -> list[dict]:
        """Get tool definitions for the specified tools."""
        return [
            tool_def
            for tool_def in self.tool_definitions
            if tool_def["function"]["name"] in tool_names
        ]

    async def execute_tool(self, tool_name: str, arguments: str) -> Any:
        """Execute a tool with given arguments."""
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}

        try:
            args = json.loads(arguments) if isinstance(arguments, str) else arguments
            result = await self.tools[tool_name](**args)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def _web_search(self, query: str, max_results: int = 5) -> dict[str, Any]:
        """Search the web using DuckDuckGo."""
        if not settings.ENABLE_WEB_SEARCH:
            return {"error": "Web search is disabled"}

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return {
                    "query": query,
                    "results": [
                        {
                            "title": r.get("title", ""),
                            "link": r.get("href", ""),
                            "snippet": r.get("body", ""),
                        }
                        for r in results
                    ],
                }
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}

    async def _file_read(self, filepath: str) -> dict[str, Any]:
        """Read a file."""
        if not settings.ENABLE_FILE_OPERATIONS:
            return {"error": "File operations are disabled"}

        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
            return {"filepath": filepath, "content": content, "size": len(content)}
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}

    async def _file_write(self, filepath: str, content: str) -> dict[str, Any]:
        """Write to a file."""
        if not settings.ENABLE_FILE_OPERATIONS:
            return {"error": "File operations are disabled"}

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return {"filepath": filepath, "size": len(content), "status": "written"}
        except Exception as e:
            return {"error": f"Failed to write file: {str(e)}"}
