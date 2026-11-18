"""Both apps' way in: md2ui's WebSocket behind the shop's one-time ticket, opened by the web
page and by the Flutter app's embed page, with a scripted stand-in for Claude. Frames are
md2ui's wire (its protocol/README.md); either page's view sends the same ones through
md2ui-ts's wire client."""

import json

from starlette.websockets import WebSocketDisconnect

import main
import socket_door
from test_api import reply, script, target, text, window

ORIGIN = {"origin": "http://localhost:5173"}


def ticket(api, cid=None) -> tuple[str, str]:
    r = api.post("/api/session", json={"conversation_id": cid}).json()
    return r["conversation_id"], r["ticket"]


def until(ws, t: str, **keys) -> list[dict]:
    """Every frame read up to and including the first of type *t* with *keys*."""
    read = []
    while True:
        frame = json.loads(ws.receive_text())
        read.append(frame)
        if frame["t"] == t and all(frame.get(k) == v for k, v in keys.items()):
            return read


def connect(api, t: str, headers=ORIGIN):
    ws = api.websocket_connect(f"{socket_door.PATH}?ticket={t}", headers=headers)
    return ws


def refused(api, path: str, headers=ORIGIN) -> bool:
    try:
        with api.websocket_connect(path, headers=headers) as ws:
            ws.send_text('{"t":"h","v":1}')
            ws.receive_text()
    except WebSocketDisconnect as e:
        return e.code == 1008
    return False


# --- the door ---------------------------------------------------------------------------
def test_the_socket_opens_only_with_a_fresh_ticket_from_a_named_origin(api):
    cid, t = ticket(api)
    assert refused(api, socket_door.PATH)  # no ticket
    assert refused(api, f"{socket_door.PATH}?ticket=made-up")
    with connect(api, t) as ws:  # the ticket opens one socket...
        ws.send_text('{"t":"h","v":1}')
        assert until(ws, "s")[-1]["s"] == "l"  # the agent listens
    assert refused(api, f"{socket_door.PATH}?ticket={t}")  # ...once
    _, t2 = ticket(api, cid)
    assert refused(api, f"{socket_door.PATH}?ticket={t2}", headers={"origin": "https://evil.example"})


def test_a_ticket_is_spent_late_or_once():
    now = [0.0]
    tickets = socket_door.Tickets(clock=lambda: now[0])
    a, b = tickets.issue("conv_a"), tickets.issue("conv_b")
    assert tickets.redeem(a) == "conv_a" and tickets.redeem(a) is None
    now[0] = socket_door.TICKET_SECONDS
    assert tickets.redeem(b) is None


def test_a_session_keeps_its_conversation(api):
    cid, _ = ticket(api)
    assert ticket(api, cid)[0] == cid
    assert ticket(api, "conv_from_a_restart")[0] != "conv_from_a_restart"  # an unknown one is new


# --- the conversation over the socket ------------------------------------------------------
def test_taps_and_prompts_over_the_socket(api, monkeypatch):
    fake = script(monkeypatch, reply(text("Spicy ones:\n\n{{menu spicy=true}}")))
    cid, t = ticket(api)
    with connect(api, t) as ws:
        ws.send_text('{"t":"h","v":1}')
        until(ws, "s", s="l")
        api.post("/api/home", json={"conversation_id": cid})
        home = until(ws, "z")[0]
        assert home["t"] == "m" and home["md"].startswith("# {#headline-1}")

        # ➕ on a card: md2ui's handler changes the cart and redraws the page in place.
        m, x = target(cid, "cart-add")
        ws.send_text(json.dumps({"t": "e", "m": m, "x": x, "q": 1, "a": "cart-add"}))
        frames = until(ws, "s")
        assert frames[0]["t"] == "m" and frames[0]["r"] == m and frames[-1]["u"] == [1]
        assert main.shop.cart != {}

        # 🍟 Sides: md2ui's handler shows the menu as a new page, with no agent turn.
        m, x = target(cid, "catalog", category="sides")
        ws.send_text(json.dumps({"t": "e", "m": m, "x": x, "q": 2, "a": "catalog"}))
        frames = until(ws, "s")
        assert "r" not in frames[0] and frames[0]["md"].startswith("# Sides") and frames[-1]["u"] == [2]
        assert fake.requests == []

        # A prompt: the agent's turn, its page over the socket.
        ws.send_text(json.dumps({"t": "p", "q": 3, "tx": "anything spicy?"}))
        frames = until(ws, "s", s="l")
        assert [f["t"] for f in frames] == ["s", "m", "z", "s"] and frames[0]["s"] == "w"
        assert frames[1]["md"].startswith("Spicy ones:")
        sent = fake.requests[0]["messages"][-1]["content"]
        assert sent.startswith("[App notes]\n- User chose") and sent.endswith("anything spicy?")
        assert "the backend showed {{menu category=sides}}" in sent


# --- the Flutter app's embed page ----------------------------------------------------------
EMBED = {"origin": main.EMBED_ORIGIN}


def test_the_embed_page_opens_the_socket_from_its_own_origin(api):
    """The app's web view loads the embed page from the app's page server on localhost, and
    its socket carries that origin; the app asks the shop for the ticket and hands it over."""
    assert main.EMBED_ORIGIN in main.ALLOWED_ORIGINS
    cid, t = ticket(api)
    assert refused(api, socket_door.PATH, headers=EMBED)  # the origin alone opens nothing
    with connect(api, t, headers=EMBED) as ws:
        ws.send_text('{"t":"h","v":1}')
        assert until(ws, "s")[-1]["s"] == "l"
    _, t2 = ticket(api, cid)
    assert refused(api, f"{socket_door.PATH}?ticket={t2}", headers={"origin": "http://localhost:8788"})  # another local page


def test_the_embed_page_reconnects_to_its_page(api, monkeypatch):
    """A dropped socket comes back with a fresh ticket for the same conversation, and md2ui
    sends the page shown again: the embed keeps no page of its own."""
    script(monkeypatch, reply(text("{{cart}}")))
    with window(api, origin=main.EMBED_ORIGIN) as w:
        w.say("my cart")
        cid, shown = w.cid, w.md.latest
    again, t = ticket(api, cid)
    with connect(api, t, headers=EMBED) as ws:
        ws.send_text('{"t":"h","v":1}')
        frames = until(ws, "s")
    assert again == cid and frames[0]["t"] == "m" and frames[0]["m"] == shown
    assert "Your cart is empty" in frames[0]["md"] and frames[-1]["s"] == "l"
