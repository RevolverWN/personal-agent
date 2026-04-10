"""MCP client for connecting to MCP servers."""

import asyncio
import json
import subprocess
from collections.abc import Callable
from datetime import datetime
from typing import Any

import httpx

from app.mcp.models import MCPServer, MCPServerStatus, MCPTool, MCPToolResult


class MCPClient:
    """Client for MCP server connection."""

    def __init__(self, server: MCPServer):
        """Initialize client with server config."""
        self.server = server
        self.process: subprocess.Popen | None = None
        self.session: httpx.AsyncClient | None = None
        self._message_id = 0
        self._pending_requests: dict[str, asyncio.Future] = {}
        self._tools: list[MCPTool] = []
        self._on_message: Callable | None = None
        self._read_task: asyncio.Task | None = None

    async def connect(self) -> bool:
        """Connect to MCP server."""
        try:
            if self.server.server_type.value == "stdio":
                return await self._connect_stdio()
            elif self.server.server_type.value == "sse":
                return await self._connect_sse()
            else:
                raise ValueError(f"Unsupported server type: {self.server.server_type}")
        except Exception as e:
            self.server.status = MCPServerStatus.ERROR
            self.server.last_error = str(e)
            return False

    async def _connect_stdio(self) -> bool:
        """Connect to stdio-based MCP server."""
        config = self.server.config

        # Start subprocess
        env = {**config.env} if config.env else None

        self.process = subprocess.Popen(
            [config.command] + config.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        # Start reading task
        self._read_task = asyncio.create_task(self._read_stdio())

        # Initialize session
        init_response = await self._send_request(
            {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "personal-agent", "version": "0.1.0"},
                },
            }
        )

        if init_response:
            self.server.status = MCPServerStatus.CONNECTED
            self.server.last_connected_at = datetime.utcnow()

            # Fetch tools
            await self._fetch_tools()

            return True

        return False

    async def _connect_sse(self) -> bool:
        """Connect to SSE-based MCP server."""
        # For SSE servers, we use HTTP client
        self.session = httpx.AsyncClient(
            base_url=self.server.config.url, timeout=self.server.config.timeout
        )

        # Test connection
        try:
            response = await self.session.get("/health")
            if response.status_code == 200:
                self.server.status = MCPServerStatus.CONNECTED
                self.server.last_connected_at = datetime.utcnow()

                # Fetch tools
                await self._fetch_tools()

                return True
        except Exception as e:
            self.server.last_error = str(e)

        return False

    async def _read_stdio(self):
        """Read messages from stdio."""
        while self.process and self.process.poll() is None:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, self.process.stdout.readline
                )

                if line:
                    message = json.loads(line.strip())
                    await self._handle_message(message)

            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"Error reading from MCP server: {e}")
                break

    async def _handle_message(self, message: dict[str, Any]):
        """Handle incoming message."""
        # Handle response to pending request
        if "id" in message:
            message_id = str(message["id"])
            if message_id in self._pending_requests:
                future = self._pending_requests.pop(message_id)
                if not future.done():
                    future.set_result(message)

        # Handle server notifications
        if "method" in message and "id" not in message:
            if self._on_message:
                await self._on_message(message)

    async def _send_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Send request to MCP server."""
        self._message_id += 1
        request["id"] = self._message_id

        message_id = str(self._message_id)
        future = asyncio.Future()
        self._pending_requests[message_id] = future

        try:
            if self.server.server_type.value == "stdio":
                # Send via stdin
                message = json.dumps(request) + "\n"
                self.process.stdin.write(message)
                self.process.stdin.flush()

            elif self.server.server_type.value == "sse":
                # Send via HTTP
                response = await self.session.post("/rpc", json=request)
                return response.json()

            # Wait for response
            return await asyncio.wait_for(future, timeout=self.server.config.timeout)

        except TimeoutError:
            self._pending_requests.pop(message_id, None)
            return None
        except Exception as e:
            self._pending_requests.pop(message_id, None)
            raise e

    async def _fetch_tools(self):
        """Fetch available tools from server."""
        try:
            response = await self._send_request({"jsonrpc": "2.0", "method": "tools/list"})

            if response and "result" in response:
                tools_data = response["result"].get("tools", [])
                self._tools = [
                    MCPTool(
                        name=tool["name"],
                        description=tool.get("description", ""),
                        parameters=tool.get("parameters", {}),
                        server_id=self.server.id,
                    )
                    for tool in tools_data
                ]
                self.server.tools = self._tools

        except Exception as e:
            print(f"Failed to fetch tools: {e}")

    async def call_tool(self, tool_name: str, parameters: dict[str, Any]) -> MCPToolResult:
        """Call a tool on the MCP server."""
        start_time = datetime.utcnow()

        try:
            response = await self._send_request(
                {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": parameters},
                }
            )

            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            if response and "result" in response:
                result = response["result"]

                # Check for errors in result
                if "error" in result:
                    return MCPToolResult(
                        success=False,
                        data=None,
                        error=result["error"],
                        execution_time_ms=execution_time,
                    )

                return MCPToolResult(
                    success=True,
                    data=result.get("content", result),
                    execution_time_ms=execution_time,
                )

            elif response and "error" in response:
                return MCPToolResult(
                    success=False,
                    data=None,
                    error=response["error"].get("message", "Unknown error"),
                    execution_time_ms=execution_time,
                )

            return MCPToolResult(
                success=False,
                data=None,
                error="No response from server",
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return MCPToolResult(
                success=False, data=None, error=str(e), execution_time_ms=execution_time
            )

    def get_tools(self) -> list[MCPTool]:
        """Get available tools."""
        return self._tools

    async def disconnect(self):
        """Disconnect from server."""
        # Cancel read task
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass

        # Terminate process
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except:
                self.process.kill()

        # Close HTTP session
        if self.session:
            await self.session.aclose()

        self.server.status = MCPServerStatus.DISCONNECTED
        self._tools = []

    def is_connected(self) -> bool:
        """Check if connected."""
        if self.server.server_type.value == "stdio":
            return self.process is not None and self.process.poll() is None
        return self.server.status == MCPServerStatus.CONNECTED
