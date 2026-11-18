"""
home_writer.py

Writes the home page's own words, fast: the greeting band and the three product cards, and
the line of the orders section, as include lines that md2ui draws (pages.registry). It is a small
call beside the conversation, not a turn of it:

  - a short system prompt (these rules only, not md2ui's notes), no tools, low effort;
  - the home context in the message, so nothing is fetched first;
  - one session kept warm (the Claude Code runtime keeps its CLI process running), which
    also remembers its recent greetings so it does not repeat them.

The window shows the shop's instant home first (pages.instant_includes) and swaps in what
this writes when it is ready.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import tempfile
from collections import deque
from typing import Any

from md2ui.includes import INCLUDE_LINE

import tools

log = logging.getLogger("burger-shop.home")

MODEL = os.environ.get("HOME_MODEL", os.environ.get("CLAUDE_MODEL", "claude-opus-5-5"))
EFFORT = os.environ.get("HOME_EFFORT", "low")

SYSTEM = """You write the home page of the Burger Shop web app, fresh each time it is shown, for one signed-in customer. You get their home context as JSON and reply with exactly five include lines and nothing else: no prose, no code fence.

{{headline greeting="…" line="…" kicker="…" image=<product id> cta="…" action=<product action> cta2="…" action2=<product action>}}
{{offer product=<id> kicker="…" title="…" chip="…" cta="…"}}
{{offer product=<id> kicker="…" title="…" chip="…" cta="…"}}
{{offer promo=<id> kicker="…" title="…" chip="…" cta="…"}}
{{home-rest note="…"}}

Rules:
- The band and the three cards are about products only: what to eat, what is new, what is on offer. Never an order, its status, an order number or a reorder there. Actions are product?id=<id>, cart-add?id=<id>, offer?id=<promo id>, offers or catalog.
- greeting: warm and of the moment (part of the day, weekday), at most eight words, e.g. "Monday night, burger night?". The customer has no name here: never address them by one. line: one sentence about food, at most twenty words, true and specific: their usual, what is new, what is on offer. kicker: two to four words, or leave it out.
- image: the product the band is about. cta: what the band leads to, two to four words; cta2 an alternative.
- The three cards are three different reasons to tap: one of their usual products, something new for them (try_next or new_on_menu), and one live promotion. kicker two or three words, title at most five words, chip one true fact (a price, a label such as "✨ New", a deal, "Ordered 3 times"), cta one or two words. A product card's default action adds it to the cart; promotions open their offer.
- note: the orders section's line, a short nudge about their orders, at most eight words ("Same again for Friday night?"). With a running order you may mention it here, and only here.
- Only ids, names, prices and facts from the context. Never invent urgency or claims: no "tonight only", "last chance", end dates.
- Write in the context's words, new each time: never reuse a greeting, a line or a note from "Recently used"."""

NAMES = ("headline", "offer", "home-rest")


class HomeWriterError(Exception):
    """The writer gave no usable home: the window keeps the instant one."""


def check(text: str) -> str:
    """The reply's include lines, in order, if they are exactly the five a home needs."""
    lines = [l.strip() for l in text.strip().strip("`").splitlines() if l.strip()]
    found = [INCLUDE_LINE.match(l) for l in lines]
    if not lines or not all(found):
        raise HomeWriterError(f"not only include lines: {text[:200]!r}")
    names = [m.group("name") for m in found if m]
    if names != ["headline", "offer", "offer", "offer", "home-rest"]:
        raise HomeWriterError(f"wrong includes: {names}")
    return "\n\n".join([lines[0], "\n".join(lines[1:4]), lines[4]])


def _said(includes: str) -> list[str]:
    return re.findall(r'(?:greeting|line|note)="([^"]+)"', includes)


class HomeWriter:
    """One warm writer for the server: API calls, or one Claude Code session kept running."""

    def __init__(self, runtime: str, client: Any = None):
        self.runtime = runtime
        self.client = client  # anthropic.AsyncAnthropic, for the API runtime
        self.recent: deque[str] = deque(maxlen=12)
        self.lock = asyncio.Lock()
        self._cc: Any = None
        self._writes = 0

    def _message(self, context: dict) -> str:
        used = "\n".join(f"- {s}" for s in self.recent) or "- (none yet)"
        return f"Home context:\n{tools.dumps(context)}\n\nRecently used (do not reuse):\n{used}"

    async def write(self, context: dict) -> str:
        async with self.lock:
            text = await (self._write_cc(context) if self.runtime == "claude-code" else self._write_api(context))
            includes = check(text)
            self.recent.extend(_said(includes))
            return includes

    async def _write_api(self, context: dict) -> str:
        response = await self.client.beta.messages.create(
            model=MODEL,
            max_tokens=4000,
            system=SYSTEM,
            messages=[{"role": "user", "content": self._message(context)}],
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": EFFORT},
        )
        if response.stop_reason == "refusal":
            raise HomeWriterError("refused")
        return "".join(b.text for b in response.content if b.type == "text")

    # --- the Claude Code runtime (dev only): one session kept warm -----------------
    async def warm(self) -> None:
        if self.runtime == "claude-code":
            await self._connect()

    async def _connect(self):
        if self._cc is None or self._writes >= 25:  # a fresh session now and then keeps it small
            await self.close()
            from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

            self._cc = ClaudeSDKClient(ClaudeAgentOptions(
                system_prompt=SYSTEM, model=MODEL, effort=EFFORT, tools=[], setting_sources=[],
                cwd=tempfile.mkdtemp(prefix="burger-home-"), max_turns=1,
            ))
            await self._cc.connect()
            self._writes = 0
        return self._cc

    async def _write_cc(self, context: dict) -> str:
        from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock

        client = await self._connect()
        self._writes += 1
        await client.query(self._message(context))
        text: list[str] = []
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                text += [b.text for b in message.content if isinstance(b, TextBlock)]
            elif isinstance(message, ResultMessage):
                if message.is_error:
                    raise HomeWriterError(message.result or message.subtype)
                break
        return "".join(text)

    async def close(self) -> None:
        if self._cc is not None:
            try:
                await self._cc.disconnect()
            except Exception as e:  # the CLI may already be gone
                log.warning("home writer disconnect: %s", e)
            self._cc = None
