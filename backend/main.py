"""
main.py

Burger Shop backend:

    web app (Vite)  ==md2ui's WebSocket==>  this backend  -->  Claude API (tools: tools.py)
    Flutter app's       --HTTP /api-->         │
      embed page                               ├──> Shop (shop.py, mock services from data/)
       │ <md2ui-view>                          └──> md2ui's Conversation, one per conversation
       │ header / footer / payment window or sheet

Each conversation is md2ui's own `Conversation` (wire_server): it draws the shop's includes
(pages.registry), keeps the pages it sent, verifies every tap against the page it was made
on and words it for the agent. Its handlers answer, with no agent turn, a tap on ➕ ➖ 🤍 ❤️
(the shop changes, md2ui redraws the includes named, ADR-612) and a tap that only chooses a
page, a category tab, View cart, My orders (md2ui shows that page of includes, ADR-614).
md2ui keeps a line of its digest for each, handed to the agent with its next input.
A running order on the page shown moves by md2ui's feeds, which the shop opens and posts to,
and the rest of what the page draws of it by md2ui's redraw of its includes, which the shop
asks for as the order moves (order_feeds.py), with no agent turn either; a payment in the
app's own window redraws the page shown the same way.

How the apps reach it, both the same way:

  The socket    - md2ui's socket (`wire_server.build_app`), behind the shop's one-time
                  ticket (socket_door.py, `/api/session`): the web page opens it, and so
                  does the Flutter app's embed page, with a ticket the app asks for. Every
                  other tap and the prompt bar arrive on the conversation's queue; `listen`
                  hands each to the agent and sends its page back over the socket.
  HTTP          - `/api/home` and `/api/home/fresh`, the native chrome's pages (`/api/nav`),
                  the payment window (`/api/checkout*`, `/api/resume`) and `/api/state`.

Checkout stays the app's: the page's Checkout (`agent:checkout`) is caught by the app, which
opens its own payment session; the agent's `open_checkout` pauses its turn until the app's
window closes and calls `/api/resume`.

Run with:
    export ANTHROPIC_API_KEY=sk-ant-...
    uvicorn main:app --port 8000
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Literal, Optional

import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from md2ui import session as md2ui_session
from md2ui import theme_lint, wire_server
from md2ui.advice import Reading, reply_issues
from md2ui.includes import INCLUDE_LINE
from md2ui.wire import Prompt, Verified
from md2ui.wire_includes import Show
from pydantic import BaseModel, Field
from starlette.applications import Starlette

import home_writer
import order_feeds
import pages
import socket_door
import tools
from shop import STAGE_SECONDS, Shop, ShopError, money

log = logging.getLogger("burger-shop")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
EFFORT = os.environ.get("CLAUDE_EFFORT", "medium")
# "api" (default): the Messages API with ANTHROPIC_API_KEY. "claude-code": DEV ONLY,
# the local Claude Code login through the Agent SDK (claude_code_runtime.py).
RUNTIME = os.environ.get("AGENT_RUNTIME", "api")
BETAS = ["server-side-fallback-2026-07-01"]  # fallbacks="default" on refusals
THEME_DIR = Path(__file__).with_name("md2ui_theme")
# The pages that may open md2ui's socket, by exact origin (md2ui refuses any other browser
# page, a localhost one included): the web app's dev server, the Flutter app's embed page
# (its web view loads it from the app's own page server, app/lib/md2ui/server.dart, on
# every platform), and the shop's real origin.
EMBED_ORIGIN = "http://localhost:8787"
ALLOWED_ORIGINS = [o for o in os.environ.get("ALLOWED_ORIGINS", f"http://localhost:5173,{EMBED_ORIGIN}").split(",") if o]


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
@dataclass
class PendingAction:
    tool_use_id: str
    tool_name: str
    tool_input: dict
    client_input: dict  # what the app needs, e.g. the checkout session
    ready_results: list[dict]  # results for the turn's other tool calls


@dataclass
class Page:
    message_id: str
    markdown: str


@dataclass
class Conversation:
    # md2ui's conversation: the pages sent, the includes they drew, the taps it answers.
    md: wire_server.Conversation = field(default_factory=lambda: served())
    # What md2ui's advice has told this conversation's agent, so it is told once.
    reading: Reading = field(default_factory=Reading)
    messages: list[dict] = field(default_factory=list)
    pending: Optional[PendingAction] = None
    # md2ui's socket over `md` (built with the first ticket), and the task that hands what
    # arrives on it to the agent.
    socket: Optional[Starlette] = None
    listener: Optional[asyncio.Task] = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    claude_code: Any = None  # the Claude Code session, with AGENT_RUNTIME=claude-code
    # Bumped by every agent turn: a fresh home written for an older token is not swapped in,
    # since the customer has moved on.
    home_token: int = 0
    # The session's home page, written once (by the home writer, or by the agent when it
    # writes a home) and shown again on every Home: its include lines, and what it was
    # written for (the part of the day, and the running order and its status).
    saved_home: Optional[str] = None
    saved_for: Optional[dict] = None
    home_page: Optional[str] = None  # the instant home's message, which the fresh one replaces
    agent_page: bool = False  # the page on screen is the agent's reply: md2ui's issues are its

    @property
    def page(self) -> Optional[Page]:
        """The page on screen: the latest md2ui sent, as it sent it."""
        latest = self.md.latest
        return Page(latest, self.md.log.markdown(latest)) if latest else None


class AppNotes:
    """What the customer did in the app since the agent last heard: told once, at the
    start of the next turn. The taps md2ui answered come as its own digest lines
    (`take_handled`), then the cart as it is now; what md2ui does not see (the footer's
    payments, the home page shown) is the shop's own line."""

    def __init__(self) -> None:
        self.events: list[str] = []
        self.home: Optional[str] = None  # the include lines of the home page on screen, latest only

    def take(self, shop: Shop, handled: list[str], issues: list[str]) -> str:
        lines = [f"- {h}" for h in handled] + [f"- {e}" for e in self.events]
        if handled:
            c = tools.cart_summary(shop)
            items = ", ".join(f"{i['quantity']} × {i['name']}" + (f" ({i['size']})" if "size" in i else "")
                              for i in c["items"]) or "empty"
            lines.append(f"- Cart now: {items}; {c['item_count']} items, total {c['total']}.")
        if self.home:
            lines.append(f"- The window shows the home page, written as:\n{self.home}")
        lines += [f"- md2ui on your last page: {i}" for i in issues]
        self.__init__()
        return "[App notes]\n" + "\n".join(lines) if lines else ""


CONVERSATIONS: dict[str, Conversation] = {}
NOTES = AppNotes()
shop = Shop()
AGENT_SESSIONS: set[str] = set()  # checkout sessions opened by the agent's open_checkout
TICKETS = socket_door.Tickets()
claude: Optional[anthropic.AsyncAnthropic] = None
writer: Optional[home_writer.HomeWriter] = None
_KIT: Optional[md2ui_session.GroupingKit] = None
CONTRACT = theme_lint.answer_contract(THEME_DIR / "THEME.md")


def kit() -> md2ui_session.GroupingKit:
    """md2ui's grouping kit, loaded once for every conversation."""
    global _KIT
    _KIT = _KIT or md2ui_session.load_grouping_kit()
    return _KIT


def served() -> wire_server.Conversation:
    """md2ui's conversation for one of the shop's: the shop's includes, drawn from the shop
    as it is when drawn, and its handlers: ➕ ➖ 🤍 ❤️ change the shop, and the taps that only
    choose a page show it. A running order on the page shown moves by md2ui's feeds
    (order_feeds.py)."""
    md = order_feeds.ShopConversation(shop, kit(), prefix=f"m{uuid.uuid4().hex[:6]}-", includes=pages.registry(shop))
    md.handlers.update({"cart-add": cart_handler(1), "cart-remove": cart_handler(-1),
                        "like": like_handler(True), "unlike": like_handler(False),
                        "catalog": catalog_handler, "cart": page_handler("{{cart}}"),
                        "orders": page_handler("{{orders}}")})
    return md


def cart_handler(delta: int):
    """➕ (`agent:cart-add?id=…&size=…`) or ➖: one cart line changes (the product at its
    `size`, or its default size when it names none), and every include that draws a cart
    line is drawn again."""
    def handle(params: dict[str, str]) -> frozenset[str]:
        shop.add(params["id"], delta, {"size": params["size"]} if params.get("size") else None)
        return pages.DRAWS_CART
    return handle


def like_handler(liked: bool):
    """🤍 (`agent:like?id=…`) or ❤️: the like changes, and every include that draws a heart."""
    def handle(params: dict[str, str]) -> frozenset[str]:
        shop.set_like(params["id"], liked)
        return pages.DRAWS_LIKES
    return handle


# The catalog filters a tap may carry that the shop's own menu page answers, each with the
# values it takes; a tap with any other (`filter=spicy`) is the agent's.
MENU_TAPS = {"category": re.compile("|".join(pages.CATEGORY_TAG)), "sort": re.compile("popular|rating|price"),
             "max_price": re.compile(r"\d{1,3}"), "page": re.compile(r"\d{1,2}")}


def catalog_handler(params: dict[str, str]) -> Optional[Show]:
    """A category tab, Keep shopping, Best sellers, Under $10, Show more
    (`agent:catalog?category=sides`): the menu page, shown by md2ui with no agent turn."""
    if any(k not in MENU_TAPS or not MENU_TAPS[k].fullmatch(v) for k, v in params.items()):
        return None
    return Show("{{" + " ".join(["menu", *(f"{k}={v}" for k, v in params.items())]) + "}}")


def page_handler(page: str):
    """A tap that only chooses one of the shop's pages (View cart: `agent:cart`)."""
    return lambda params: None if params else Show(page)


@asynccontextmanager
async def lifespan(_: FastAPI):
    global claude, writer
    if RUNTIME == "claude-code":
        log.warning("AGENT_RUNTIME=claude-code: dev only, runs on the local Claude Code login")
    else:
        claude = anthropic.AsyncAnthropic()
    writer = home_writer.HomeWriter(RUNTIME, claude)
    warming = asyncio.create_task(writer.warm())  # the home writer's session starts now, not on the first visit
    if os.environ.get("DEMO_SEED_ORDER") == "1":
        seed_order()
    yield
    warming.cancel()
    await writer.close()
    for conv in CONVERSATIONS.values():
        if conv.listener is not None:
            conv.listener.cancel()
        if conv.claude_code is not None:
            await conv.claude_code.close()


app = FastAPI(title="Burger Shop agent", lifespan=lifespan)


def seed_order() -> None:
    """A paid order already on its way, so the home page shows its tracking card."""
    shop.set_qty("classic-smash", 2)
    shop.set_qty("crispy-fries", 1)
    s = shop.create_checkout()
    shop.pay(s.id, "4242 4242 4242 4242", "12/30", "123")
    shop.orders[s.order_id].placed_at -= 1.2 * STAGE_SECONDS  # just into "preparing": it can still be cancelled


# ---------------------------------------------------------------------------
# Pages: what the window shows, sent through md2ui, which draws the includes
# ---------------------------------------------------------------------------
async def show(conv: Conversation, markdown: str, replaces: Optional[str] = None) -> Page:
    await conv.md.send(pages.prepare(markdown), replaces=replaces)
    page = conv.page
    assert page is not None
    return page


async def show_reply(conv: Conversation, text: str) -> None:
    """The agent's reply as the page; md2ui's issues with it go to the agent's next turn."""
    if not text.strip():
        return
    if "{{home-saved}}" in text:  # the session's saved home, or the instant one if none fits
        text = text.replace("{{home-saved}}", saved_home(conv) or pages.instant_includes(shop))
    if not pages.draw(shop, text)[1]:
        save_home(conv, text)
    await show(conv, text)


def issues(conv: Conversation) -> list[str]:
    """md2ui's issues with the page on screen, as its own send tool would return them to the
    agent (protocol/backend.md): the errors and warnings, and advice once per section. The
    includes it drew and the taps the shop's handlers answer are named, so neither is
    advised against."""
    mid = conv.md.latest
    if mid is None:
        return []
    markdown = conv.md.log.markdown(mid)
    found = reply_issues(markdown, md2ui_session.group_markdown(markdown, kit()), CONTRACT, conv.reading,
                         includes=conv.md.includes, regions=conv.md.log.pages.includes.regions(mid),
                         handled=conv.md.handlers)
    return [f"{i['level']} ({i['code']}): {i['message']}" for i in found
            if i["level"] in ("error", "warning") or i["code"] == "advice"]


# ---------------------------------------------------------------------------
# The saved home: written once a session, shown again on every Home
# ---------------------------------------------------------------------------
def written_for(ctx: dict) -> dict:
    running = ctx["running_order"]
    return {"part_of_day": ctx["now"]["part_of_day"],
            "order": (running["order_id"], running["status"]) if running else None}


def save_home(conv: Conversation, text: str) -> None:
    """An agent reply that is a whole home (a band and the rest) becomes the session's saved home."""
    found = [m for l in text.splitlines() if (m := INCLUDE_LINE.match(l.strip()))]
    lines, names = [m.group(0) for m in found], [m.group("name") for m in found]
    if "headline" in names and "home-rest" in names:
        conv.saved_home, conv.saved_for = "\n".join(lines), written_for(shop.home_context())


def saved_home(conv: Conversation) -> Optional[str]:
    """The saved home's include lines if they still fit: none once the part of the day has
    changed (a "Good morning" in the evening). The orders line is dropped, and the section's
    own line shown, once the order it may speak of has moved on."""
    if conv.saved_home is None or conv.saved_for is None:
        return None
    now = written_for(shop.home_context())
    if now["part_of_day"] != conv.saved_for["part_of_day"]:
        return None
    includes = conv.saved_home
    if now["order"] != conv.saved_for["order"]:
        includes = re.sub(r'\s+note="[^"]*"', "", includes)
    return includes


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------
def tool_result(tool_use_id: str, content: Any, is_error: bool = False) -> dict:
    block = {"type": "tool_result", "tool_use_id": tool_use_id,
             "content": content if isinstance(content, str) else tools.dumps(content)}
    if is_error:
        block["is_error"] = True
    return block


async def run_agent_loop(conv: Conversation) -> dict:
    assert claude is not None
    all_tools = tools.BACKEND_TOOLS_SCHEMA + tools.CLIENT_TOOLS_SCHEMA
    while True:
        response = await claude.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=tools.system_prompt(date.today()),
            messages=conv.messages,
            tools=all_tools,
            betas=BETAS,
            fallbacks="default",
            output_config={"effort": EFFORT},
            cache_control={"type": "ephemeral"},
        )
        # Append the SDK blocks as they are (thinking and fallback blocks included):
        # history is append-only and never re-serialized through the client.
        conv.messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "pause_turn":
            continue
        if response.stop_reason != "tool_use":
            text = "".join(b.text for b in response.content if b.type == "text")
            if response.stop_reason == "refusal" and not text:
                text = "Sorry, I can't help with that. Is there anything on the menu I can get you?"
            return {"reply": text}

        results: list[dict] = []
        pending: Optional[PendingAction] = None
        for block in response.content:
            if block.type != "tool_use":
                continue
            log.info("tool_use %s", block.name)
            if block.name in tools.CLIENT_TOOL_NAMES:
                if pending is not None:
                    results.append(tool_result(block.id, {"error": "Only one payment window at a time."}, True))
                    continue
                client_input, error = tools.start_client_call(shop, block.name, dict(block.input))
                if error:
                    results.append(tool_result(block.id, {"error": error}, is_error=True))
                else:
                    pending = PendingAction(block.id, block.name, dict(block.input), client_input or {}, [])
                    AGENT_SESSIONS.add(pending.client_input.get("session_id", ""))
            else:
                results.append(tool_result(block.id, await tools.call_backend_tool(shop, block.name, block.input)))

        if pending:
            pending.ready_results = results
            conv.pending = pending
            return {"pending": pending}
        conv.messages.append({"role": "user", "content": results})


async def drive(conv: Conversation) -> dict:
    """Runs the loop, rolling history back if the Claude call fails so the request can
    be retried cleanly."""
    snapshot_len, snapshot_pending = len(conv.messages), conv.pending
    try:
        return await run_agent_loop(conv)
    except anthropic.APIStatusError as e:
        del conv.messages[snapshot_len:]
        conv.pending = snapshot_pending
        raise HTTPException(status_code=502, detail=f"Claude API error ({e.status_code}): {e.message}")
    except anthropic.APIConnectionError:
        del conv.messages[snapshot_len:]
        conv.pending = snapshot_pending
        raise HTTPException(status_code=502, detail="Could not reach the Claude API")


# ---------------------------------------------------------------------------
# A turn: what the customer said or did, the agent's answer, its page
# ---------------------------------------------------------------------------
HOME_ASKED = re.compile(r"\bhome\b", re.I)


def user_turn(conv: Conversation, said: str, shown_by_agent: bool) -> str:
    """The agent's next input: the app notes (md2ui's digest of the taps it answered, the
    shop's own lines, md2ui's issues with the agent's last page), the home context when home
    is asked for, then *said*: md2ui's sentence for a tap, or the customer's own words."""
    notes = NOTES.take(shop, conv.md.take_handled(), issues(conv) if shown_by_agent else [])
    if HOME_ASKED.search(said):  # written fresh from the shop's context, with no tool round trip
        home = "[Home context]\n" + tools.dumps(shop.home_context())
        notes = f"{notes}\n\n{home}" if notes else home
    return f"{notes}\n\n{said}" if notes else said


async def turn(conv: Conversation, said: str) -> None:
    """One agent turn, under the conversation's lock; its page is sent through md2ui. A turn
    that opens the payment window leaves it pending and shows the order review behind it."""
    conv.home_token += 1  # an agent turn: a fresh home on its way is no longer wanted
    content = user_turn(conv, said, conv.agent_page)
    if RUNTIME == "claude-code":
        from claude_code_runtime import ClaudeCodeConversation

        conv.claude_code = conv.claude_code or ClaudeCodeConversation(shop)
        outcome = await claude_code_outcome(conv, conv.claude_code.turn(content))
    else:
        conv.messages.append({"role": "user", "content": content})
        try:
            outcome = await drive(conv)
        except HTTPException:
            if conv.messages and conv.messages[-1] == {"role": "user", "content": content}:
                conv.messages.pop()
            raise
    await answer(conv, outcome)


async def answer(conv: Conversation, outcome: dict) -> None:
    if outcome.get("pending") is not None:
        await show(conv, "{{checkout}}")  # behind the payment window: the order review
    elif outcome.get("reply", "").strip():
        await show_reply(conv, outcome["reply"])
        conv.agent_page = True


async def settle(conv: Conversation, event: Optional[Verified] = None) -> None:
    """md2ui's state for the window: listening again, releasing the tap answered; or working
    while the agent's turn waits for the payment window."""
    if conv.pending is not None:
        await conv.md.set_state("w", note="Waiting for the payment window")
    else:
        await conv.md.set_state("l", answered={event.peer: [event.seq]} if event is not None else None)


async def listen(conv: Conversation) -> None:
    """The conversation on md2ui's socket: each tap md2ui verified and did not answer itself, and each
    message typed in the prompt bar, handed to the agent in turn; its page goes back over
    md2ui's socket. A window closing or coming back is md2ui's to handle."""
    await settle(conv)
    while True:
        event = await conv.md.events.get()
        if not isinstance(event, (Verified, Prompt)):
            continue
        await conv.md.set_state("w")
        try:
            async with conv.lock:
                if conv.pending is None:  # the window blocks taps while the payment window is open
                    await turn(conv, event.agent_text() if isinstance(event, Verified) else event.text)
        except Exception:  # the agent's failure: the button is released, the page stays
            log.exception("turn failed")
        await settle(conv, event if isinstance(event, Verified) else None)


# ---------------------------------------------------------------------------
# API models
# ---------------------------------------------------------------------------
class SessionRequest(BaseModel):
    conversation_id: Optional[str] = None


class SessionResponse(BaseModel):
    conversation_id: str
    ticket: str  # one socket, once, within socket_door.TICKET_SECONDS


class ResumeRequest(BaseModel):
    conversation_id: str
    tool_use_id: str


class PendingOut(BaseModel):
    tool_use_id: str
    tool_name: str
    checkout: dict


def cart_badge() -> dict:
    c = shop.cart_view()
    return {"item_count": c["item_count"], "total": c["total"], "total_label": money(c["total"]),
            "subtotal": c["subtotal"], "delivery": c["delivery"]}


def pending_out(conv: Conversation) -> Optional[PendingOut]:
    p = conv.pending
    return PendingOut(tool_use_id=p.tool_use_id, tool_name=p.tool_name, checkout=p.client_input) if p else None


def get_conversation(conversation_id: str) -> Conversation:
    conv = CONVERSATIONS.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="unknown conversation")
    return conv


# ---------------------------------------------------------------------------
# md2ui's socket, for both apps
# ---------------------------------------------------------------------------
@app.post("/api/session", response_model=SessionResponse)
async def open_session(req: SessionRequest):
    """A one-time ticket for md2ui's socket (socket_door.py), and the conversation it joins:
    the one named, or a new one. The conversation's agent listens from now on."""
    conversation_id = req.conversation_id if req.conversation_id in CONVERSATIONS else f"conv_{uuid.uuid4().hex[:12]}"
    conv = CONVERSATIONS.setdefault(conversation_id, Conversation())
    conv.socket = conv.socket or wire_server.build_app(conv.md, allowed_origins=ALLOWED_ORIGINS)
    conv.listener = conv.listener or asyncio.create_task(listen(conv))
    return SessionResponse(conversation_id=conversation_id, ticket=TICKETS.issue(conversation_id))


def socket_for(conversation_id: str) -> Optional[Starlette]:
    conv = CONVERSATIONS.get(conversation_id)
    return conv.socket if conv is not None else None


app.add_middleware(socket_door.door(TICKETS, socket_for))


# ---------------------------------------------------------------------------
# The agent's payment window: its turn waits until the app's window closes
# ---------------------------------------------------------------------------
@app.post("/api/resume", status_code=204)
async def resume(req: ResumeRequest) -> None:
    """Called by the app once the payment window closes. Carries no outcome: the tool
    result is built from the checkout session on the server. The agent's page goes out over
    md2ui's socket."""
    conv = get_conversation(req.conversation_id)
    async with conv.lock:
        pending = conv.pending
        if not pending or pending.tool_use_id != req.tool_use_id:
            raise HTTPException(status_code=409, detail="no matching pending action")
        result = tools.resolve_client_result(shop, pending.tool_name, pending.client_input)
        conv.pending = None
        try:
            if conv.claude_code is not None:
                await answer(conv, await claude_code_outcome(conv, conv.claude_code.resume(result)))
            else:
                snapshot_len = len(conv.messages)
                conv.messages.append({"role": "user", "content": pending.ready_results + [tool_result(pending.tool_use_id, result)]})
                try:
                    await answer(conv, await drive(conv))
                except HTTPException:
                    del conv.messages[snapshot_len:]
                    conv.pending = pending
                    raise
        finally:
            await settle(conv)


async def claude_code_outcome(conv: Conversation, turn: Any) -> dict:
    """Maps a Claude Code turn onto the outcome the API runtime gives."""
    result = await turn
    if "error" in result:
        raise HTTPException(status_code=502, detail=str(result["error"]))
    pending = result.get("pending")
    if pending is not None:
        conv.pending = PendingAction(pending.tool_use_id, pending.tool_name, {}, pending.client_input, [])
        AGENT_SESSIONS.add(pending.client_input.get("session_id", ""))
        return {"pending": conv.pending}
    return {"reply": result.get("reply", "")}


# ---------------------------------------------------------------------------
# The native chrome's pages: no agent turn
# ---------------------------------------------------------------------------
# The header's My orders, the footer's View cart, and the order confirmation after the app's
# own payment window: buttons of the app, not of the page, so md2ui's handlers never see
# them. The shop shows the page itself and the agent hears it in its notes.
NAV = {"cart": "{{cart}}", "orders": "{{orders}}", "success": "{{success}}"}


class NavRequest(BaseModel):
    conversation_id: str
    to: Literal["cart", "orders", "success"]


@app.post("/api/nav", status_code=204)
async def nav(req: NavRequest) -> None:
    conv = get_conversation(req.conversation_id)
    async with conv.lock:
        if conv.pending:
            raise HTTPException(status_code=409, detail="the payment window is open; call /api/resume first")
        await show(conv, NAV[req.to])
        conv.agent_page = False
        NOTES.events.append(f"The app showed `{NAV[req.to]}` from its own {req.to} button, with no turn of yours.")


# ---------------------------------------------------------------------------
# The home page, fast: the instant one at once, then the fresh one
# ---------------------------------------------------------------------------
class HomeRequest(BaseModel):
    conversation_id: Optional[str] = None


class HomeResponse(BaseModel):
    """The page itself goes out over md2ui's socket."""
    conversation_id: str
    token: int
    cart: dict
    fresh: bool = False  # /api/home: true when the window should ask for a fresh one


@app.post("/api/home", response_model=HomeResponse)
async def home(req: HomeRequest):
    """The home page in the shop's own words, personalised from live data, at once: the
    first visit and every Home tap. The window then asks for the fresh one."""
    conversation_id = req.conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
    conv = CONVERSATIONS.setdefault(conversation_id, Conversation())
    conv.home_token += 1
    saved = saved_home(conv)
    fresh = saved is None or bool(pages.draw(shop, saved)[1])
    if saved is None or fresh:  # nothing saved yet this session, or it no longer fits: the instant home, then a fresh one
        saved = pages.instant_includes(shop)
    else:
        NOTES.home = saved
    conv.home_page, conv.agent_page = (await show(conv, saved)).message_id, False
    return HomeResponse(conversation_id=conversation_id, token=conv.home_token, cart=cart_badge(), fresh=fresh)


class FreshHomeRequest(BaseModel):
    conversation_id: str
    token: int


@app.post("/api/home/fresh", response_model=HomeResponse)
async def fresh_home(req: FreshHomeRequest):
    """The home page in new words, written by the home writer beside the conversation.
    Swapped in, in place of the instant one, only if nothing happened since but taps on
    ➕ ➖ 🤍 ❤️: no agent turn, and no other page shown (a category tab, View cart)."""
    conv = get_conversation(req.conversation_id)
    assert writer is not None
    try:
        includes = await writer.write(shop.home_context())
        failed = pages.draw(shop, includes)[1]
        if failed:
            raise home_writer.HomeWriterError("; ".join(failed))
    except Exception as e:  # any failure keeps the instant home, which is already right
        log.warning("fresh home not written: %s", e)
        return HomeResponse(conversation_id=req.conversation_id, token=conv.home_token, cart=cart_badge())
    shown = conv.md.latest
    if conv.home_token != req.token or conv.home_page is None or conv.md.log.head(conv.home_page) != shown:
        return HomeResponse(conversation_id=req.conversation_id, token=conv.home_token, cart=cart_badge())
    await show(conv, includes, replaces=shown)
    conv.saved_home, conv.saved_for = includes, written_for(shop.home_context())
    # The conversation's agent hears what the window shows, so "the first card" means something.
    NOTES.home = includes
    return HomeResponse(conversation_id=req.conversation_id, token=conv.home_token, cart=cart_badge())


# ---------------------------------------------------------------------------
# App endpoints: no agent turn
# ---------------------------------------------------------------------------
@app.get("/api/state")
async def state(conversation_id: Optional[str] = None):
    """The footer's badge, read after every page; and the agent's payment window, when its
    turn waits on one (the web app opens it from here)."""
    running = shop.running_order()
    conv = CONVERSATIONS.get(conversation_id or "")
    return {"cart": cart_badge(), "likes": sorted(shop.likes),
            "running_order": tools.order_summary(shop, running.id) if running else None,
            "pending_action": pending_out(conv) if conv is not None else None}


@app.post("/api/checkout")
async def open_checkout_from_footer():
    """The footer's Checkout button, or the page's (caught by the web app): a payment session
    without an agent turn. Paid, the app shows the confirmation (`/api/nav`)."""
    try:
        return tools.checkout_view(shop.create_checkout())
    except ShopError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.get("/api/checkout/{session_id}")
async def get_checkout(session_id: str):
    try:
        return tools.checkout_view(shop.session(session_id))
    except ShopError as e:
        raise HTTPException(status_code=404, detail=str(e))


class PayRequest(BaseModel):
    """The sandbox card form. The card number never leaves this request: the shop keeps
    only its brand and last four digits, and nothing of it reaches the agent."""
    card_number: str = Field(min_length=12, max_length=23)
    expiry: str = Field(max_length=7)
    cvc: str = Field(max_length=4)
    name: str = Field(default="", max_length=80)


@app.post("/api/checkout/{session_id}/pay")
async def pay(session_id: str, body: PayRequest):
    try:
        s = shop.pay(session_id, body.card_number, body.expiry, body.cvc, body.name)
    except ShopError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if s.status == "paid" and session_id not in AGENT_SESSIONS:
        o = tools.order_summary(shop, s.order_id)
        NOTES.events.append(f"The customer paid in the app's own payment window: order {o['order_id']}, "
                            f"{o['total']}, {o['card']}.")
    if s.status == "paid":  # the cart emptied and an order began with no tap: the page shown is redrawn
        for conv in list(CONVERSATIONS.values()):
            await conv.md.changed(pages.DRAWS_CART | pages.DRAWS_ORDERS)
    if s.status == "failed" and session_id not in AGENT_SESSIONS:
        NOTES.events.append(f"The customer tried to pay in the app's own payment window and the card was "
                            f"declined ({s.error}); nothing was charged and the cart is unchanged.")
    view = tools.checkout_view(s)
    view["cart"] = cart_badge()
    return view


@app.post("/api/checkout/{session_id}/cancel")
async def cancel_checkout(session_id: str):
    try:
        return tools.checkout_view(shop.cancel_checkout(session_id))
    except ShopError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------------------------------------------------------------------------
# The theme the window draws with: THEME.md and its fonts (the meanings and patterns
# stay on the server, in the agent's prompt)
# ---------------------------------------------------------------------------
@app.get("/theme/THEME.md")
async def theme_file():
    return FileResponse(THEME_DIR / "THEME.md", media_type="text/markdown")


app.mount("/theme/assets", StaticFiles(directory=THEME_DIR / "assets"), name="theme-assets")


@app.get("/api/health")
async def health():
    return {"status": "ok", "runtime": RUNTIME, "model": MODEL}
