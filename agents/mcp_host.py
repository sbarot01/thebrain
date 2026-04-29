# ourbrain/mcp_host.py
"""
MCP host for OurBrain.

Spawns the OurBrain MCP server as a subprocess, connects to it over stdio,
and exposes a clean async interface for listing and calling tools.

This is what makes us an "MCP host" — the same role Claude Desktop plays,
but written in Python so we can build multi-agent orchestration on top.
"""

import asyncio
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class OurBrainMCPHost:
    def __init__(self, server_path: str, python_cmd: str = "python"):
        # The command to launch your existing ourbrain_server.py.
        # Same as what Claude Desktop runs — we're just running it ourselves.
        self.server_params = StdioServerParameters(
            command=python_cmd,
            args=[server_path],
            env=None,  # inherits parent environment, so .env loading still works
        )

    @asynccontextmanager
    async def session(self):
        """Open an MCP session. Use as: `async with host.session() as s: ...`"""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    async def list_tools(self):
        """Return the list of tools the server exposes, in MCP's format."""
        async with self.session() as s:
            result = await s.list_tools()
            return result.tools

    async def call_tool(self, name: str, arguments: dict | None = None):
        """Call a single tool by name and return its text result."""
        async with self.session() as s:
            result = await s.call_tool(name, arguments or {})
            # FastMCP tools return text content; we extract it.
            return result.content[0].text if result.content else ""
