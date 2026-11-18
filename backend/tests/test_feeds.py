"""A running order on screen moves by md2ui's feeds, with no agent turn (order_feeds.py): its
page marks the stage and the arrival as slots and keys its bar, the shop opens a feed for it
when the page is shown, and posts the order's values as the shop's clock moves it. A
delivered order's page is a receipt and opens none. The shop's clock is a stand-in here; a
producer is woken by hand where it would wait for the next stage."""

import json
import time

import pytest

import main
from shop import STAGE_SECONDS, Shop, clock_time
from test_api import reply, script, text, window


@pytest.fixture
def clock(monkeypatch):
    """The shop on a clock the test moves, with one order paid now: BS-1042, received."""
    now = [time.time()]
    shop = Shop(clock=lambda: now[0])
    monkeypatch.setattr(main, "shop", shop)
    shop.set_qty("classic-smash", 2)
    shop.pay(shop.create_checkout().id, "4242 4242 4242 4242", "12/30", "123")
    return now


def replaced(w, *words: str) -> str:
    """The Markdown of the first replacement md2ui sends the window holding every one of
    *words*: what the window draws, with no agent turn in between."""
    while True:
        frame = json.loads(w.ws.receive_text())
        assert frame["t"] != "s" or frame["s"] != "w", "the agent was woken"
        if frame["t"] == "m" and "r" in frame and all(x in frame["md"] for x in words):
            return frame["md"]


def advance(w, now, steps: float, order_id: str = "BS-1042") -> None:
    now[0] += steps * STAGE_SECONDS
    w.md.orders.wake(order_id)  # where the producer would sleep until the stage changed


def test_the_status_page_moves_with_the_order_and_ends_delivered(api, monkeypatch, clock):
    fake = script(monkeypatch, reply(text("{{order BS-1042}}")))
    with window(api) as w:
        w.say("where is my order?")
        assert "***[`Received`](feed:stage-BS-1042)***" in w.page
        assert "[" + main.shop.order_view(main.shop.order("BS-1042"))["arrives"] + "](feed:arrives-BS-1042)" in w.page
        (feed,) = w.md.feeds.live()
        assert set(feed.values) == {"stage-BS-1042", "arrives-BS-1042", "Progress"}
        assert feed.until == "silence"

        advance(w, clock, 1)
        assert "Progress: 40%" in replaced(w, "[`Preparing`](feed:stage-BS-1042)")
        advance(w, clock, 2)
        assert "Progress: 75%" in replaced(w, "[`On the way`](feed:stage-BS-1042)")
        advance(w, clock, 3)
        final = replaced(w, "[`Delivered`](feed:stage-BS-1042)", "Progress: 100%")
        assert w.page == final  # the page keeps the final values
    assert feed.ended == "end" and not w.md.feeds.live()
    assert len(fake.requests) == 1  # no turn of the agent's moved anything


def test_the_arrival_moves_while_the_order_runs_and_ends_as_the_delivery_time(api, monkeypatch, clock):
    """The arrival slot is fed the shop's estimate, which moves at each stage and on the way;
    the delivered order's page is a receipt that says when it came, with no slot."""
    script(monkeypatch, reply(text("{{order BS-1042}}")), reply(text("{{order BS-1042}}")))
    order = main.shop.order("BS-1042")
    with window(api) as w:
        w.say("where is my order?")
        seen = [main.shop.order_view(order)["arrives"]]
        assert f"[{seen[0]}](feed:arrives-BS-1042)" in w.page
        for steps in (1, 2, 0.5, 0.5, 0.5):  # preparing, on the way, three quotes on the way
            advance(w, clock, steps)
            now = main.shop.order_view(order)["arrives"]
            if now != seen[-1]:  # md2ui sends only a change
                replaced(w, f"[{now}](feed:arrives-BS-1042)")
            seen.append(now)
        assert len(set(seen)) >= 3, seen  # the slot changed during the order's life
        advance(w, clock, 2)
        replaced(w, "[`Delivered`](feed:stage-BS-1042)")
        w.say("and now?")
        door = clock_time(main.shop.order("BS-1042").placed_at + 6 * STAGE_SECONDS)
        assert f"delivered Today at {door}_" in w.page and "feed:" not in w.page


def test_a_delivered_order_is_a_receipt_with_no_feed(api, monkeypatch, clock):
    script(monkeypatch, reply(text("{{order BS-1040}}")))  # from the demo customer's history
    with window(api) as w:
        w.say("my last order")
        assert "___Delivered___" in w.page and "feed:" not in w.page
        assert not w.md.feeds.live()


def test_the_home_track_card_moves_too(api, monkeypatch, clock):
    script(monkeypatch, reply(text("{{track}}")))
    with window(api) as w:
        w.say("my order?")
        assert "feed:stage-BS-1042" in w.page and len(w.md.feeds.live()) == 1
        advance(w, clock, 1)
        assert "Progress: 40%" in replaced(w, "[`Preparing`](feed:stage-BS-1042)")


def test_cancelling_ends_the_feed_on_the_cancel_sheet(api, monkeypatch, clock):
    script(monkeypatch, reply(text("{{cancel BS-1042}}")))
    with window(api) as w:
        w.say("cancel my order")
        (feed,) = w.md.feeds.live()
        assert set(feed.values) == {"stage-BS-1042"}  # the sheet has no bar and no arrival
        main.shop.cancel_order("BS-1042")  # the shop tells the producer
        replaced(w, "__Cancel order BS-1042?__", "[`Cancelled`](feed:stage-BS-1042)")
    assert feed.ended == "end"


def test_another_page_ends_the_feed(api, monkeypatch, clock):
    script(monkeypatch, reply(text("{{order BS-1042}}")), reply(text("{{cart}}")))
    with window(api) as w:
        w.say("where is my order?")
        (feed,) = w.md.feeds.live()
        producer = w.md.orders.producers["BS-1042"]
        w.say("my cart")
        assert producer.task.cancelled() or producer.task.cancelling()  # the shop stops posting
        for _ in range(50):  # md2ui ends the feed at its next tick
            if feed.ended:
                break
            time.sleep(0.1)
        assert feed.ended == "replaced" and not w.md.orders.producers
