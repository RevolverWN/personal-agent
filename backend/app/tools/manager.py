"""Tool manager for registering and executing tools."""

import json
from typing import Any

from app.tools.base import BaseTool, ToolResult
from app.tools.code_execution import CalculateTool, CodeExecutionTool
from app.tools.file_analysis import FileInfoTool, FileListTool, FileReadTool
from app.tools.system_tools import CurrentTimeTool, DateCalculatorTool, SystemInfoTool
from app.tools.web_search import WebFetchTool, WebSearchTool


class ToolManager:
    """Manager for all available tools."""

    def __init__(self):
        """Initialize tool manager with all available tools."""
        self._tools: dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register all default tools."""
        tools = [
            # Web tools
            WebSearchTool(),
            WebFetchTool(),
            # Code & Math tools
            CodeExecutionTool(),
            CalculateTool(),
            # File tools
            FileReadTool(),
            FileListTool(),
            FileInfoTool(),
            # System tools
            CurrentTimeTool(),
            DateCalculatorTool(),
            SystemInfoTool(),
        ]

        for tool in tools:
            self.register_tool(tool)

    def register_tool(self, tool: BaseTool):
        """Register a new tool."""
        self._tools[tool.name] = tool

    def unregister_tool(self, tool_name: str):
        """Unregister a tool."""
        if tool_name in self._tools:
            del self._tools[tool_name]

    def get_tool(self, name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_all_schemas(self) -> list[dict[str, Any]]:
        """Get schemas for all registered tools."""
        return [tool.get_schema() for tool in self._tools.values()]

    def get_tool_schemas(self, tool_names: list[str]) -> list[dict[str, Any]]:
        """Get schemas for specific tools."""
        schemas = []
        for name in tool_names:
            if name in self._tools:
                schemas.append(self._tools[name].get_schema())
        return schemas

    async def execute_tool(self, tool_name: str, arguments: Any) -> ToolResult:
        """Execute a tool with given arguments."""
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult(success=False, data=None, error=f"Tool '{tool_name}' not found")

        try:
            # Parse arguments if string
            if isinstance(arguments, str):
                try:
                    kwargs = json.loads(arguments)
                except json.JSONDecodeError:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Invalid arguments format for tool '{tool_name}'",
                    )
            else:
                kwargs = arguments

            # Execute tool
            result = await tool.execute(**kwargs)
            return result

        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Tool execution error: {str(e)}")

    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """Get information about a tool."""
        tool = self._tools.get(tool_name)
        if not tool:
            return None

        return {"name": tool.name, "description": tool.description, "schema": tool.get_schema()}

    def get_all_tools_info(self) -> list[dict[str, Any]]:
        """Get information about all tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
            }
            for tool in self._tools.values()
        ]


# Global tool manager instance
tool_manager = ToolManager()
