"""
order_feeds.py

A running order kept current on the page while it is on screen, with no agent turn: its stage,
arrival and progress by md2ui's own feeds (its ADR-608), and everything else the page draws of
it (the badge, the updates list, the actions, the sentences) by md2ui's redraw of the includes
that draw it (`Conversation.changed`, its ADR-612 as amended 2026-11-16). The shop is the
producer of both.

A page that shows a running order marks its live values as feed slots named by the order,
`[`Preparing`](feed:stage-BS-1042)` and `[8:22 PM](feed:arrives-BS-1042)` (pages.py), and its
bar is keyed (`Progress: 40%`). Each time md2ui shows a page (the agent's reply, a page the
shop or a handler shows, the page a window comes back to), the shop reads the slots on it
and opens one md2ui feed per running order they name. The page's Markdown is what says which
orders are live there; the shop keeps nothing else about what is on screen.

Each feed has a producer: a task that reads the order from the shop, whose clock decides the
stage and the arrival estimate, at each change of either and every REFRESH seconds between,
and posts its values to the feed. md2ui checks each value, writes only the ones that changed
and sends the page as a replacement. Once the order is delivered or cancelled the producer posts the final values and
`end`, and the page keeps them. A page left behind ends its feed (md2ui ends it, and answers
the next post 410), and its producer stops there.

When the order's view changed, the producer then names the includes that draw orders
(`pages.DRAWS_ORDERS`) to md2ui, which draws them again on the page shown and sends a
replacement only if they read otherwise. It waits for the feed's tick first, so the values
have one writer, the feed: the redraw draws the same values into the slots and changes only
what no slot holds. A page that draws a running order with no slot of it (the order list)
has a producer with no feed, which only redraws. The redraw is md2ui's, from the shop's data
now; nothing here keeps a copy of what the page says.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Collection
from dataclasses import dataclass

from md2ui import wire_server
from md2ui.wire_feeds import Feed
from md2ui.wire_frames import FrameError
from md2ui.wire_texts import page_slots

from pages import DRAWS_ORDERS, FINISHED, PROGRESS, STAGE_WORD, arrives_slot, live_values, stage_slot
from shop import Shop

log = logging.getLogger("burger-shop.feeds")

# How often a producer posts between stage boundaries. md2ui ends a feed that falls silent
# for ten of its usual gaps (at least a minute), and an order's stages are minutes apart.
REFRESH = 20.0
# How long a producer waits for md2ui's tick to write what it posted before it redraws: the
# tick comes within two seconds (md2ui's TICK); past this it redraws anyway.
WRITTEN = 5.0


@dataclass
class Producer:
    page: str  # the page shown when it started; it runs while that page (or its replacement) is shown
    feed: Feed | None  # None: the page draws the order with no slot of it, and is only redrawn
    wake: asyncio.Event
    task: asyncio.Task


class OrderFeeds:
    """The feeds of one conversation's page: one per running order it shows."""

    def __init__(self, md: wire_server.Conversation, shop: Shop) -> None:
        self.md, self.shop = md, shop
        self.producers: dict[str, Producer] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        shop.listeners.append(self.wake)

    def wake(self, order_id: str) -> None:
        """The order changed other than by the clock (a cancel): its producer posts now."""
        producer = self.producers.get(order_id)
        if producer is not None and self._loop is not None:
            self._loop.call_soon_threadsafe(producer.wake.set)

    async def track(self) -> None:
        """A producer for each running order the page on screen shows and none watches: with a
        feed when the page marks its slots, and with none when only an include draws it."""
        self._loop = asyncio.get_running_loop()
        shown = self.md.latest
        if shown is None:
            return
        for order_id, producer in list(self.producers.items()):  # a page left behind stops its producers
            ended = producer.feed is not None and producer.feed.ended is not None
            if ended or self.md.log.head(producer.page) != shown:
                producer.task.cancel()
                del self.producers[order_id]
        slots = page_slots(self.md.log.markdown(shown))
        ids = dict.fromkeys(name.split("-", 1)[1] for name in slots if name.startswith(("stage-", "arrives-")))
        drawn = any(r.name in DRAWS_ORDERS for r in self.md.log.pages.includes.regions(shown))
        running = [o.id for o in self.shop.history() if self.shop.order_view(o)["status"] not in FINISHED]
        watched: list[str] = [*ids, *running] if drawn else list(ids)
        for order_id in dict.fromkeys(watched):
            if order_id in self.producers:
                continue
            order = self.shop.orders.get(order_id)
            if order is None or self.shop.order_view(order)["status"] in FINISHED:
                continue  # a receipt: the slots stay as drawn
            names = [n for n in (stage_slot(order_id), arrives_slot(order_id)) if n in slots]
            # The bar is the order's only when the page shows one order.
            feed = await self._open(shown, names, [PROGRESS] if len(ids) == 1 else []) if names else None
            if feed is None and not drawn:
                continue
            wake = asyncio.Event()
            task = asyncio.create_task(self._produce(order_id, feed, wake))
            self.producers[order_id] = Producer(shown, feed, wake, task)

    async def _open(self, shown: str, names: list[str], keys: list[str]) -> Feed | None:
        stage = [n for n in names if n.startswith("stage-")]
        values = {stage[0]: list(STAGE_WORD.values())} if stage else None
        try:
            return await self.md.feeds.open(shown, keys or None, None, values=values, slots=names)
        except FrameError as e:
            if keys:  # a page with the order's slots and no bar of its own: the cancel sheet
                return await self._open(shown, names, [])
            # A slot spelled otherwise than the patterns (the agent's own page): left as drawn.
            log.warning("no feed for %s: %s", ", ".join(names), e)
            return None

    async def _produce(self, order_id: str, feed: Feed | None, wake: asyncio.Event) -> None:
        order = self.shop.orders[order_id]
        drawn = self.shop.order_view(order)  # the order as the page was drawn
        while True:
            wake.clear()  # a wake while this pass posts and redraws makes another pass
            v = self.shop.order_view(order)
            finished = v["status"] in FINISHED
            if feed is not None:
                values = {k: value for k, value in live_values(v).items() if k in feed.values}
                status, answer = await self.md.feeds.post(feed.token, json.dumps(values))
                if status in (404, 410):  # the page was left: md2ui ended the feed
                    return
                if status != 200:
                    log.warning("feed %s refused %s: %s", feed.id, values, answer.get("error"))
                if finished:
                    await self.md.feeds.post(feed.token, "end")
                await self._written(feed)
                if self.shop.order_view(order) != v:
                    continue  # it moved meanwhile: its values go to the feed before any redraw
            if v != drawn:
                mine = self.producers.get(order_id)
                if finished and mine is not None and mine.task is asyncio.current_task():
                    del self.producers[order_id]  # done: the redraw's tracking must not cancel it
                await self.md.changed(DRAWS_ORDERS)
                drawn = v
            if finished:
                return
            try:
                await asyncio.wait_for(wake.wait(), min(REFRESH, (self.shop.next_change(order) or 0) + 0.05))
            except TimeoutError:
                pass

    @staticmethod
    async def _written(feed: Feed) -> None:
        """Until md2ui's tick has written what *feed* was posted (or ended it)."""
        for _ in range(int(WRITTEN / 0.05)):
            if feed.ended is not None or not (feed.pending or feed.ending):
                return
            await asyncio.sleep(0.05)


class ShopConversation(wire_server.Conversation):
    """md2ui's conversation for one of the shop's, which tells the order feeds whenever a page
    may have changed: one sent, a tap or a message received (a handler may have shown a
    page), a window joined (its feeds ended when the last one left), includes redrawn (one
    may now draw a running order)."""

    def __init__(self, shop: Shop, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.orders = OrderFeeds(self, shop)

    async def _track(self) -> None:
        try:
            await self.orders.track()
        except Exception:  # live values are a nicety: a page is never lost to them
            log.exception("order feeds not opened")

    async def send(self, markdown: str, replaces: str | None = None, continues: str | None = None) -> str:
        mid = await super().send(markdown, replaces=replaces, continues=continues)
        await self._track()
        return mid

    async def receive(self, frame: dict, peer: str):
        result = await super().receive(frame, peer)
        await self._track()
        return result

    async def changed(self, names: Collection[str]) -> str | None:
        mid = await super().changed(names)
        await self._track()
        return mid

    async def join(self, ws, peer: str = "") -> None:
        await super().join(ws, peer)
        await self._track()
