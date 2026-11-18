"""
claude_code_runtime.py

DEV-ONLY agent runtime: runs the shop agent on the locally installed Claude Code through
the Claude Agent SDK, so the demo can be tried with your own Claude Code login when there
is no API key. Turn it on with AGENT_RUNTIME=claude-code. It is for your machine only:
never ship it, and never let other people's traffic reach it.

It keeps main.py's HTTP contract, so the web app does not change:

  - the shop tools (tools.BACKEND_TOOLS_SCHEMA) are an in-process MCP server; Claude
    Code's own tools are disabled and no settings, CLAUDE.md or skills are loaded;
  - open_checkout is a tool whose call waits: the turn reports it as a pending action,
    and /api/resume completes the call with the result tools.resolve_client_result
    builds from the checkout session.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    tool,
)

import tools
from shop import Shop

SERVER = "shop"
MODEL = os.environ.get("CLAUDE_CODE_MODEL", "claude-opus-5-5")


@dataclass
class Pending:
    tool_use_id: str
    tool_name: str
    client_input: dict


def _text(payload: Any, is_error: bool = False) -> dict:
    result: dict[str, Any] = {
        "content": [{"type": "text", "text": payload if isinstance(payload, str) else tools.dumps(payload)}]
    }
    if is_error:
        result["is_error"] = True
    return result


class ClaudeCodeConversation:
    """One conversation: a Claude Code session, and the turn running in it."""

    def __init__(self, shop: Shop):
        self.shop = shop
        self.outcomes: asyncio.Queue[dict] = asyncio.Queue()
        self.device: Optional[asyncio.Future] = None
        self.client: Optional[ClaudeSDKClient] = None
        self.workdir = tempfile.mkdtemp(prefix="burger-shop-")

    def _tools(self) -> list:
        made = [self._backend_tool(s) for s in tools.BACKEND_TOOLS_SCHEMA]
        made += [self._client_tool(s) for s in tools.CLIENT_TOOLS_SCHEMA]
        return made

    def _backend_tool(self, schema: dict):
        name = schema["name"]

        async def run(args: dict) -> dict:
            return _text(await tools.call_backend_tool(self.shop, name, args))

        return tool(name, schema["description"], schema["input_schema"])(run)

    def _client_tool(self, schema: dict):
        name = schema["name"]

        async def run(args: dict) -> dict:
            client_input, error = tools.start_client_call(self.shop, name, args)
            if error:
                return _text({"error": error}, is_error=True)
            # The turn waits here until the payment window closes and /api/resume answers.
            self.device = asyncio.get_running_loop().create_future()
            await self.outcomes.put({"pending": Pending(f"cc_{uuid.uuid4().hex[:12]}", name, client_input or {})})
            result = await self.device
            self.device = None
            return _text(result)

        return tool(name, schema["description"], schema["input_schema"])(run)

    async def _connect(self) -> ClaudeSDKClient:
        if self.client is None:
            names = [s["name"] for s in tools.BACKEND_TOOLS_SCHEMA + tools.CLIENT_TOOLS_SCHEMA]
            options = ClaudeAgentOptions(
                system_prompt=tools.system_prompt(date.today()),
                model=MODEL,
                tools=[],  # no Bash, files or web: only the shop's tools
                mcp_servers={SERVER: create_sdk_mcp_server(SERVER, tools=self._tools())},
                strict_mcp_config=True,
                allowed_tools=[f"mcp__{SERVER}__{n}" for n in names],
                setting_sources=[],  # no user/project settings, CLAUDE.md or skills
                cwd=self.workdir,
                max_turns=40,
            )
            self.client = ClaudeSDKClient(options)
            await self.client.connect()
        return self.client

    async def _run_turn(self, client: ClaudeSDKClient) -> None:
        """Reads one turn to its end; the reply is the text after the last tool call."""
        text: list[str] = []
        try:
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            text = []
                        elif isinstance(block, TextBlock):
                            text.append(block.text)
                elif isinstance(message, ResultMessage):
                    if message.is_error:
                        await self.outcomes.put({"error": message.result or message.subtype})
                    else:
                        await self.outcomes.put({"reply": "\n\n".join(text) or (message.result or "")})
                    return
        except Exception as e:  # the CLI exited, the login expired...
            await self.outcomes.put({"error": f"Claude Code: {e}"})

    async def turn(self, message: str) -> dict:
        client = await self._connect()
        await client.query(message)
        asyncio.create_task(self._run_turn(client))
        return await self.outcomes.get()

    async def resume(self, result: dict) -> dict:
        if self.device is not None and not self.device.done():
            self.device.set_result(result)
        return await self.outcomes.get()

    async def close(self) -> None:
        if self.device is not None and not self.device.done():
            self.device.set_result({"error": "conversation closed"})
        if self.client is not None:
            await self.client.disconnect()
            self.client = None
