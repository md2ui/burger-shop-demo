"""
tools.py

Everything the agent can see and call, and how its replies are written.

The tools are built to cost the agent as little as possible:

  - Pages are includes, not tokens. A reply may hold lines such as `{{home}}`, `{{cart}}`
    or `{{cards classic-smash bacon-bbq}}`; md2ui (pages.registry) swaps each one for the page's
    Markdown from live shop state before the window sees it. Showing the cart is one
    line, with no tool call.
  - Taps on ➕ ➖ 🤍 ❤️ and the taps that only choose a page (a category tab, View cart,
    My orders) never reach the agent: md2ui hands them to the shop's handlers (main.py),
    which change the cart or the likes and redraw the includes on the page on screen, or
    show a page of includes. Its digest of them is handed to the agent as app notes at the
    start of its next turn, with the cart as it is now.
  - Few tools, each returning in one call what a reply needs, with ids that go straight
    into an include.
  - Burgers and shakes come in sizes; a cart line is a product at one size, and the cart
    tools take the size beside the id. The product page is md2ui's form: its size and
    quantity are held on the page until one commit press, which reaches the agent as md2ui's
    own sentence (`Verified.agent_text`).

open_checkout is a CLIENT tool: the loop pauses while the app's payment window is
open (the app learns of it from /api/state, or the HTTP answer), and its result is built here from the checkout session on the server (the window's
own claim about what happened is never trusted).
"""

from __future__ import annotations

import json
from datetime import date
from functools import cache
from pathlib import Path
from typing import Any

import pages
from shop import Shop, ShopError, money, unit_price

MD2UI_NOTES = Path(__file__).with_name("md2ui_notes")


@cache
def md2ui_notes() -> str:
    """md2ui's core authoring note and this theme's meanings and patterns, written by
    scripts/sync_md2ui.sh from the md2ui checkout and md2ui_theme/."""
    parts = []
    for name in ("core.md", "theme.md"):
        path = MD2UI_NOTES / name
        if path.exists():
            parts.append(path.read_text())
    return "\n\n".join(parts) or "(md2ui notes missing: run scripts/sync_md2ui.sh)"


def system_prompt(today: date) -> str:
    return f"""You are the assistant inside the Burger Shop web app. You help one customer browse the menu, fill their cart, pay and follow their order. Reply in the customer's language; prices are in US dollars.

How your replies are shown:
- The app renders each reply with md2ui in the window between its own header and footer: every reply is one md2ui page, written as md2ui Markdown by the notes below. The footer already shows the cart's total and item count, a View cart button and a Checkout button; never repeat those as a bar of your own.
- The shop's pages are includes. A line holding only an include is replaced by that page's Markdown, drawn from the shop's live data, before the customer sees it. Use them for every page they cover, instead of writing the page yourself:

{pages.INCLUDES_HELP}

  An include stands alone on its line, with a blank line before and after. You can put your own md2ui Markdown around includes: a `# ` title or one short sentence above `{{{{cards …}}}}`, a section of your own under `{{{{cart}}}}`. For anything no include covers (a question about ingredients, allergens, a comparison, a recommendation with reasons), write the page yourself, following the theme's patterns and spellings; include product cards or rows by id rather than retyping them.
- When an include is the whole answer, your reply is the include line alone: no sentence before it ("Here's your cart", "The home page is ready"). The page says it already. Add words only when they tell the customer something the page does not: an answer to their question, why you picked these products.
- The app shows the home page by itself (the first visit, Home, the logo, Back to home): it is written once a session and saved, and its orders, cart and recommendations stay live. When the customer only asks in words to go home, reply `{{{{home-saved}}}}` alone. Write a new home only when it should change: they ask for something different on it, or something you know makes it stale. What you write becomes the session's saved home. When the message carries a [Home context], write from it; otherwise call get_home_context once. Then reply with your own band and three cards, about products, over the shop's live sections:

  {{{{headline greeting="…" line="…" kicker="…" image=<product id> cta="…" action=<product action> cta2="…" action2=<product action>}}}}

  {{{{offer product=<id> kicker="…" title="…" chip="…" cta="…"}}}}
  {{{{offer product=<id> …}}}}
  {{{{offer promo=<id> …}}}}

  {{{{home-rest note="…"}}}}

  - The band and the three coloured cards are for products and their calls to action only: what to eat, what is new, what is on offer. Their actions are product, cart-add, offer, offers, catalog or picks. Orders never go there: no order status, tracking, order number or reorder in the band or the cards.
  - Orders have their own section, which `{{{{home-rest}}}}` draws under the cards: the running order's status card, the last order, and a panel suggesting to order the usual again. Your `note=` is that panel's line, written fresh: a short question or nudge about their orders, at most eight words ("Same again for Friday night?", "Your fries are on the way, want a shake?").
  - The greeting is warm and fits the moment: the part of the day, the weekday, their taste, something new. It never names the customer: the shop does not know their name. At most eight words, e.g. "Monday night, burger night?". The line under it is one sentence, at most twenty words, about food: their usual, what is new, what is on offer. The kicker is a few words above the greeting, or left out.
  - Never the same words twice in a conversation: vary the greeting, the line, the cards and the note each time home is shown.
  - The three cards are three different reasons to tap, in any order: one of their usual products, something new for them (try_next or new_on_menu), and a live promotion or offer. Kicker two or three words, title at most five words, chip one fact (a price, a label, a deal, "Ordered 3 times"), cta one or two words.
  - Only ids, prices and facts from the home context. Never invent urgency or a claim the context does not hold: no "tonight only", "last chance", "selling fast" or end dates; promotions have no end date. A card's default action is the product's cart-add (the app adds it at once) or the promotion's offer; `action=product?id=<id>` opens the product instead.
  - `{{{{home}}}}` is only the fallback when get_home_context fails.
- Some taps never reach you: the shop answers them itself and the window shows its page at once. A category tab or Keep shopping shows `{{{{menu …}}}}`, View cart `{{{{cart}}}}`, My orders `{{{{orders}}}}`, Home and the logo the saved home; ➕ ➖ 🤍 ❤️ change the cart or the likes on the page shown. You hear each one in your next message's app notes (`… the backend showed {{{{menu category=sides}}}}`, `… the backend answered it, redrawing {{{{cart}}}}`), and the window already shows what they say. The steppers and hearts cost no turn, so they stay buttons on every page (cards, rows, the cart, the product page's heart and its "Goes well with" rows): md2ui's advice to write a count instead of ➖ ➕ buttons is for steppers that would come back to you, and these never do.
- Every other tap reaches you as md2ui's sentence: `User chose "<label>": <action> {{<params>}} (message <id>)`. Treat it as the customer's request. Most need no tool call: a product's name is `{{{{product …}}}}`, "Track order" is `{{{{order …}}}}`, a filter the shop does not answer (`catalog {{filter: spicy}}`) is `{{{{menu …}}}}` with your filters. A message the customer typed reaches you as their own words.
- Sizes: burgers come Single, Double or Triple, shakes Regular or Large; sides and combos have none. Each product's listed price is its default size's (`default_size` in find_products and get_product; get_product lists every size with its price). A cart line is a product at one size: two Classic Smash Double and one Triple are two lines. A stepper or link names its line as `agent:cart-add?id=classic-smash&size=triple`; with no `size` it means the default size, as on cards, rows and the catalog. The cart's rows always name their size. On the product page the size and the quantity are the form's (below); `{{{{product <id> size=<size>}}}}` opens it at a size. When the customer asks in words for a size ("a large strawberry shake"), pass `size` to update_cart; without one, the default size is added.
- A message may start with [App notes], what the customer did in the app since your last reply (cart changes, likes, pages the shop showed, a payment from the footer), and then md2ui's issues with your last page, if it found any: fix an error or a warning in your next page. It is server state, true as written. The page on screen already shows those numbers.

Tools:
- find_products, get_product, get_cart and get_order answer questions and give you the ids for includes. You do not need them just to show a page an include draws.
- update_cart sets quantities when the customer asks in words ("add two Classic Smash", "two triple Classic Smash", "remove the fries", "order again"), one cart line (an id and a size) per item. Reply with `{{{{cart}}}}` or a short confirmation page afterwards.
- The product page is md2ui's form (pattern `product-details`): `{{{{product <id>}}}}` draws its size as a choice and its quantity as a count, held on the page until the one Add to cart press (`md2ui.commit=1`) carries them in one turn. Choosing a size or counting sends you nothing; only the press does. It reads as md2ui hands it over, e.g. `User chose "Add to cart": add {{id: classic-smash, size: double}}, with size: "Triple", "Quantity" at 4`: the button's label, its action and parameters, then the values the customer changed before pressing (a choice as `name: "Option"`, a count as `"Label" at N`, a box as `"Label" ticked`; `with no change` when they changed none). A value it leaves out is as the page drew it: the size in the button's parameters (none for a product without sizes), a quantity of 1. That press is: update_cart with items [{{"id": "classic-smash", "size": "triple", "quantity": 4}}] and add=true (a chosen size by its id: the option's label in lower case), then `{{{{cart}}}}` or a short confirmation. A press with a quantity of 0 adds nothing: say so in one sentence over `{{{{product <id>}}}}`. Write a form of your own in the same shape: the label on its own line above its options, ` | ` between the options, `Quantity: ➖ [1/9] ➕`, one commit button.
- open_checkout opens the app's secure payment window. Call it when the customer asks in words to pay ("let's pay", "check me out"); a Checkout or Pay button opens the window by itself and you hear the outcome in your app notes. Your reply while it is open is not needed: when the window closes you get its outcome. Paid: reply with `{{{{success}}}}`. Cancelled or failed: one short sentence and `{{{{cart}}}}`. Never ask for or mention card numbers; payment is the window's.
- Past orders and recommendations: "my orders" is `{{{{orders}}}}`; "what should I get?" or "something new" is `{{{{picks}}}}`, or `get_recommendations` when you want to say why in your own words around `{{{{cards …}}}}`. "Order again" is `reorder`, then `{{{{cart}}}}`.
- Cancelling: a tap on Cancel order (agent:cancel-order) or "cancel my order" in words is answered with `{{{{cancel <order id>}}}}`, the question sheet. Call cancel_order only when the customer confirms there (agent:confirm-cancel) or says it plainly again, then show `{{{{order <order id>}}}}`. Only an order still received or preparing can be cancelled; if cancel_order says it can't, say why in one sentence and show `{{{{order <order id>}}}}`.
- Never invent products, prices, offers, times or order states: every one comes from a tool or an include.

About the notes below: there is no guide tool. Where they say `guide("includes")`, read the include table above; where they say `guide("theme")`, read "This theme" at their end; where they say `guide("theme/<name>")` or `patterns/<name>` for one of this theme's patterns, read its `## theme/<name>` section. The shared md2ui patterns and pages they mention are not available: use this theme's patterns, and write only the spellings the theme declares. The theme's patterns are what the includes draw, so read them to write a page of your own in the same shapes.

<md2ui_notes>
{md2ui_notes()}
</md2ui_notes>

Today's date is {today.isoformat()}."""


# ---------------------------------------------------------------------------
# Views: the agent's compact picture of the shop
# ---------------------------------------------------------------------------
def product_view(shop: Shop, p: dict, full: bool = False) -> dict:
    view = {
        "id": p["id"],
        "name": p["name"],
        "category": p["category"],
        "price": money(p["price"]),
        "was_price": money(p["was_price"]) if p["was_price"] else None,
        "label": p["label"],
        "rating": p["rating"],
        "reviews": p["reviews"],
        "delivery": pages.delivery_range(p),
        "calories": p["calories"],
        "spicy": p["spicy"],
        "vegetarian": p["vegetarian"],
        "in_cart": shop.product_qty(p["id"]),
        "liked": p["id"] in shop.likes,
    }
    for group in p.get("options", []):
        view[f"default_{group['name']}"] = group["default"]
        if full:
            view[f"{group['name']}s"] = [
                {"id": v["id"], "label": v["label"],
                 "price": money(unit_price(p, {group["name"]: v["id"]})),
                 "in_cart": shop.qty(p["id"], {group["name"]: v["id"]})} for v in group["values"]]
    if full:
        view["description"] = p["description"]
        view["ingredients"] = p["ingredients"]
        view["image"] = p["image"]
        view["goes_well_with"] = [x["id"] for x in shop.pairs_with(p["id"])]
    return view


def cart_summary(shop: Shop) -> dict:
    c = shop.cart_view()
    return {
        "items": [{"id": l["product_id"], "name": l["name"], **({"size": l["options"]["size"]} if "size" in l["options"] else {}),
                   "quantity": l["quantity"], "line_total": money(l["line_total"])} for l in c["lines"]],
        "item_count": c["item_count"],
        "subtotal": money(c["subtotal"]),
        "delivery": "Free" if c["delivery"] == 0 else money(c["delivery"]),
        "total": money(c["total"]),
        "free_delivery_over": money(c["free_delivery_over"]),
    }


def order_summary(shop: Shop, order_id: str | None = None) -> dict:
    v = shop.order_view(shop.order(order_id))
    out = {k: v[k] for k in ("order_id", "status", "headline", "progress", "placed", "arrives", "rider", "card",
                             "item_count", "can_cancel")}
    out["items"] = [f"{l['quantity']} × {l['name']}" + (f" {l['options_label']}" if l["options"] else "")
                    + f" ({l['product_id']})" for l in v["lines"]]
    out["total"] = money(v["total"])
    if v["cancel_reason"]:
        out["cancel_reason"] = v["cancel_reason"]
    return out


def orders_summary(shop: Shop, limit: int | None = None) -> dict:
    history = shop.history()[:limit] if limit else shop.history()
    rows = []
    for o in history:
        v = shop.order_view(o)
        rows.append({"order_id": o.id, "placed": v["placed"], "status": v["status"], "total": money(o.total),
                     "items": [f"{l['quantity']} × {l['name']}" for l in v["lines"]], "can_cancel": v["can_cancel"]})
    recs = shop.recommendations()
    return {"orders": rows, "orders_delivered": recs["orders_placed"], "usual_spend": recs["usual_spend"],
            "usual_items": [f"{r['name']} ({r['id']}): {r['reason'].lower()}" for r in recs["order_again"]]}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
BACKEND_TOOLS_SCHEMA: list[dict] = [
    {
        "name": "find_products",
        "description": (
            "Searches the menu. All filters are optional and combine. Returns each product's id, name, category, "
            "price (and was_price when on offer), label, rating, delivery time, calories, spicy/vegetarian, and how "
            "many are in the cart and whether the customer liked it. Show the result with `{{cards id …}}` or "
            "`{{menu …}}` with the same filters."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Words in the name, description or ingredients."},
                "category": {"type": "string", "enum": ["burgers", "combos", "sides", "shakes"]},
                "max_price": {"type": "number"},
                "label": {"type": "string", "enum": ["New", "Offer", "Limited edition", "Chef's Pick"]},
                "spicy": {"type": "boolean"},
                "vegetarian": {"type": "boolean"},
                "liked": {"type": "boolean", "description": "true: only the customer's favourites."},
                "sort": {"type": "string", "enum": ["popular", "rating", "price"]},
                "limit": {"type": "integer", "minimum": 1, "maximum": 20},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_product",
        "description": (
            "One product in full: description, ingredients, its sizes with their prices and how many of each are "
            "in the cart (burgers and shakes), and the ids of what goes well with it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_cart",
        "description": "The cart now: items with quantities and line totals, item count, subtotal, delivery, total.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "update_cart",
        "description": (
            "Sets the quantity of one or more cart lines in one call; quantity 0 removes the line. A line is a "
            "product at one size: give `size` for burgers (single, double, triple) and shakes (regular, large), or "
            "leave it out for the product's default size. Use add=true to add to what is there instead. Returns "
            "the cart afterwards, each item with its size."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "size": {"type": "string", "description": "The size's id; none: the default size."},
                            "quantity": {"type": "integer", "minimum": 0, "maximum": 20},
                        },
                        "required": ["id", "quantity"],
                        "additionalProperties": False,
                    },
                    "minItems": 1,
                },
                "add": {"type": "boolean", "description": "true: add the quantities to the cart's."},
                "clear_first": {"type": "boolean", "description": "true: empty the cart before (order again)."},
            },
            "required": ["items"],
            "additionalProperties": False,
        },
    },
    {
        "name": "set_like",
        "description": "Likes or unlikes a product when the customer asks in words.",
        "input_schema": {
            "type": "object",
            "properties": {"id": {"type": "string"}, "liked": {"type": "boolean"}},
            "required": ["id", "liked"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_home_context",
        "description": (
            "Everything a fresh home page is written from, in one call: the weekday, "
            "time and part of the day, their usual items, what to try next, their last and running orders, "
            "what is new and on offer, the promotions, their likes and how many items are in the cart."
        ),
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "get_orders",
        "description": (
            "The customer's order history, newest first: each order's id, date, status (received, preparing, "
            "on_the_way, delivered, cancelled), total, items and whether it can still be cancelled; with how many "
            "were delivered, the usual spend and the items they order most. Show it with `{{orders}}`."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 50}},
            "additionalProperties": False,
        },
    },
    {
        "name": "get_recommendations",
        "description": (
            "What to suggest from the order history, ready to show: order_again (the items they order most, how "
            "often, when last) and try_next (products they never ordered, close to those), each with a reason "
            "in words. Show them with `{{picks}}`, or `{{cards id …}}` / `{{rows id …}}` beside your own words."
        ),
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "get_order",
        "description": (
            "One order: status (received, preparing, on_the_way, delivered, cancelled), progress, date, arrival "
            "time, rider, items, total and can_cancel. Without order_id: the latest order. Show it with `{{order}}`."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "additionalProperties": False,
        },
    },
]


ORDER_TOOLS_SCHEMA: list[dict] = [
    {
        "name": "cancel_order",
        "description": (
            "Cancels an order and refunds it to the card it was paid with. Only orders still received or "
            "preparing can be cancelled; one on the way, delivered or already cancelled returns an error saying "
            "so. Call it only after the customer confirmed: they tapped the cancel sheet's Cancel order "
            "(agent:confirm-cancel) or said so plainly in words. Then show `{{order id}}`."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "reason": {"type": "string", "description": "The customer's reason in a few words, if they gave one."},
            },
            "required": ["order_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "reorder",
        "description": (
            "Puts the items of a past order in the cart, in one call: added to what is there, or replacing it with "
            "replace_cart=true. Products no longer on the menu are skipped. Returns the cart afterwards; show "
            "`{{cart}}`."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}, "replace_cart": {"type": "boolean"}},
            "required": ["order_id"],
            "additionalProperties": False,
        },
    },
]
BACKEND_TOOLS_SCHEMA += ORDER_TOOLS_SCHEMA


async def call_backend_tool(shop: Shop, name: str, args: dict) -> dict:
    """Runs one backend tool; errors come back as {"error": …} so the agent can recover."""
    try:
        match name:
            case "find_products":
                found = shop.find(**{k: v for k, v in args.items() if v not in (None, "")})
                return {"count": len(found), "products": [product_view(shop, p) for p in found]}
            case "get_product":
                return product_view(shop, shop.product(args["id"]), full=True)
            case "get_cart":
                return cart_summary(shop)
            case "update_cart":
                if args.get("clear_first"):
                    shop.clear_cart()
                for item in args["items"]:
                    options = {"size": item["size"]} if item.get("size") else None
                    if args.get("add"):
                        shop.add(item["id"], int(item["quantity"]), options)
                    else:
                        shop.set_qty(item["id"], int(item["quantity"]), options)
                return cart_summary(shop)
            case "set_like":
                shop.set_like(args["id"], bool(args["liked"]))
                return {"id": args["id"], "liked": bool(args["liked"])}
            case "get_order":
                return order_summary(shop, args.get("order_id"))
            case "get_home_context":
                return shop.home_context()
            case "get_orders":
                return orders_summary(shop, args.get("limit"))
            case "get_recommendations":
                return shop.recommendations()
            case "cancel_order":
                o = shop.cancel_order(args["order_id"], (args.get("reason") or "Cancelled by the customer").strip())
                return order_summary(shop, o.id) | {"refunded": money(o.total), "refunded_to": o.card}
            case "reorder":
                o = shop.order(args["order_id"])
                if args.get("replace_cart"):
                    shop.clear_cart()
                for line in o.lines:
                    if line["product_id"] in shop.products:
                        shop.add(line["product_id"], line["quantity"], line["options"])
                return cart_summary(shop)
            case _:
                return {"error": f"unknown tool {name}"}
    except ShopError as e:
        return {"error": str(e)}
    except (KeyError, TypeError, ValueError) as e:
        return {"error": f"invalid arguments: {e}"}


# ---------------------------------------------------------------------------
# Client tool: the payment window (the loop pauses on it)
# ---------------------------------------------------------------------------
CLIENT_TOOLS_SCHEMA: list[dict] = [
    {
        "name": "open_checkout",
        "description": (
            "Opens the app's secure payment window for the cart as it is now. The customer pays there; you never "
            "see card details. The result says paid (with the order), cancelled or failed."
        ),
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]
CLIENT_TOOL_NAMES = {t["name"] for t in CLIENT_TOOLS_SCHEMA}


def start_client_call(shop: Shop, name: str, args: dict) -> tuple[dict | None, str | None]:
    """Prepares a client tool before the loop pauses. Returns (what the app needs, error)."""
    if name == "open_checkout":
        try:
            s = shop.create_checkout()
        except ShopError as e:
            return None, str(e)
        return checkout_view(s), None
    return None, f"unknown client tool {name}"


def resolve_client_result(shop: Shop, name: str, client_input: dict) -> dict:
    """The tool result for a finished client action, from server state only. A window
    that closed without paying leaves its session cancelled."""
    if name == "open_checkout":
        s = shop.cancel_checkout(client_input["session_id"])
        if s.status == "paid":
            return {"status": "paid", "order": order_summary(shop, s.order_id)}
        if s.status == "failed":
            return {"status": "failed", "reason": s.error, "cart": cart_summary(shop)}
        return {"status": "cancelled", "cart": cart_summary(shop)}
    raise ValueError(f"unknown client tool {name}")


def checkout_view(s) -> dict:
    return {
        "session_id": s.id,
        "status": s.status,
        "lines": [{"name": l["name"], "quantity": l["quantity"], "line_total": money(l["line_total"])} for l in s.lines],
        "item_count": s.item_count,
        "subtotal": money(s.subtotal),
        "delivery": "Free" if s.delivery == 0 else money(s.delivery),
        "total": money(s.total),
        "order_id": s.order_id,
        "error": s.error,
    }


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)
