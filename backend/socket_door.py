"""
socket_door.py

The door to md2ui's WebSocket: the shop's own check before a socket opens.

md2ui authenticates no one (its protocol/backend.md): its socket, `wire_server.build_app`,
takes whatever check the backend already makes, at the upgrade request. The shop's is a
one-time ticket:

  1. The page asks the shop's own API for one (`POST /api/session`), same-origin. In a real
     shop that request carries the customer's session cookie and is checked like any other;
     here the demo has a single customer, and the ticket names the conversation.
  2. The page opens `/md2ui/ws?ticket=…` within TICKET_SECONDS. This door spends the ticket
     (it opens one socket, once) and hands the upgrade to that conversation's md2ui app,
     which checks the page's Origin against the shop's named origins.
  3. No ticket, an unknown one, a spent one or a late one: the socket is closed before it is
     accepted, which the browser sees as a 403.

A ticket rides in the URL because a browser's WebSocket can send no header of its own; it
is single-use and short-lived, so a URL in a log is worth nothing. A page on another site
cannot fetch one: `/api/session` is a JSON POST with no CORS, so its answer never reaches
that page's script.
"""

from __future__ import annotations

import secrets
import time
from collections.abc import Callable
from typing import Any, Optional
from urllib.parse import parse_qs

PATH = "/md2ui/ws"
TICKET_SECONDS = 30.0

Asgi = Callable[..., Any]


class Tickets:
    """One-time tickets, each naming the conversation its socket joins."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._open: dict[str, tuple[str, float]] = {}

    def issue(self, conversation_id: str) -> str:
        now = self._clock()
        self._open = {t: (c, at) for t, (c, at) in self._open.items() if now - at < TICKET_SECONDS}
        ticket = secrets.token_urlsafe(24)
        self._open[ticket] = (conversation_id, now)
        return ticket

    def redeem(self, ticket: str) -> Optional[str]:
        """The conversation *ticket* names, spending it; None when it never was, is spent,
        or is late."""
        found = self._open.pop(ticket, None)
        if found is None or self._clock() - found[1] >= TICKET_SECONDS:
            return None
        return found[0]


def door(tickets: Tickets, socket_for: Callable[[str], Optional[Asgi]]) -> Callable[[Asgi], Asgi]:
    """ASGI middleware (`app.add_middleware`): a WebSocket upgrade at PATH goes to the md2ui
    app of the conversation its ticket names (`socket_for`), as `/ws`; every other request
    goes on to the shop."""

    class Door:
        def __init__(self, app: Asgi) -> None:
            self.app = app

        async def __call__(self, scope: dict, receive: Asgi, send: Asgi) -> None:
            if scope["type"] != "websocket" or scope["path"] != PATH:
                await self.app(scope, receive, send)
                return
            query = parse_qs(scope.get("query_string", b"").decode())
            conversation = tickets.redeem(query.get("ticket", [""])[0])
            socket = socket_for(conversation) if conversation is not None else None
            if socket is None:
                await send({"type": "websocket.close", "code": 1008})  # before accept: HTTP 403
                return
            await socket(dict(scope, path="/ws", raw_path=b"/ws", query_string=b""), receive, send)

    return Door
