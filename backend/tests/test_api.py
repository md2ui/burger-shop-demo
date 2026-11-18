"""The shop's API with a scripted stand-in for Claude: no API key, no network. Both apps talk
to a conversation over md2ui's WebSocket, behind the shop's ticket (test_socket.py): a typed
message is md2ui's prompt frame and a tap its event frame, naming the message shown and the
target's ordinal, found here as the app's view would report them. HTTP keeps what is the
app's own: the home page, the native chrome's pages, the payment window and the footer's
badge."""

import json
from contextlib import contextmanager
from types import SimpleNamespace

import home_writer
import main
import socket_door


def text(t: str):
    return SimpleNamespace(type="text", text=t)


def tool_use(name: str, args: dict | None = None, id_: str = "tu_1"):
    return SimpleNamespace(type="tool_use", id=id_, name=name, input=args or {})


def reply(*blocks, stop: str = "end_turn"):
    return SimpleNamespace(content=list(blocks), stop_reason=stop)


class FakeClaude:
    """Returns the scripted responses in order and records every request."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests: list[dict] = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

    async def create(self, **kwargs):
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        return self.responses.pop(0)


def script(monkeypatch, *responses) -> FakeClaude:
    fake = FakeClaude(*responses)
    monkeypatch.setattr(main, "claude", fake)
    return fake


def target(cid: str, action: str | None = None, label: str | None = None, **params) -> tuple[str, int]:
    """The page shown and the ordinal of its first target with that action (and params) or
    label, as md2ui numbers them: what the app's view reports for a tap."""
    md = main.CONVERSATIONS[cid].md
    for x, t in enumerate(md.log.targets(md.latest)):
        a = t.action
        if a is not None and (action is None or a.action == action) and (label is None or a.label == label) \
                and (not params or dict(a.params) == params):
            return md.latest, x
    raise AssertionError(f"no {action or label} {params} on the page shown")


class Window:
    """An app's view on md2ui's socket, as md2ui-ts's wire client drives it: each frame it
    sends is numbered, and what comes back is read until the agent listens again, the
    payment window holds its turn, or md2ui answers a frame that woke no one."""

    def __init__(self, api, ws, cid: str):
        self.api, self.ws, self.cid, self.q = api, ws, cid, 0

    def send(self, frame: dict) -> list[dict]:
        self.q += 1
        self.ws.send_text(json.dumps(frame | {"q": self.q}))
        return self.settled()

    def settled(self) -> list[dict]:
        read = []
        while True:
            read.append(json.loads(self.ws.receive_text()))
            if read[-1]["t"] == "s" and (read[-1]["s"] != "w" or "n" in read[-1]):
                return read

    def say(self, words: str) -> list[dict]:
        return self.send({"t": "p", "tx": words})

    def tap(self, action: str | None = None, label: str | None = None, vs: list | None = None, **params) -> list[dict]:
        m, x = target(self.cid, action, label, **params)
        return self.send({"t": "e", "m": m, "x": x} | ({"a": action} if action else {}) | ({"vs": vs} if vs is not None else {}))

    @property
    def md(self):
        return main.CONVERSATIONS[self.cid].md

    @property
    def page(self) -> str:
        """The page on screen, as md2ui sent it."""
        return self.md.log.markdown(self.md.latest)

    def cart(self) -> dict:
        return self.api.get("/api/state", params={"conversation_id": self.cid}).json()["cart"]


@contextmanager
def window(api, cid: str | None = None, origin: str = "http://localhost:5173"):
    """A ticket from the shop, md2ui's socket opened with it, and the hello."""
    r = api.post("/api/session", json={"conversation_id": cid}).json()
    with api.websocket_connect(f"{socket_door.PATH}?ticket={r['ticket']}", headers={"origin": origin}) as ws:
        ws.send_text('{"t":"h","v":1}')
        w = Window(api, ws, r["conversation_id"])
        w.settled()
        yield w


def refusal(frames: list[dict]) -> str | None:
    """The code of md2ui's refusal among *frames*, if any."""
    return next((f["code"] for f in frames if f["t"] == "x"), None)


def test_includes_become_pages(api, monkeypatch):
    script(monkeypatch, reply(text("{{home}}")))
    with window(api) as w:
        w.say("hi")
        assert w.page.startswith("# {#headline-1}") and w.cart()["item_count"] == 0


def test_taps_patch_the_page_and_reach_the_agent_as_notes(api, monkeypatch):
    fake = script(monkeypatch, reply(text("{{home}}")), reply(text("{{cart}}")))
    with window(api) as w:
        w.say("hi")
        first = w.md.latest
        frames = w.tap("cart-add", id="classic-smash")
        assert frames[0]["t"] == "m" and frames[0]["r"] == first  # redrawn in place
        assert w.cart()["total_label"] == "$12.49"
        assert "__[➖](agent:cart-remove?id=classic-smash)__ - **1** -" in w.page
        w.tap("like", id="double-pickle")
        assert "agent:unlike?id=double-pickle" in w.page
        assert len(fake.requests) == 1  # neither tap woke the agent
        w.say("what's in my cart?")
    sent = fake.requests[1]["messages"][-1]["content"]
    assert sent.startswith('[App notes]\n- User chose "➕": cart-add {id: classic-smash}')  # md2ui's digest
    assert 'User chose "🤍": like {id: double-pickle}' in sent and "the backend answered it" in sent
    assert "Cart now: 1 × Classic Smash (double)" in sent
    assert sent.endswith("what's in my cart?")


def test_a_tap_md2ui_cannot_verify_changes_nothing(api, monkeypatch):
    fake = script(monkeypatch, reply(text("{{cards classic-smash}}")))
    with window(api) as w:
        w.say("hi")
        m, x = target(w.cid, "cart-add", id="classic-smash")
        for forged, code in (({"m": m, "x": 99}, "bad_target"), ({"m": m, "x": x, "a": "free-burgers"}, "slug_mismatch"),
                             ({"m": "m-never", "x": x}, "unknown_message")):
            assert refusal(w.send({"t": "e"} | forged)) == code, forged
    assert main.shop.cart == {} and len(fake.requests) == 1


def test_tools_run_on_the_server(api, monkeypatch):
    fake = script(
        monkeypatch,
        reply(tool_use("update_cart", {"items": [{"id": "bacon-bbq", "quantity": 2}]}), stop="tool_use"),
        reply(text("Added!\n\n{{cart}}")),
    )
    with window(api) as w:
        w.say("two bacon bbq please")
        assert w.cart()["item_count"] == 2 and "`2 items`" in w.page
    result = fake.requests[1]["messages"][-1]["content"][0]
    assert result["type"] == "tool_result" and "$23.80" in result["content"]


def test_checkout_pauses_for_the_payment_window(api, monkeypatch):
    main.shop.set_qty("classic-smash", 3)
    fake = script(monkeypatch, reply(tool_use("open_checkout", id_="tu_pay"), stop="tool_use"),
                  reply(text("{{success}}")))
    with window(api) as w:
        frames = w.say("pay for my cart")
        assert frames[-1]["s"] == "w" and frames[-1]["n"] == "Waiting for the payment window"
        assert w.page.startswith("# Checkout")  # behind the window: the order review
        pending = api.get("/api/state", params={"conversation_id": w.cid}).json()["pending_action"]
        assert pending["tool_name"] == "open_checkout" and pending["checkout"]["total"] == "$28.50"

        # While the window is open, the conversation waits: a message is not heard, a page not shown.
        assert w.say("hi")[-1]["n"] == "Waiting for the payment window" and len(fake.requests) == 1
        assert api.post("/api/nav", json={"conversation_id": w.cid, "to": "cart"}).status_code == 409

        sid = pending["checkout"]["session_id"]
        paid = api.post(f"/api/checkout/{sid}/pay",
                        json={"card_number": "4242 4242 4242 4242", "expiry": "12/30", "cvc": "123"}).json()
        assert paid["status"] == "paid" and paid["cart"]["item_count"] == 0

        assert api.post("/api/resume", json={"conversation_id": w.cid, "tool_use_id": "tu_pay"}).status_code == 204
        w.settled()
        assert "Payment successful" in w.page and "Visa •••• 4242" in w.page
        assert api.get("/api/state", params={"conversation_id": w.cid}).json()["pending_action"] is None
    result = fake.requests[1]["messages"][-1]["content"][-1]
    assert result["tool_use_id"] == "tu_pay" and '"status": "paid"' in result["content"]
    assert "4242 4242" not in str(fake.requests)  # the card number never reaches the agent


def test_closing_the_window_without_paying_cancels(api, monkeypatch):
    main.shop.set_qty("classic-smash", 1)
    fake = script(monkeypatch, reply(tool_use("open_checkout", id_="tu_pay"), stop="tool_use"),
                  reply(text("No problem.\n\n{{cart}}")))
    with window(api) as w:
        w.say("pay")
        api.post("/api/resume", json={"conversation_id": w.cid, "tool_use_id": "tu_pay"})
        w.settled()
        assert "# Your cart" in w.page
    assert '"status": "cancelled"' in fake.requests[1]["messages"][-1]["content"][-1]["content"]


def test_the_apps_own_checkout_pays_and_confirms_without_the_agent(api, monkeypatch):
    """The footer's Checkout, or the page's (both apps catch `agent:checkout`): the app's own
    payment session, then the confirmation shown by the shop; the agent hears both."""
    main.shop.set_qty("triple-stack", 2)
    fake = script(monkeypatch, reply(text("Enjoy!")))
    with window(api) as w:
        api.post("/api/home", json={"conversation_id": w.cid})
        s = api.post("/api/checkout").json()
        api.post(f"/api/checkout/{s['session_id']}/pay",
                 json={"card_number": "5555 5555 5555 4444", "expiry": "01/31", "cvc": "999"})
        assert api.post("/api/nav", json={"conversation_id": w.cid, "to": "success"}).status_code == 204
        assert "Mastercard •••• 4444" in w.page and fake.requests == []
        w.say("thanks")
    sent = fake.requests[0]["messages"][-1]["content"]
    assert "paid in the app's own payment window: order BS-1042" in sent and "`{{success}}`" in sent


def test_cancel_flow_and_reorder_tools(api, monkeypatch):
    main.shop.set_qty("classic-smash", 1)
    s = main.shop.create_checkout()
    main.shop.pay(s.id, "4242 4242 4242 4242", "12/30", "123")
    fake = script(
        monkeypatch,
        reply(text("{{order}}")),
        reply(text("{{cancel BS-1042}}")),
        reply(tool_use("cancel_order", {"order_id": "BS-1042", "reason": "Too slow"}), stop="tool_use"),
        reply(text("{{order BS-1042}}")),
        reply(tool_use("reorder", {"order_id": "BS-1040"}), stop="tool_use"),
        reply(text("{{cart}}")),
    )
    with window(api) as w:
        w.say("where is my order?")
        w.tap("cancel-order", id="BS-1042")
        assert "Cancel order BS-1042?" in w.page
        w.tap("confirm-cancel", id="BS-1042")
        result = fake.requests[3]["messages"][-1]["content"][0]["content"]
        assert '"status": "cancelled"' in result and '"refunded": "$12.49"' in result
        assert "Order cancelled" in w.page and "Too slow" in w.page
        w.say("order my last delivered order again")
        assert w.cart()["item_count"] == 4 and "# Your cart" in w.page


def test_home_turns_carry_the_home_context(api, monkeypatch):
    fake = script(monkeypatch, reply(text("{{home-rest}}")), reply(text("{{cart}}")), reply(text("{{home-rest}}")))
    with window(api) as w:
        for said in ("Hi! Show me the home page.", "show my cart", "Home"):
            w.say(said)
    sent = [r["messages"][-1]["content"] for r in fake.requests]
    assert "[Home context]" in sent[0] and '"part_of_day"' in sent[0] and "Alex" not in sent[0]  # no name: the demo greets the moment
    assert "[Home context]" not in sent[1]
    assert "[Home context]" in sent[2] and sent[2].endswith("Home")


class FakeWriter:
    def __init__(self, reply: str | Exception):
        self.reply, self.calls = reply, 0

    async def write(self, context):
        self.calls += 1
        if isinstance(self.reply, Exception):
            raise self.reply
        return home_writer.check(self.reply)

    async def close(self):
        pass


FRESH = """{{headline greeting="Good evening, hungry?" line="The new Smokehouse is $11.50." image=smokehouse cta="Try it" action=product?id=smokehouse}}
{{offer product=classic-smash kicker="Your usual" chip="Ordered 3 times"}}
{{offer product=double-pickle kicker="New for you"}}
{{offer promo=box-deal}}
{{home-rest note="Same again tonight?"}}"""


def shown(cid: str) -> str:
    """The page on screen in *cid*, as md2ui sent it."""
    md = main.CONVERSATIONS[cid].md
    return md.log.markdown(md.latest)


def fresh_swapped(api, cid: str, token: int) -> bool:
    """Asks for the fresh home; true when it took the instant one's place."""
    md = main.CONVERSATIONS[cid].md
    before = md.latest
    api.post("/api/home/fresh", json={"conversation_id": cid, "token": token})
    return md.latest != before


def test_home_is_instant_then_fresh(api, monkeypatch):
    fake = script(monkeypatch)  # no agent call may happen
    monkeypatch.setattr(main, "writer", FakeWriter(FRESH))
    r = api.post("/api/home", json={}).json()
    cid, instant = r["conversation_id"], main.CONVERSATIONS[r["conversation_id"]].md.latest
    assert shown(cid).startswith("# {#headline-1}") and "Alex" not in shown(cid)
    assert any(f"___{g}___" in shown(cid) for g in main.pages.SALUTE.values())
    assert fresh_swapped(api, cid, r["token"])
    assert "___Good evening, hungry?___" in shown(cid) and "Same again tonight?" in shown(cid) and fake.requests == []
    md = main.CONVERSATIONS[cid].md
    assert md.log.head(instant) == md.latest  # in place of the instant one
    assert "The window shows the home page" in main.NOTES.take(main.shop, [], [])


def test_a_fresh_home_is_dropped_once_the_customer_moved_on(api, monkeypatch):
    script(monkeypatch, reply(text("{{cart}}")))
    monkeypatch.setattr(main, "writer", FakeWriter(FRESH))
    for moved_on in (lambda w: w.say("show my cart"),
                     lambda w: w.tap("catalog", category="sides"),  # a page the shop shows
                     lambda w: api.post("/api/nav", json={"conversation_id": w.cid, "to": "orders"})):
        with window(api) as w:
            r = api.post("/api/home", json={"conversation_id": w.cid}).json()
            w.tap("cart-add")  # a redraw of the home: still fine
            moved_on(w)
            assert not fresh_swapped(api, w.cid, r["token"])


def test_a_failed_or_bad_writer_keeps_the_instant_home(api, monkeypatch):
    for bad in (RuntimeError("down"), "Hello there!", FRESH.replace("{{home-rest", "{{cart"),
                FRESH.replace("action=product?id=smokehouse", "action=reorder?id=BS-1040")):
        monkeypatch.setattr(main, "writer", FakeWriter(bad))
        r = api.post("/api/home", json={}).json()
        assert not fresh_swapped(api, r["conversation_id"], r["token"]), bad


def open_home(api, cid=None) -> tuple[str, bool]:
    """Home, and the fresh one when asked for: the conversation, and whether it was written."""
    r = api.post("/api/home", json={"conversation_id": cid}).json()
    if r["fresh"]:
        fresh_swapped(api, r["conversation_id"], r["token"])
    return r["conversation_id"], r["fresh"]


def test_the_home_is_written_once_a_session(api, monkeypatch):
    w = FakeWriter(FRESH)
    monkeypatch.setattr(main, "writer", w)
    cid, fresh = open_home(api)
    assert fresh and w.calls == 1
    main.shop.set_qty("bacon-bbq", 1)
    assert api.post("/api/home", json={"conversation_id": cid}).json()["fresh"] is False and w.calls == 1  # no writer call
    md = shown(cid)
    assert "___Good evening, hungry?___" in md and "Same again tonight?" in md
    assert "__[➖](agent:cart-remove?id=bacon-bbq)__ - **1** -" in md  # its live parts are live
    assert open_home(api)[1] and w.calls == 2  # another session writes its own


def test_the_saved_home_is_rewritten_for_a_new_part_of_the_day(api, monkeypatch):
    w = FakeWriter(FRESH)
    monkeypatch.setattr(main, "writer", w)
    cid = open_home(api)[0]
    main.CONVERSATIONS[cid].saved_for["part_of_day"] = "morning" if main.shop.home_context()["now"]["part_of_day"] != "morning" else "evening"
    assert api.post("/api/home", json={"conversation_id": cid}).json()["fresh"] is True


def test_the_orders_line_is_dropped_once_the_order_moved_on(api, monkeypatch):
    monkeypatch.setattr(main, "writer", FakeWriter(FRESH))
    cid = open_home(api)[0]
    main.CONVERSATIONS[cid].saved_for["order"] = ("BS-9999", "preparing")  # written for another state
    api.post("/api/home", json={"conversation_id": cid})
    md = shown(cid)
    assert "Same again tonight?" not in md and "Fancy your usual again?" in md and "___Good evening, hungry?___" in md


def test_a_home_the_agent_writes_becomes_the_saved_one(api, monkeypatch):
    monkeypatch.setattr(main, "writer", FakeWriter(FRESH))
    agent_home = FRESH.replace("Good evening, hungry?", "Shake o'clock!")
    script(monkeypatch, reply(text(agent_home)), reply(text("{{home-saved}}")))
    with window(api) as w:
        open_home(api, w.cid)
        w.say("put the shakes on my home page")
        api.post("/api/home", json={"conversation_id": w.cid})
        assert "Shake o'clock!" in w.page
        w.say("take me home")
        assert "Shake o'clock!" in w.page and "{{" not in w.page


def test_history_tools(api):
    import asyncio
    import tools
    out = asyncio.run(tools.call_backend_tool(main.shop, "get_orders", {"limit": 2}))
    assert [o["order_id"] for o in out["orders"]] == ["BS-1040", "BS-1039"] and out["usual_items"]
    recs = asyncio.run(tools.call_backend_tool(main.shop, "get_recommendations", {}))
    assert recs["order_again"][0]["id"] == "crispy-fries"
    err = asyncio.run(tools.call_backend_tool(main.shop, "cancel_order", {"order_id": "BS-1040"}))
    assert "can no longer be cancelled" in err["error"]


# --- taps that only choose a page: md2ui's handlers show it, with no agent turn (ADR-614) ----
def test_navigation_taps_cost_no_agent_turn(api, monkeypatch):
    main.shop.set_qty("classic-smash", 1)
    fake = script(monkeypatch, reply(text("{{cart}}")), reply(text("Spicy ones:\n\n{{menu spicy=true}}")))
    with window(api) as w:
        w.say("cart")
        frames = w.tap("catalog")  # Keep shopping
        assert w.page.startswith("# Our menu") and "r" not in frames[0]  # a new page, not a redraw
        w.tap("catalog", category="sides")  # the Sides tab
        assert w.page.startswith("# Sides") and "Crispy Fries" in w.page
        w.tap("catalog", category="shakes")
        assert w.page.startswith("# Shakes")
        for to, heading in (("cart", "# Your cart"), ("orders", "# Your orders")):  # the native chrome's buttons
            api.post("/api/nav", json={"conversation_id": w.cid, "to": to})
            assert w.page.startswith(heading)
        assert len(fake.requests) == 1  # none of them woke the agent
        w.say("anything spicy?")
    sent = fake.requests[1]["messages"][-1]["content"]
    assert 'User chose "🍟 Sides": catalog {category: sides} (message ' in sent
    assert "the backend showed {{menu category=sides}}" in sent
    assert "The app showed `{{orders}}` from its own orders button" in sent


def test_a_catalog_tap_the_shop_does_not_answer_is_the_agents(api, monkeypatch):
    fake = script(monkeypatch, reply(text("{{home}}")), reply(text("{{menu spicy=true}}")))
    with window(api) as w:
        w.say("hi")
        w.tap("catalog", filter="spicy")
        assert w.page.startswith("# Our menu")
    assert 'User chose "🔥 Something spicy": catalog {filter: spicy} (message ' in fake.requests[1]["messages"][-1]["content"]


def test_a_view_cart_link_on_the_page_shows_the_cart(api, monkeypatch):
    main.shop.set_qty("classic-smash", 1)
    fake = script(monkeypatch, reply(text("[View cart](agent:cart) [My orders](agent:orders)")))
    with window(api) as w:
        w.say("hi")
        w.tap("cart")
        assert w.page.startswith("# Your cart")
        api.post("/api/nav", json={"conversation_id": w.cid, "to": "orders"})  # wherever the customer is
    assert len(fake.requests) == 1


def test_md2uis_issues_with_the_agents_page_reach_its_next_turn(api, monkeypatch):
    fake = script(monkeypatch, reply(text("{{cart}}\n\n{{nonsense}}")), reply(text("{{cart}}")))
    with window(api) as w:
        w.say("cart")
        assert "Could not show the" not in w.page  # an unknown include draws nothing
        w.say("and now?")
    sent = fake.requests[1]["messages"][-1]["content"]
    assert "md2ui on your last page: error (unknown-include)" in sent and "{{nonsense}}" in sent


def test_empty_carts_and_unknown_conversations_are_refused(api):
    assert api.post("/api/checkout").status_code == 409
    assert api.post("/api/nav", json={"conversation_id": "nope", "to": "cart"}).status_code == 404
    assert api.post("/api/resume", json={"conversation_id": "nope", "tool_use_id": "tu"}).status_code == 404


def test_theme_is_served(api):
    assert api.get("/theme/THEME.md").text.startswith("# Burger Shop")
    assert api.get("/theme/assets/fonts/Inter_18pt-Regular.ttf").status_code == 200


# --- sizes and the form's commit press ---------------------------------------------------
def test_a_stepper_changes_its_sized_line(api, monkeypatch):
    main.shop.set_qty("classic-smash", 1, {"size": "triple"})
    script(monkeypatch, reply(text("{{cart}}")))
    with window(api) as w:
        w.say("cart")
        w.tap("cart-add", id="classic-smash", size="triple")
        assert main.shop.qty("classic-smash", {"size": "triple"}) == 2 and "**$24.00**" in w.page
        w.tap("cart-remove", id="classic-smash", size="triple")
        assert main.shop.cart == {"classic-smash?size=triple": 1}
        notes = main.NOTES.take(main.shop, w.md.take_handled(), [])
    assert 'cart-add {id: classic-smash, size: triple}' in notes and "1 × Classic Smash (triple)" in notes


def test_get_product_and_update_cart_take_sizes(api):
    import asyncio
    import tools
    p = asyncio.run(tools.call_backend_tool(main.shop, "get_product", {"id": "classic-smash"}))
    assert p["default_size"] == "double" and [(s["id"], s["price"]) for s in p["sizes"]] == [
        ("single", "$7.50"), ("double", "$9.50"), ("triple", "$12.00")]
    cart = asyncio.run(tools.call_backend_tool(main.shop, "update_cart", {
        "items": [{"id": "classic-smash", "size": "triple", "quantity": 2}, {"id": "crispy-fries", "quantity": 1}]}))
    assert cart["items"][0] == {"id": "classic-smash", "name": "Classic Smash", "size": "triple", "quantity": 2,
                                "line_total": "$24.00"}
    assert "size" not in cart["items"][1]
    err = asyncio.run(tools.call_backend_tool(main.shop, "update_cart", {"items": [{"id": "classic-smash", "size": "xl", "quantity": 1}]}))
    assert "no size 'xl'" in err["error"]


def test_a_commit_press_reaches_the_agent_as_md2uis_sentence(api, monkeypatch):
    fake = script(monkeypatch, reply(text("{{product classic-smash}}")),
                  reply(tool_use("update_cart", {"items": [{"id": "classic-smash", "size": "triple", "quantity": 4}],
                                                 "add": True}), stop="tool_use"),
                  reply(text("{{cart}}")))
    with window(api) as w:
        w.say("show me the classic smash")
        vs = [[target(w.cid, label="Triple")[1], True], [target(w.cid, label="Quantity")[1], 4]]
        frames = w.tap("add", vs=vs)
        assert frames[-1]["s"] == "l" and frames[-1]["u"] == [w.q]  # the press is let go
        assert main.shop.cart == {"classic-smash?size=triple": 4} and "*`Triple`*" in w.page
    sent = fake.requests[1]["messages"][-1]["content"]
    assert sent.startswith('User chose "Add to cart": add {id: classic-smash, size: double}, with size: "Triple", "Quantity" at 4 (message ')


def test_choosing_and_counting_send_the_agent_nothing(api, monkeypatch):
    """md2ui records a choice or a count its commit press will carry; only the press is heard."""
    fake = script(monkeypatch, reply(text("{{product classic-smash}}")))
    with window(api) as w:
        w.say("show me the classic smash")
        m, x = target(w.cid, label="Triple")
        assert refusal(w.send({"t": "e", "m": m, "x": x, "a": "size", "c": True})) is None
        m, x = target(w.cid, label="Quantity")
        assert refusal(w.send({"t": "e", "m": m, "x": x, "v": 3})) is None
    assert len(fake.requests) == 1


def test_a_commit_press_must_match_the_page(api, monkeypatch):
    """Each on a page of its own: md2ui spends a button on its first press, refused or not."""
    script(monkeypatch, *[reply(text("{{product classic-smash}}"))] * 5)
    with window(api) as w:
        for values in (lambda t, q: [[q, 99]], lambda t, q: [[t, False]], lambda t, q: [[t, 4]],
                       lambda t, q: [[200, True]], lambda t, q: [[i, True] for i in range(40)]):
            w.say("show me the classic smash")
            vs = values(target(w.cid, label="Triple")[1], target(w.cid, label="Quantity")[1])
            assert refusal(w.tap("add", vs=vs)) is not None, vs
    assert main.shop.cart == {}


def test_the_prompt_teaches_the_product_form():
    from datetime import date
    import tools
    prompt = tools.system_prompt(date.today())
    assert 'User chose "Add to cart": add {id: classic-smash, size: double}' in prompt
    assert "The product page is md2ui's form" in prompt and "stay buttons on every page" in prompt
    assert "agent:add?id=classic-smash&size=double&md2ui.commit=1" in prompt  # the pattern, from the notes


def test_a_press_that_changed_nothing_says_so(api, monkeypatch):
    """md2ui-ts sends no values for a press when nothing was changed, and the agent reads
    md2ui's `with no change`: the size in the button, a quantity of 1."""
    fake = script(monkeypatch, reply(text("{{product classic-smash size=triple}}")), reply(text("Added.")))
    with window(api) as w:
        w.say("a triple classic smash")
        assert refusal(w.tap("add")) is None
    assert fake.requests[1]["messages"][-1]["content"].startswith(
        'User chose "Add to cart": add {id: classic-smash, size: triple}, with no change (message ')


def test_a_sized_tap_on_the_cart_page_patches_only_its_row(api, monkeypatch):
    main.shop.set_qty("classic-smash", 1)
    main.shop.set_qty("classic-smash", 1, {"size": "triple"})
    script(monkeypatch, reply(text("{{cart}}")))
    with window(api) as w:
        w.say("cart")
        before = w.page.split("\n")
        w.tap("cart-add", id="classic-smash", size="triple")
        after = w.page.split("\n")
    changed = [(a, b) for a, b in zip(before, after) if a != b]
    rows = [b for _a, b in changed if b.startswith("- ")]
    assert len(rows) == 1 and "*`Triple`*" in rows[0] and "**2**" in rows[0] and "**$24.00**" in rows[0]
    double = next(l for l in after if "*`Double`*" in l)
    assert double in before and "- **1** -" in double  # the Double row is untouched
    assert main.shop.cart == {"classic-smash?size=double": 1, "classic-smash?size=triple": 2}
