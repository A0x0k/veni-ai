"""
MCP (Model Context Protocol) client adapter for Veni AI.

Allows Veni to connect to external MCP servers and use
their tools as native Veni tools.

MCP Spec: https://modelcontextprotocol.io
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from veni.tools.base import AITool


class MCPToolWrapper(AITool):
    """Wraps an MCP tool declaration as a Veni AITool."""

    def __init__(
        self,
        tool_spec: Dict[str, Any],
        mcp_client: "MCPClient",
    ):
        self._tool_spec = tool_spec
        self._client = mcp_client

    @property
    def name(self) -> str:
        return self._tool_spec["name"]

    @property
    def description(self) -> str:
        return self._tool_spec.get("description", "No description provided.")

    @property
    def parameters(self) -> Dict[str, Any]:
        return self._tool_spec.get("inputSchema", {})

    def execute(self, **kwargs) -> Any:
        """Execute the MCP tool via the client."""
        return self._client.call_tool(self.name, kwargs)


class MCPClient:
    """
    Lightweight MCP client using stdio transport.

    Connects to an MCP server via a subprocess (stdio transport)
    and exposes its tools to Veni's tool registry.
    """

    def __init__(self, command: str, args: Optional[List[str]] = None):
        """
        Initialize an MCP client.

        Args:
            command: The command to run (e.g., "npx", "python")
            args: Arguments to the command (e.g., ["-y", "@modelcontextprotocol/server-filesystem"])
        """
        self.command = command
        self.args = args or []
        self._process: Optional[subprocess.Popen] = None
        self._tools: List[Dict[str, Any]] = []
        self._request_id = 0

    def connect(self) -> bool:
        """Start the MCP server process and initialize the protocol."""
        try:
            cmd = [self.command] + self.args
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            # Send initialize
            result = self._send_request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "veni-ai", "version": "1.2.0"},
                },
            )
            if result is None:
                return False

            # Send initialized notification
            self._send_notification("notifications/initialized", {})

            # List available tools
            tools_result = self._send_request("tools/list", {})
            if tools_result and "tools" in tools_result:
                self._tools = tools_result["tools"]
                return True

            return False
        except Exception:
            return False

    def disconnect(self):
        """Terminate the MCP server process."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
            self._process = None

    def get_tools(self, bot: Any) -> List[MCPToolWrapper]:
        """Get all MCP tools as Veni AITool instances."""
        return [MCPToolWrapper(spec, self) for spec in self._tools]

    def get_tool_names(self) -> List[str]:
        """Get names of all available MCP tools."""
        return [t["name"] for t in self._tools]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Call an MCP tool with the given arguments."""
        result = self._send_request(
            "tools/call", {"name": name, "arguments": arguments}
        )
        if result is None:
            return f"Error: MCP tool '{name}' returned no result."
        # Extract content from MCP response
        content = result.get("content", [])
        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict):
                    texts.append(item.get("text", str(item)))
                else:
                    texts.append(str(item))
            return "\n".join(texts) if texts else str(content)
        return str(content)

    def _send_request(
        self, method: str, params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Send a JSON-RPC request and wait for the response."""
        if not self._process or not self._process.stdin:
            return None

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }
        self._process.stdin.write(json.dumps(request) + "\n")
        self._process.stdin.flush()

        # Read response
        if self._process.stdout:
            line = self._process.stdout.readline()
            if line:
                try:
                    response = json.loads(line.strip())
                    return response.get("result")
                except json.JSONDecodeError:
                    return None
        return None

    def _send_notification(self, method: str, params: Dict[str, Any]) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        if not self._process or not self._process.stdin:
            return

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        self._process.stdin.write(json.dumps(notification) + "\n")
        self._process.stdin.flush()


def load_mcp_config(config_path: str) -> List[MCPClient]:
    """
    Load MCP server configurations from a JSON file.

    Expected format:
    {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
            },
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"]
            }
        }
    }
    """
    path = Path(config_path)
    if not path.exists():
        return []

    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    clients = []
    servers = config.get("mcpServers", {})
    for name, server_config in servers.items():
        command = server_config.get("command", "")
        args = server_config.get("args", [])
        if command:
            clients.append(MCPClient(command, args))

    return clients
