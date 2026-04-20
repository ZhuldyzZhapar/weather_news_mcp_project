from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


class MCPToolError(RuntimeError):
    """Raised when an MCP tool call fails."""


class MCPToolClient:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)

    async def call_tool(self, server_rel_path: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        server_path = self.project_root / server_rel_path
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(server_path)],
            env=None,
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                if result.isError:
                    raise MCPToolError(self._extract_text(result) or f"Tool '{tool_name}' failed.")

                if getattr(result, "structuredContent", None):
                    return result.structuredContent

                text = self._extract_text(result)
                if not text:
                    return {"ok": True, "message": "Empty response from MCP tool."}

                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"ok": True, "message": text}

    @staticmethod
    def _extract_text(result: Any) -> str:
        parts: list[str] = []
        for content in getattr(result, "content", []):
            if isinstance(content, types.TextContent):
                parts.append(content.text)
        return "\n".join(parts).strip()

    def call_tool_sync(self, server_rel_path: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return asyncio.run(self.call_tool(server_rel_path, tool_name, arguments))
