"""
shop.py

The mock Burger Shop services: catalog, cart, likes, checkout sessions and orders. Each
public method stands in for one call to a real service, and all state is in memory for a
single demo customer, so restarting the server resets everything.

The catalog is seeded from data/products.json. Orders move through their states on a
clock (ORDER_STAGE_SECONDS per step), so "where is my order?" has a live answer.

Burgers and shakes come in sizes (a product's `options`; its listed price is its default
size's). A cart line is a product with its options, so two Classic Smash, one Double and one
Triple, are two lines. A line's key is spelled as the steppers spell it,
`classic-smash?size=triple`; a product with no options is its bare id. Every cart call
without options means the product's defaults.
"""

from __future__ import annotations

import json
import os
import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

DATA_DIR = Path(__file__).with_name("data")
DATA = json.loads((DATA_DIR / "products.json").read_text())
HISTORY = json.loads((DATA_DIR / "past_orders.json").read_text())["orders"]
CUSTOMER = json.loads((DATA_DIR / "customer.json").read_text())

DELIVERY_FEE = float(DATA["delivery_fee"])
FREE_DELIVERY_OVER = float(DATA["free_delivery_over"])
MAX_QTY = 20
# One step of an order's life (received -> preparing -> on the way -> delivered) lasts
# this many seconds of demo time: 120 makes a whole order take about twelve minutes, and
# leaves six minutes to cancel it (until a rider picks it up).
STAGE_SECONDS = float(os.environ.get("ORDER_STAGE_SECONDS", "120"))

# (status, starts after N stages, progress %, badge, headline, update title, update detail)
STAGES = [
    ("received", 0, 10, "🧾", "Order received", "Order received", "Paid with {card}"),
    ("preparing", 1, 40, "👨‍🍳", "Preparing your order", "Preparing your order", "The kitchen started on {items} items"),
    ("on_the_way", 3, 75, "🛵", "On the way", "Picked up by {rider}", "Your rider is on the way"),
    ("delivered", 6, 100, "🏁", "Delivered", "Delivered", "Enjoy your burgers!"),
]
# The arrival is an estimate, and moves as a delivery service's does: quoted when the order is
# placed, again when the kitchen starts and when a rider picks it up, then every ETA_REQUOTE
# steps on the way. Each quote is off the true delivery by a whole number of minutes in its
# stage's range (low, high): wide and late at first, narrowing at the door. The ranges do not
# overlap, so every stage change moves the estimate. Delivered, the arrival is the delivery.
ETA_ERROR = {"received": (4, 6), "preparing": (2, 3), "on_the_way": (-1, 1)}
ETA_REQUOTE = 0.5
_WAY, _DOOR = STAGES[2][1], STAGES[-1][1]
# When, in steps after placing, the view of an order changes: a stage or a new quote.
QUOTE_MARKS = sorted({st[1] for st in STAGES}
                     | {_WAY + k * ETA_REQUOTE for k in range(1, int((_DOOR - _WAY) / ETA_REQUOTE))})
RIDERS = ["Sam", "Alex", "Jordan", "Riley"]
# An order can be cancelled until a rider picks it up.
CANCELLABLE = {"received", "preparing"}
DAY = 24 * 3600

# Sandbox cards for the payment window, as a payment sandbox would accept them.
DECLINED_CARDS = {"4000000000000002"}


class ShopError(Exception):
    """A request the shop refuses: an unknown product, an empty cart, a closed session."""


class OptionError(ShopError):
    """An option the product does not have: a size it is not sold in."""


# --- options and line keys ------------------------------------------------------
def default_options(p: dict) -> dict[str, str]:
    return {o["name"]: o["default"] for o in p.get("options", [])}


def resolve_options(p: dict, given: dict[str, str] | None = None) -> dict[str, str]:
    """The product's options with `given` applied over its defaults, in the product's
    order. A name or value the product does not have is refused, never guessed."""
    given = {k: v for k, v in (given or {}).items() if v not in (None, "")}
    groups = {o["name"]: o for o in p.get("options", [])}
    for name, value in given.items():
        if name not in groups:
            raise OptionError(f"{p['name']} has no option '{name}'")
        if value not in {v["id"] for v in groups[name]["values"]}:
            ids = ", ".join(v["id"] for v in groups[name]["values"])
            raise OptionError(f"{p['name']} has no {name} '{value}' (it has {ids})")
    return {name: str(given.get(name) or o["default"]) for name, o in groups.items()}


def option_value(p: dict, name: str, value_id: str) -> dict:
    group = next(o for o in p["options"] if o["name"] == name)
    return next(v for v in group["values"] if v["id"] == value_id)


def unit_price(p: dict, options: dict[str, str]) -> float:
    return round(p["price"] + sum(option_value(p, k, v)["price_delta"] for k, v in options.items()), 2)


def options_label(p: dict, options: dict[str, str]) -> str:
    """The chosen options in words: `Triple`."""
    return ", ".join(option_value(p, k, v)["label"] for k, v in options.items())


def options_query(options: dict[str, str]) -> str:
    """`&size=triple`: how a stepper or a link names a line's options after its id."""
    return "".join(f"&{k}={v}" for k, v in options.items())


def line_key(product_id: str, options: dict[str, str]) -> str:
    return product_id + ("?" + options_query(options)[1:] if options else "")


def split_key(key: str) -> tuple[str, dict[str, str]]:
    pid, _, query = key.partition("?")
    return pid, dict(pair.split("=", 1) for pair in query.split("&") if pair)


@dataclass
class CheckoutSession:
    id: str
    lines: list[dict]
    subtotal: float
    delivery: float
    total: float
    item_count: int
    status: str = "open"  # open | paid | cancelled | failed
    order_id: Optional[str] = None
    error: Optional[str] = None
    created_at: float = 0.0


@dataclass
class Order:
    id: str
    lines: list[dict]
    subtotal: float
    delivery: float
    total: float
    item_count: int
    card: str  # "Visa •••• 4242": the only card detail the shop keeps
    rider: str
    placed_at: float
    cancelled_at: Optional[float] = None
    cancel_reason: Optional[str] = None


@dataclass
class Shop:
    clock: Callable[[], float] = time.time
    products: dict[str, dict] = field(default_factory=lambda: {p["id"]: p for p in DATA["products"]})
    cart: dict[str, int] = field(default_factory=dict)  # line key -> quantity; insertion order = order added
    likes: set[str] = field(default_factory=set)
    sessions: dict[str, CheckoutSession] = field(default_factory=dict)
    orders: dict[str, Order] = field(default_factory=dict)
    _next_order: int = 1042
    with_history: bool = True  # the demo customer's past orders (data/past_orders.json)
    # Told an order's id when it changes other than by the clock (a cancel), as a real order
    # service would notify its subscribers; the stages themselves follow the clock.
    listeners: list[Callable[[str], None]] = field(default_factory=list)
    customer: dict = field(default_factory=lambda: {k: v for k, v in CUSTOMER.items() if k != "note"})
    eta_seed: str = ""  # with the order's id, picks each arrival quote's error; a test sets it

    def __post_init__(self) -> None:
        if self.with_history:
            self._load_history()

    def _load_history(self) -> None:
        now = datetime.fromtimestamp(self.clock())
        for h in HISTORY:
            hour, minute = (int(x) for x in h["hour"].split(":"))
            placed = now.replace(hour=hour, minute=minute, second=0, microsecond=0).timestamp() - h["days_ago"] * DAY
            lines = self._lines(h["items"])
            subtotal = round(sum(l["line_total"] for l in lines), 2)
            delivery = 0.0 if subtotal >= FREE_DELIVERY_OVER else DELIVERY_FEE
            cancelled = h.get("cancelled")
            self.orders[h["id"]] = Order(
                id=h["id"], lines=lines, subtotal=subtotal, delivery=delivery, total=round(subtotal + delivery, 2),
                item_count=sum(l["quantity"] for l in lines), card=h["card"], rider=h["rider"], placed_at=placed,
                cancelled_at=placed + cancelled["after_minutes"] * 60 if cancelled else None,
                cancel_reason=cancelled["reason"] if cancelled else None,
            )

    # --- catalog ---------------------------------------------------------------
    def product(self, product_id: str) -> dict:
        try:
            return self.products[product_id]
        except KeyError:
            raise ShopError(f"unknown product '{product_id}'") from None

    def find(
        self,
        query: str | None = None,
        category: str | None = None,
        max_price: float | None = None,
        label: str | None = None,
        spicy: bool | None = None,
        vegetarian: bool | None = None,
        liked: bool | None = None,
        sort: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        items = list(self.products.values())
        if query:
            q = query.lower()
            items = [p for p in items if q in p["name"].lower() or q in p["description"].lower()
                     or any(q in i.lower() for i in p["ingredients"])]
        if category:
            items = [p for p in items if p["category"] == category]
        if max_price is not None:
            items = [p for p in items if p["price"] <= max_price]
        if label:
            items = [p for p in items if (p["label"] or "").lower().endswith(label.lower())]
        if spicy is not None:
            items = [p for p in items if p["spicy"] == spicy]
        if vegetarian is not None:
            items = [p for p in items if p["vegetarian"] == vegetarian]
        if liked is not None:
            items = [p for p in items if (p["id"] in self.likes) == liked]
        if sort == "popular":
            items.sort(key=lambda p: -p["reviews"])
        elif sort == "rating":
            items.sort(key=lambda p: -p["rating"])
        elif sort == "price":
            items.sort(key=lambda p: p["price"])
        return items[:limit] if limit else items

    def recommended(self, n: int = 3) -> list[dict]:
        """The home page's picks: from the order history when there is one (the usual
        burger, then new ones to try), else liked burgers, the kitchen's picks, the best rated."""
        recs = self.recommendations()
        picked = [self.products[r["id"]] for r in recs["order_again"] if self.products[r["id"]]["category"] == "burgers"][:1]
        picked += [self.products[r["id"]] for r in recs["try_next"] if self.products[r["id"]]["category"] == "burgers"]
        burgers = [p for p in self.products.values() if p["category"] == "burgers" and p not in picked]
        burgers.sort(key=lambda p: (p["id"] not in self.likes, not (p["label"] or "").endswith("Chef's Pick"), -p["rating"]))
        return (picked + burgers)[:n]

    # --- history and recommendations ---------------------------------------------
    def ordered_counts(self) -> dict[str, dict]:
        """How often each product was in a delivered or running order, and when last."""
        counts: dict[str, dict] = {}
        for o in self.orders.values():
            if o.cancelled_at is not None:
                continue
            for line in o.lines:
                c = counts.setdefault(line["product_id"], {"times": 0, "quantity": 0, "last": 0.0})
                c["times"] += 1
                c["quantity"] += line["quantity"]
                c["last"] = max(c["last"], o.placed_at)
        return counts

    def recommendations(self, n: int = 3) -> dict:
        """What to suggest from the order history: the usual items to order again, and
        products never ordered that are close to them, each with a reason in words."""
        counts = self.ordered_counts()
        again = sorted(counts.items(), key=lambda kv: (-kv[1]["times"], -kv[1]["last"]))
        order_again = [{"id": pid, "name": self.products[pid]["name"], "times": c["times"],
                        "last_ordered": date_label(c["last"], self.clock()),
                        "reason": f"You ordered it {c['times']} time{'s' if c['times'] > 1 else ''}"}
                       for pid, c in again[:n]]
        usual: dict[str, dict] = {}  # the most-ordered product of each category
        for pid, _c in again:
            usual.setdefault(self.products[pid]["category"], self.products[pid])
        fresh = [p for p in self.products.values() if p["id"] not in counts and p["category"] in (usual or {"burgers": None})]

        def score(p: dict) -> tuple:
            label = p["label"] or ""
            return (not label.endswith("New") and not label.endswith("Chef's Pick"), p["id"] not in self.likes, -p["rating"])

        fresh.sort(key=score)
        LABEL_WORDS = {"New": "New on the menu", "Offer": "On offer today", "Limited edition": "A limited edition",
                       "Chef's Pick": "The chef's pick"}
        try_next = []
        for p in fresh[:n]:
            label = (p["label"] or "").split(" ", 1)[-1]
            head = LABEL_WORDS.get(label, f"Rated {p['rating']}")
            near = usual.get(p["category"])
            tail = f", if you like the {near['name']}" if near else ""
            try_next.append({"id": p["id"], "name": p["name"], "reason": head + tail})
        spent = [o.total for o in self.orders.values() if o.cancelled_at is None]
        return {
            "order_again": order_again,
            "try_next": try_next,
            "orders_placed": len(spent),
            "usual_spend": money(sum(spent) / len(spent)) if spent else None,
        }

    def home_context(self) -> dict:
        """What a greeting can be made of, in one call: who, when, their usual, their
        orders, what is new and what is on offer."""
        now = datetime.fromtimestamp(self.clock())
        hour = now.hour
        part = ("late night" if hour < 5 else "morning" if hour < 11 else "lunchtime" if hour < 15
                else "afternoon" if hour < 18 else "evening" if hour < 22 else "late night")
        recs = self.recommendations()
        last = next((o for o in self.history() if o.cancelled_at is None), None)
        running = self.running_order()

        def brief(o: Order) -> dict:
            v = self.order_view(o)
            return {"order_id": o.id, "placed": v["placed"], "status": v["status"], "total": money(o.total),
                    "items": [f"{l['quantity']} × {l['name']} ({l['product_id']})" for l in o.lines],
                    "arrives": v["arrives"] if v["status"] not in ("delivered", "cancelled") else None}

        return {
            "now": {"weekday": now.strftime("%A"), "time": clock_time(self.clock()), "part_of_day": part},
            "usual": recs["order_again"],
            "try_next": recs["try_next"],
            "last_order": brief(last) if last else None,
            "running_order": brief(running) if running else None,
            "new_on_menu": [{"id": p["id"], "name": p["name"], "price": money(p["price"])}
                            for p in self.products.values() if (p["label"] or "").endswith("New")],
            "on_offer": [{"id": p["id"], "name": p["name"], "price": money(p["price"]), "was": money(p["was_price"])}
                         for p in self.deals()],
            "promotions": [{"id": x["id"], "kicker": x["kicker"], "title": x["title"], "deal": x["deal"]}
                           for x in self.promotions()],
            "liked": sorted(self.likes),
            "cart_items": sum(self.cart.values()),
        }

    def history(self) -> list[Order]:
        """Every order, newest first."""
        return sorted(self.orders.values(), key=lambda o: -o.placed_at)

    def deals(self) -> list[dict]:
        return [p for p in self.products.values() if p["was_price"]]

    def pairs_with(self, product_id: str, n: int = 2) -> list[dict]:
        p = self.product(product_id)
        wanted = ["sides", "shakes"] if p["category"] in ("burgers", "combos") else ["burgers"]
        picks = [x for x in self.products.values() if x["category"] in wanted and x["id"] != product_id]
        picks.sort(key=lambda x: -x["reviews"])
        return picks[:n]

    def promotions(self) -> list[dict]:
        return DATA["promotions"]

    def headline(self) -> dict:
        return DATA["headline"]

    # --- likes -----------------------------------------------------------------
    def set_like(self, product_id: str, liked: bool) -> bool:
        self.product(product_id)
        (self.likes.add if liked else self.likes.discard)(product_id)
        return liked

    # --- cart ------------------------------------------------------------------
    def options(self, product_id: str, given: dict[str, str] | None = None) -> dict[str, str]:
        """The line's options: `given` over the product's defaults (OptionError if unknown)."""
        return resolve_options(self.product(product_id), given)

    def qty(self, product_id: str, options: dict[str, str] | None = None) -> int:
        """How many of that line are in the cart: the product with these options, or its defaults."""
        return self.cart.get(line_key(product_id, self.options(product_id, options)), 0)

    def product_qty(self, product_id: str) -> int:
        """How many of the product are in the cart, every size added up."""
        return sum(q for key, q in self.cart.items() if split_key(key)[0] == product_id)

    def set_qty(self, product_id: str, qty: int, options: dict[str, str] | None = None) -> int:
        key = line_key(product_id, self.options(product_id, options))
        qty = max(0, min(MAX_QTY, int(qty)))
        if qty == 0:
            self.cart.pop(key, None)
        else:
            self.cart[key] = qty
        return qty

    def add(self, product_id: str, delta: int = 1, options: dict[str, str] | None = None) -> int:
        return self.set_qty(product_id, self.qty(product_id, options) + delta, options)

    def clear_cart(self) -> None:
        self.cart.clear()

    def _lines(self, items: dict[str, int]) -> list[dict]:
        """Lines from line keys (a bare product id is its default options)."""
        lines = []
        for key, qty in items.items():
            pid, given = split_key(key)
            p = self.products[pid]
            options = resolve_options(p, given)
            price = unit_price(p, options)
            lines.append({"key": line_key(pid, options), "product_id": pid, "name": p["name"],
                          "category": p["category"], "options": options, "options_label": options_label(p, options),
                          "default_options": options == default_options(p), "unit_price": price,
                          "quantity": qty, "line_total": round(price * qty, 2), "image": p["image"]})
        return lines

    def cart_view(self) -> dict:
        lines = self._lines(self.cart)
        subtotal = round(sum(line["line_total"] for line in lines), 2)
        delivery = 0.0 if subtotal == 0 or subtotal >= FREE_DELIVERY_OVER else DELIVERY_FEE
        return {
            "lines": lines,
            "item_count": sum(line["quantity"] for line in lines),
            "subtotal": subtotal,
            "delivery": delivery,
            "total": round(subtotal + delivery, 2),
            "free_delivery_over": FREE_DELIVERY_OVER,
        }

    # --- checkout --------------------------------------------------------------
    def create_checkout(self) -> CheckoutSession:
        """Opens a payment session for the cart as it is now; its amount never changes."""
        cart = self.cart_view()
        if not cart["lines"]:
            raise ShopError("the cart is empty")
        for s in self.sessions.values():  # one open session at a time
            if s.status == "open":
                s.status = "cancelled"
        s = CheckoutSession(
            id=f"cs_{uuid.uuid4().hex[:12]}", lines=cart["lines"], subtotal=cart["subtotal"],
            delivery=cart["delivery"], total=cart["total"], item_count=cart["item_count"], created_at=self.clock(),
        )
        self.sessions[s.id] = s
        return s

    def session(self, session_id: str) -> CheckoutSession:
        try:
            return self.sessions[session_id]
        except KeyError:
            raise ShopError(f"unknown checkout session '{session_id}'") from None

    def pay(self, session_id: str, card_number: str, expiry: str, cvc: str, name: str = "") -> CheckoutSession:
        """The sandbox payment: any well-formed card pays, except the decline test card."""
        s = self.session(session_id)
        if s.status != "open":
            raise ShopError(f"checkout session is {s.status}")
        digits = "".join(ch for ch in card_number if ch.isdigit())
        if not (13 <= len(digits) <= 19) or not cvc.isdigit() or len(cvc) not in (3, 4) or not _valid_expiry(expiry):
            raise ShopError("check the card details")
        if digits in DECLINED_CARDS:
            s.status, s.error = "failed", "card declined"
            return s
        brand = {"4": "Visa", "5": "Mastercard", "3": "Amex"}.get(digits[0], "Card")
        order = Order(
            id=f"BS-{self._next_order}", lines=s.lines, subtotal=s.subtotal, delivery=s.delivery, total=s.total,
            item_count=s.item_count, card=f"{brand} •••• {digits[-4:]}",
            rider=RIDERS[self._next_order % len(RIDERS)], placed_at=self.clock(),
        )
        self._next_order += 1
        self.orders[order.id] = order
        s.status, s.order_id = "paid", order.id
        self.clear_cart()
        return s

    def cancel_checkout(self, session_id: str) -> CheckoutSession:
        s = self.session(session_id)
        if s.status == "open":
            s.status = "cancelled"
        return s

    # --- orders ----------------------------------------------------------------
    def order(self, order_id: str | None = None) -> Order:
        if order_id:
            try:
                return self.orders[order_id]
            except KeyError:
                raise ShopError(f"unknown order '{order_id}'") from None
        if not self.orders:
            raise ShopError("no orders yet")
        return list(self.orders.values())[-1]

    def cancel_order(self, order_id: str, reason: str = "Cancelled by the customer") -> Order:
        """Cancels an order the kitchen has not handed to a rider yet; the payment is
        refunded to the card it was paid with (mock)."""
        o = self.order(order_id)
        status = self.order_view(o)["status"]
        if status == "cancelled":
            raise ShopError(f"order {o.id} is already cancelled")
        if status not in CANCELLABLE:
            raise ShopError(f"order {o.id} is {status.replace('_', ' ')} and can no longer be cancelled")
        o.cancelled_at, o.cancel_reason = self.clock(), reason
        for tell in self.listeners:
            tell(o.id)
        return o

    def can_cancel(self, o: Order) -> bool:
        return self.order_view(o)["status"] in CANCELLABLE

    def running_order(self) -> Order | None:
        for o in self.history():
            if self.order_view(o)["status"] not in ("delivered", "cancelled"):
                return o
        return None

    def next_change(self, order: Order) -> float | None:
        """Seconds until the order reaches its next stage or arrival quote; None once delivered
        or cancelled."""
        if order.cancelled_at is not None:
            return None
        ahead = [m for m in QUOTE_MARKS if order.placed_at + m * STAGE_SECONDS > self.clock()]
        return order.placed_at + ahead[0] * STAGE_SECONDS - self.clock() if ahead else None

    def arrival(self, order: Order, now: float) -> float:
        """When the order arrives, as known at *now*: the delivery once it is past, else the
        latest quote (ETA_ERROR), never earlier than *now*."""
        door = order.placed_at + _DOOR * STAGE_SECONDS
        elapsed = (now - order.placed_at) / STAGE_SECONDS
        if elapsed >= _DOOR:
            return door
        mark = max(m for m in QUOTE_MARKS if m <= elapsed)
        stage = [st[0] for st in STAGES if st[1] <= mark][-1]
        minutes = random.Random(f"{self.eta_seed}:{order.id}:{mark}").randint(*ETA_ERROR[stage])
        return max(door + minutes * 60, now)

    def order_view(self, order: Order) -> dict:
        now = self.clock() if order.cancelled_at is None else order.cancelled_at
        elapsed_stages = (now - order.placed_at) / STAGE_SECONDS
        reached = [st for st in STAGES if elapsed_stages >= st[1]]
        current = reached[-1]
        values = {"card": order.card, "items": order.item_count, "rider": order.rider}
        today = self.clock()

        def at(stage_start: int) -> str:
            return clock_time(order.placed_at + stage_start * STAGE_SECONDS)

        updates = [{"status": st[0], "badge": st[3], "title": st[5].format(**values),
                    "detail": st[6].format(**values), "time": at(st[1]), "done": True} for st in reversed(reached)]
        arrives = clock_time(self.arrival(order, now))
        upcoming = [{"status": st[0], "badge": st[3], "title": st[4], "done": False,
                     "time": f"about {arrives if st is STAGES[-1] else at(st[1])}"}
                    for st in STAGES if st not in reached]
        status, badge, headline, progress = current[0], current[3], current[4], current[2]
        if order.cancelled_at is not None:
            status, badge, headline, progress = "cancelled", "❌", "Order cancelled", None
            updates.insert(0, {"status": "cancelled", "badge": "❌", "title": "Order cancelled",
                               "detail": f"{order.cancel_reason}. Refunded to {order.card}",
                               "time": clock_time(order.cancelled_at), "done": True})
            upcoming = []
        return {
            "order_id": order.id,
            "status": status,
            "badge": badge,
            "headline": headline,
            "progress": progress,
            "placed": date_label(order.placed_at, today),
            "placed_time": clock_time(order.placed_at),
            "cancel_reason": order.cancel_reason,
            "can_cancel": order.cancelled_at is None and current[0] in CANCELLABLE,
            "arrives": arrives,
            "rider": order.rider,
            "card": order.card,
            "item_count": order.item_count,
            "total": order.total,
            "lines": [{"product_id": l["product_id"], "name": l["name"], "quantity": l["quantity"],
                       "options": l["options"], "options_label": l["options_label"],
                       "default_options": l["default_options"], "line_total": l["line_total"]} for l in order.lines],
            "subtotal": order.subtotal,
            "delivery": order.delivery,
            "updates": updates,
            "upcoming": upcoming,
        }


def _valid_expiry(expiry: str) -> bool:
    """MM/YY or MM/YYYY, with or without the slash: a phone's number pad has no `/` key."""
    text = expiry.replace(" ", "")
    month, _, year = text.partition("/") if "/" in text else (text[:2], "", text[2:])
    return month.isdigit() and year.isdigit() and 1 <= int(month) <= 12 and len(year) in (2, 4)


def clock_time(ts: float) -> str:
    """7:42 PM, in the server's local time."""
    return datetime.fromtimestamp(ts).strftime("%I:%M %p").lstrip("0")


def date_label(ts: float, now: float) -> str:
    """Today, Yesterday, or the date: Oct 31."""
    day, today = datetime.fromtimestamp(ts).date(), datetime.fromtimestamp(now).date()
    if day == today:
        return "Today"
    if (today - day).days == 1:
        return "Yesterday"
    return datetime.fromtimestamp(ts).strftime("%b %-d")


def money(value: float) -> str:
    return f"${value:,.2f}"
