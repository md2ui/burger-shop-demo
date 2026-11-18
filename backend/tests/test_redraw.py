"""What no slot holds stays current too: when the shop's clock moves an order shown on screen,
the shop names the includes that draw orders to md2ui (`Conversation.changed`), which draws
them again on the page shown and sends a replacement only if they read otherwise, with no
agent turn (order_feeds.py). The feed still writes the stage, the arrival and the bar first;
the redraw changes the rest: the badge, the updates list, the actions and the sentences. A
payment in the app's own window redraws the page shown the same way (main.py)."""

import json
import time

import main
import pages
from test_api import reply, script, text, window
from test_feeds import advance, clock, replaced  # noqa: F401 -- clock is a fixture


def test_the_cancel_button_goes_once_a_rider_has_the_order(api, monkeypatch, clock):
    fake = script(monkeypatch, reply(text("{{order BS-1042}}")))
    with window(api) as w:
        w.say("where is my order?")
        assert "[Cancel order](agent:cancel-order?id=BS-1042)" in w.page
        advance(w, clock, 3)  # on the way: past the cancel window
        page = replaced(w, "[`On the way`](feed:stage-BS-1042)", "Order again")
        assert "Cancel order" not in page and "*🛵*" in page  # the badge, which no slot holds
        assert "the backend redrew {{order}}" in " ".join(w.md.take_handled())  # the agent hears it once
    assert len(fake.requests) == 1


def test_the_updates_list_grows_as_the_order_moves(api, monkeypatch, clock):
    fake = script(monkeypatch, reply(text("{{order BS-1042}}")))
    with window(api) as w:
        w.say("where is my order?")
        assert "__Preparing your order__" not in w.page and "_Preparing your order_" in w.page  # upcoming, muted
        advance(w, clock, 1)
        page = replaced(w, "__Preparing your order__")
        assert "__Order received__" in page
        advance(w, clock, 2)
        page = replaced(w, "__Picked up by")
        assert page.count("__ : _") == 3  # three done rows: received, preparing, picked up
    assert len(fake.requests) == 1


def test_after_delivery_no_card_still_says_arriving(api, monkeypatch, clock):
    """The home's orders section: its fed track card said "arriving around" next to a chip fed
    Delivered; the redraw draws the delivered order as the last one instead."""
    fake = script(monkeypatch, reply(text("{{your-orders}}")))
    with window(api) as w:
        w.say("my orders?")
        assert "arriving around" in w.page and "feed:stage-BS-1042" in w.page
        advance(w, clock, 6)
        page = replaced(w, "__Last order BS-1042__")
        assert "arriving around" not in page and "feed:" not in page
        assert w.page == page and not w.md.orders.producers
    assert len(fake.requests) == 1


def test_the_status_page_ends_as_a_receipt(api, monkeypatch, clock):
    script(monkeypatch, reply(text("{{order BS-1042}}")))
    with window(api) as w:
        w.say("where is my order?")
        advance(w, clock, 6)
        page = replaced(w, "___Delivered___")
        assert "Arriving around" not in page and "Your order was delivered." in page and "feed:" not in page


def test_a_page_with_no_slot_of_the_order_is_redrawn_too(api, monkeypatch, clock):
    """The order list draws the running order as a link card, where md2ui takes no slot: no
    feed, and its chip moves by the redraw alone."""
    script(monkeypatch, reply(text("{{orders}}")))
    with window(api) as w:
        w.say("my orders")
        assert "***`Received`***" in w.page and not w.md.feeds.live()
        advance(w, clock, 1)
        assert "***`Preparing`***" in replaced(w, "***`Preparing`***")


def test_nothing_is_sent_when_nothing_on_the_page_changed(api, monkeypatch, clock):
    script(monkeypatch, reply(text("{{order BS-1042}}")))
    with window(api) as w:
        w.say("where is my order?")
        shown = w.md.latest
        assert api.portal.call(w.md.changed, pages.DRAWS_ORDERS) is None  # the order has not moved
        clock[0] += 1  # within its stage and its quote
        w.md.orders.wake("BS-1042")  # the producer's pass: the same values, nothing to redraw
        time.sleep(3)  # past md2ui's slowest feed tick
        assert w.md.latest == shown


def test_paying_in_the_apps_window_redraws_the_cart_shown(api, monkeypatch):
    script(monkeypatch, reply(text("{{cart}}")))
    main.shop.set_qty("classic-smash", 1)
    with window(api) as w:
        w.say("my cart")
        assert "# Your cart" in w.page
        s = api.post("/api/checkout").json()
        assert api.post(f"/api/checkout/{s['session_id']}/pay",
                        json={"card_number": "4242 4242 4242 4242", "expiry": "12/30", "cvc": "123"}).json()["status"] == "paid"
        frame = json.loads(w.ws.receive_text())
        assert frame["t"] == "m" and "r" in frame and "Your cart is empty" in frame["md"]
