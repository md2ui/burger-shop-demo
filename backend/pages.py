"""
pages.py

md2ui Markdown for the shop's pages, built from live shop state in exactly the spellings
of the theme's patterns (md2ui_theme/patterns/). Two users:

  - The agent. Instead of writing a product card or a whole cart page token by token, it
    writes an include line such as `{{cart}}` or `{{cards classic-smash bacon-bbq}}` in
    its reply, and md2ui's `Conversation.send` swaps it for the Markdown before the window
    sees it (`registry`, ADR-612). The numbers are then always the shop's, and a page costs
    the agent a few tokens.
  - md2ui again after a tap: a handler (main.py) changes the cart or the likes and names
    the includes that changed, and md2ui draws their regions again.

A stepper names its cart line: `agent:cart-add?id=classic-smash&size=triple`. With no
`&size=` it means the product's default options, which is how cards, deal rows and the
catalog spell it; cart rows and the product page always spell their line's options.

Every function here returns Markdown; none of them changes the shop.
"""

from __future__ import annotations

import re
from collections.abc import Set as AbstractSet

from md2ui.includes import INCLUDE_LINE, Args, Includes, expand

from shop import Order, Shop, ShopError, money, options_query, unit_price

CATEGORY_TAG = {"burgers": "Burger", "combos": "Combo", "sides": "Side", "shakes": "Shake"}
CATEGORY_TABS = [("burgers", "🍔 Burgers"), ("combos", "🥡 Combos"), ("sides", "🍟 Sides"), ("shakes", "🥤 Shakes")]


# --- images -------------------------------------------------------------------
def img_card(p: dict) -> str:
    return f"{p['image']}?w=800&md2ui.aspect_ratio=5:4"


def img_row(p: dict, size: int = 64) -> str:
    return f"{p['image']}?w=200&md2ui.max_width={size}&md2ui.aspect_ratio=1:1&md2ui.corner_radius={size // 4}"


def img_hero(p: dict) -> str:
    return f"{p['image']}?w=1200&md2ui.aspect_ratio=1:1&md2ui.min_width=300&md2ui.corner_radius=28"


def alt(text: str) -> str:
    return text.replace("[", "").replace("]", "")


# --- the pieces the host patches ----------------------------------------------
def stepper(product_id: str, qty: int, options: dict[str, str] | None = None) -> str:
    """➖ N ➕ for one cart line; `options` spelled after the id, none for the defaults."""
    line = product_id + options_query(options or {})
    minus = f"__[➖](agent:cart-remove?id={line})__"
    if qty <= 0:
        minus = f"~~{minus}~~"
    return f"{minus} - **{qty}** - __[➕](agent:cart-add?id={line})__"


def like(product_id: str, liked: bool) -> str:
    return f"__[❤️](agent:unlike?id={product_id})__" if liked else f"__[🤍](agent:like?id={product_id})__"


def name_link(p: dict) -> str:
    return f"[`{p['name']}`](agent:product?id={p['id']})"


def chip(p: dict) -> str:
    return f"`{p['label']}`" if p["label"] else ""


def delivery_range(p: dict) -> str:
    low, high = p["delivery_min"]
    return f"{low}–{high} min"


# --- product cards and rows ----------------------------------------------------
def card(shop: Shop, p: dict) -> str:
    """One product card. The whole card opens the product; the heart and the stepper
    inside it stay their own buttons (the innermost target wins, md2ui ADR-404)."""
    top = f"{chip(p)} ... {like(p['id'], p['id'] in shop.likes)}".strip()
    price = (f"~~{money(p['was_price'])}~~ - " if p["was_price"] else "") + f"___{money(p['price'])}___"
    return "\n".join([
        "### ",
        "[",
        "![",
        top,
        "+++++",
        f"]({img_card(p)})",
        f"__{p['name']}__ ... {price}",
        f"**⭐** {p['rating']} _({p['reviews']:,})_ - **⏱️** _{delivery_range(p)}_",
        "---",
        f"_{p['calories']:,} kcal_ ... {stepper(p['id'], shop.qty(p['id']))}",
        f"](agent:product?id={p['id']})",
    ])


def cards(shop: Shop, products: list[dict]) -> str:
    return "\n\n".join(card(shop, p) for p in products) + "\n\n***"


def row(shop: Shop, p: dict) -> str:
    parts = [name_link(p)]
    if p["label"]:
        parts.append(chip(p))
    price = f"**{money(p['price'])}**" + (f" ~~{money(p['was_price'])}~~" if p["was_price"] else "")
    parts.append(price)
    return f"- ![{alt(p['name'])}]({img_row(p)}) - " + " : ".join(parts) + f" ... {stepper(p['id'], shop.qty(p['id']))}"


def rows(shop: Shop, products: list[dict]) -> str:
    return "\n".join(row(shop, p) for p in products)


def cart_row(shop: Shop, line: dict) -> str:
    """One cart line. A product sold in sizes shows its size as a second tag beside its kind,
    its name opens the product at that size, and its stepper spells the size."""
    p, options = shop.product(line["product_id"]), line["options"]
    name = f"[`{p['name']}`](agent:product?id={p['id']}{options_query(options)})"
    tags = f"`{CATEGORY_TAG[p['category']]}`" + (f" *`{line['options_label']}`*" if options else "")
    return (f"- ![{alt(p['name'])}]({img_row(p, 72)}) - {name} : {tags} : "
            f"**{money(line['line_total'])}** ... {stepper(p['id'], line['quantity'], options)}")


# --- summary panel ---------------------------------------------------------------
def delivery_value(cart: dict) -> str:
    return "`Free`" if cart["delivery"] == 0 else f"**{money(cart['delivery'])}**"


def summary(cart: dict, first: str = "Subtotal") -> str:
    head = "Subtotal" if first == "Subtotal" else f"Items ({cart['item_count']})"
    return "\n".join([
        "## {#summary-1}",
        "",
        f"{head} ... **{money(cart['subtotal'])}**",
        f"Delivery ... {delivery_value(cart)}",
        f"__Total__ ... ___{money(cart['total'])}___",
    ])


def items_label(n: int) -> str:
    return f"{n} item" if n == 1 else f"{n} items"


# --- whole pages ------------------------------------------------------------------
def words(text: str | None, limit: int = 120) -> str:
    """An agent's line set into a tier: one line, no Markdown of its own (an underscore
    or asterisk would end the tier early), at most `limit` characters."""
    text = re.sub(r"[_*`\[\]]", "", " ".join((text or "").split()))
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


# The band and the three coloured cards are for products and their calls to action; what is
# about orders (status, tracking, reordering) goes in the home page's orders section.
PRODUCT_ACTIONS = {"product", "cart-add", "offer", "offers", "catalog", "picks"}


def action_link(action: str | None, default: str, allowed: set[str] | None = None) -> str:
    """An agent: link from an include's `action=` (`product?id=smokehouse`, `agent:catalog`)."""
    a = (action or default).strip()
    if not re.fullmatch(r"(agent:)?[a-z][a-z0-9-]*(\?[A-Za-z0-9_.,%=&-]*)?", a):
        raise ShopError(f"not an action: {a!r}")
    a = a if a.startswith("agent:") else f"agent:{a}"
    name = a[len("agent:"):].split("?", 1)[0]
    if allowed is not None and name not in allowed:
        raise ShopError(f"`{name}` is not a product action: the band and the cards are for products and offers "
                        f"({', '.join(sorted(allowed))}); orders go in the orders section, `{{{{home-rest note=\"…\"}}}}`")
    return a


def headline(shop: Shop, greeting: str | None = None, line: str | None = None, kicker: str | None = None,
             image: str | None = None, cta: str | None = None, action: str | None = None,
             cta2: str | None = None, action2: str | None = None) -> str:
    """The home page's band. The agent writes its words each time (`greeting`, `line`,
    `kicker`, the buttons) and may pick the photo by product id; the shop's own words and
    rating are the fallback."""
    h = shop.headline()
    photo = shop.product(image)["image"] if image else h["image"]
    picture_alt = shop.product(image)["name"] if image else h["title"]
    top = (f"_{words(kicker, 80)}_" if kicker
           else f"**⭐** __{h['rating']}__ _from {h['happy_customers']} happy customers_")
    buttons = f"[{words(cta or 'Order now', 28)}]({action_link(action, 'catalog', PRODUCT_ACTIONS)})"
    if cta2 or not cta:
        buttons += f" *[{words(cta2 or 'See offers', 28)}]({action_link(action2, 'offers', PRODUCT_ACTIONS)})*"
    return "\n".join([
        "# {#headline-1}",
        "",
        "___",
        top,
        f"___{words(greeting, 70) or h['title']}___",
        words(line, 160) or h["subtitle"],
        "+++",
        buttons,
        "::: 1 >",
        f"![{alt(picture_alt)}]({photo}?w=900&md2ui.aspect_ratio=4:3&md2ui.min_width=260&md2ui.corner_radius=24)",
        ":::1",
        "___",
        "***",
    ])


def offer_card(shop: Shop, n: int, product: str | None = None, promo: str | None = None, kicker: str | None = None,
               title: str | None = None, chip: str | None = None, cta: str | None = None,
               action: str | None = None) -> str:
    """One of the three cards under the headline (`{#offer-N}`; the theme colours it by N).
    It features a product or a promotion, for its photo and default words and action; the
    agent's words replace any of them."""
    if product:
        p = shop.product(product)
        image, base = p["image"], {
            "kicker": (p["label"] or "").split(" ", 1)[-1] or "For you", "title": p["name"],
            "chip": f"{p['label']}" if p["label"] else money(p["price"]),
            "cta": "Add one", "action": f"cart-add?id={p['id']}",
        }
    else:
        promos = {x["id"]: x for x in shop.promotions()}
        pr = promos.get(promo or "") or shop.promotions()[(n - 1) % len(promos)]
        if promo and promo not in promos:
            raise ShopError(f"unknown promotion '{promo}'")
        image, base = pr["image"], {"kicker": pr["kicker"], "title": pr["title"], "chip": pr["deal"],
                                    "cta": pr["cta"], "action": f"offer?id={pr['id']}"}
    return "\n".join([
        f"### {{#offer-{n}}}",
        f"_{words(kicker, 40) or base['kicker']}_",
        f"___{words(title, 40) or base['title']}___",
        f"`{words(chip, 28) or base['chip']}`",
        f"**[{words(cta, 22) or base['cta']}]({action_link(action, base['action'], PRODUCT_ACTIONS)})**",
        "::: 1",
        f"![{alt(words(title, 40) or base['title'])}]({image}?w=600&md2ui.aspect_ratio=1:1&md2ui.max_width=88"
        "&md2ui.min_width=88&md2ui.corner_radius=44)",
        ":::0",
    ])


def offer_cards(shop: Shop) -> str:
    return "\n\n".join(offer_card(shop, i, promo=pr["id"]) for i, pr in enumerate(shop.promotions()[:3], 1)) + "\n\n***"


def track_card(shop: Shop, order: Order, level: str = "##") -> str:
    """The running order's card: its stage and arrival are slots and its bar is keyed, so
    the shop's feed moves all three while the card is on screen (order_feeds.py)."""
    v = shop.order_view(order)
    return "\n".join([
        f"{level} {{#track-1}}",
        "",
        f"*{v['badge']}* - {stage_chip(v)} : _Order {v['order_id']} • arriving around {arrival(v)}_ ... "
        f"**[Track order](agent:order-status?id={v['order_id']})**",
        f"{PROGRESS}: {v['progress']}%",
    ])


SUGGESTIONS = ("## What are you craving?\n\n... *[🔥 Something spicy](agent:catalog?filter=spicy)* "
               "*[🍔 Best sellers](agent:catalog?sort=popular)* *[🥤 Shakes](agent:catalog?category=shakes)* "
               "*[🍟 Sides](agent:catalog?category=sides)* *[🏷️ Under $10](agent:catalog?max_price=10)* ...")


def order_card(shop: Shop, o: Order, prefix: str = "Order") -> str:
    """One order as a tappable two-line card that opens it (one line in a link is a button)."""
    v = shop.order_view(o)
    names = ", ".join(l["name"] for l in v["lines"][:2]) + (" and more" if len(v["lines"]) > 2 else "")
    return "\n".join([
        "- [",
        f"  {STATUS_BADGE[v['status']]} - __{prefix} {v['order_id']}__ ... **{money(v['total'])}**",
        f"  _{v['placed']} • {items_label(v['item_count'])} • {names}_ ... {STATUS_CHIP[v['status']]}",
        f"  ](agent:order-status?id={v['order_id']})",
    ])


def orders_section(shop: Shop, note: str | None = None) -> str:
    """The home page's place for orders: the running one's status, the last one, and the
    suggestion to order again, in the agent's words (`note`). Empty with no orders."""
    history = shop.history()
    if not history:
        return ""
    running = shop.running_order()
    last = next((o for o in history if o is not running), None)
    delivered = next((o for o in history if shop.order_view(o)["status"] == "delivered"), None)
    out = ["## Your orders ... [`See all`](agent:orders)", ""]
    if running:
        out += [track_card(shop, running, "###"), "", "***", ""]
    if last:
        out += [order_card(shop, last, "Last order"), ""]
    if delivered:
        items = [l["name"] for l in delivered.lines]
        listed = ", ".join(items[:-1]) + f" and {items[-1]}" if len(items) > 1 else items[0]
        out += ["#### ", f"🔁 - __{words(note, 80) or 'Fancy your usual again?'}__ : _{listed}_ ... "
                f"_[Order again](agent:reorder?id={delivered.id})_", "", "***"]
    return "\n".join(out).rstrip()


def home_rest(shop: Shop, featured: AbstractSet[str] = frozenset(), note: str | None = None) -> str:
    """The home page under its band and cards: the running order, the recommendations,
    today's offers and the suggestions, from live data. Products the cards above already
    feature are left out, so nothing shows twice."""
    recommended = [p for p in shop.recommended(3 + len(featured)) if p["id"] not in featured][:3]
    shown = {p["id"] for p in recommended} | set(featured)
    parts = [section for section in [orders_section(shop, note)] if section]
    because = "\n\n_Picked from your past orders_" if shop.ordered_counts() else ""
    parts.append("## Recommended for you ... [`View more`](agent:catalog)" + because + "\n\n" + cards(shop, recommended)
                 + "\n\n... [View more burgers](agent:catalog?category=burgers) ...")
    deals = [p for p in shop.deals() if p["id"] not in shown]
    if deals:
        parts.append("## Today's offers\n\n" + rows(shop, deals))
    parts.append(SUGGESTIONS)
    return "\n\n".join(parts)


# The instant home's greeting: warm and of the moment, never a name (everyone trying the demo is
# the same customer).
SALUTE = {"morning": "Good morning, what are you craving?", "lunchtime": "Lunchtime! What are you craving?",
          "afternoon": "Good afternoon, what are you craving?", "evening": "Good evening, what are you craving?",
          "late night": "Late-night cravings? We're cooking."}


def instant_includes(shop: Shop) -> str:
    """The home page's include lines in the shop's own words, personalised from live data:
    what the window shows at once, while the fresh one is written."""
    c = shop.home_context()
    burgers = [u for u in c["usual"] if shop.product(u["id"])["category"] == "burgers"]
    usual = burgers[0] if burgers else (c["usual"][0] if c["usual"] else None)
    new = (c["try_next"] or c["new_on_menu"] or [None])[0]
    if usual and new:
        line = f"Your {usual['name']} is ready when you are, or try the new {new['name']}."
    else:
        line = shop.headline()["subtitle"]
    star = usual or new
    head = (f'{{{{headline greeting="{SALUTE[c["now"]["part_of_day"]]}" line="{line}"'
            + (f' image={star["id"]} cta="Add a {words(star["name"], 20)}" action=cart-add?id={star["id"]}'
               ' cta2="See the menu" action2=catalog' if star else "") + "}}")
    offers = []
    if usual:
        offers.append(f'{{{{offer product={usual["id"]} kicker="Your usual" chip="Ordered {usual["times"]} times"}}}}')
    if new:
        offers.append(f'{{{{offer product={new["id"]} kicker="New for you"}}}}')
    promos = [x for x in c["promotions"]]
    while len(offers) < 3 and promos:
        offers.append(f'{{{{offer promo={promos.pop(0)["id"]}}}}}')
    return "\n\n".join([head, "\n".join(offers), '{{home-rest}}'])


def home(shop: Shop) -> str:
    """The whole home page in the shop's own words: the fallback when the agent writes none."""
    return "\n\n".join([headline(shop), offer_cards(shop), home_rest(shop)])


def menu(shop: Shop, title: str | None = None, page: int = 1, per_page: int = 9, **filters) -> str:
    found = shop.find(**filters)
    if not found:
        return empty(shop, "search")
    start = (page - 1) * per_page
    shown = found[start:start + per_page]
    category = filters.get("category")
    tabs = [("**[All](agent:catalog)**" if not category else "***[All](agent:catalog)***")]
    for cid, label in CATEGORY_TABS:
        spell = "**" if cid == category else "***"
        tabs.append(f"{spell}[{label}](agent:catalog?category={cid}){spell}")
    heading = title or (dict(CATEGORY_TABS)[category].split(" ", 1)[1] if category else "Our menu")
    out = [f"# {heading}", "", f"_Showing {start + len(shown)} of {len(found)} items_", "",
           "... " + " ".join(tabs) + " ...", "", cards(shop, shown)]
    if start + len(shown) < len(found):
        out += ["", f"... [Show more](agent:catalog?page={page + 1}) ..."]
    return "\n".join(out)


def size_choice(p: dict, size: str) -> list[str]:
    """The product form's size picker: options of the choice `size`, the size shown chosen,
    held on the page until Add to cart. Empty for a product with no sizes."""
    group = next((o for o in p.get("options", []) if o["name"] == "size"), None)
    if group is None:
        return []
    buttons = [f"[{v['label']}](agent:size?id={p['id']}&size={v['id']}&md2ui.choice=size)" for v in group["values"]]
    buttons = [b if v["id"] == size else f"*{b}*" for b, v in zip(buttons, group["values"])]
    return [f"_{group['label']}_", " | ".join(buttons), ""]


def product_page(shop: Shop, product_id: str, size: str | None = None) -> str:
    """One product in full, at `size` (its default when none), as md2ui's form: a size choice,
    a quantity count and one Add to cart press that commits both. The press names the size
    shown, so a press that changed nothing still says which line it adds."""
    p = shop.product(product_id)
    options = shop.options(product_id, {"size": size} if size else None)
    delta = unit_price(p, options) - p["price"]
    price = (f"___{money(p['price'] + delta)}___"
             + (f" - ~~{money(p['was_price'] + delta)}~~" if p["was_price"] else ""))
    top = f"{chip(p)} ... {like(p['id'], p['id'] in shop.likes)}".strip()
    tags = " ".join(f"`{i}`" for i in p["ingredients"])
    pairs = shop.pairs_with(product_id)
    shown = options.get("size", "")
    buy = size_choice(p, shown) + ["Quantity: ➖ [1/9] ➕", "",
                                   f"[Add to cart](agent:add?id={p['id']}{options_query(options)}&md2ui.commit=1)"]
    return "\n".join([
        "___",
        f"![{alt(p['name'])}]({img_hero(p)})",
        "::: 1 >",
        top,
        f"# {p['name']}",
        f"**⭐** __{p['rating']}__ _{p['reviews']:,} reviews_ - **⏱️** _{delivery_range(p)}_ - "
        f"**🔥** _{p['calories']:,} kcal_",
        "+++",
        price,
        "+++",
        p["description"],
        "",
        "_Ingredients_",
        tags,
        "+++",
        *buy,
        ":::1.2",
        "___",
        "***",
        "",
        "## Goes well with",
        "",
        rows(shop, pairs),
    ])


def cart(shop: Shop) -> str:
    c = shop.cart_view()
    if not c["lines"]:
        return empty(shop, "cart")
    return "\n".join([
        f"# Your cart ... `{items_label(c['item_count'])}`",
        "",
        "\n".join(cart_row(shop, line) for line in c["lines"]),
        "",
        summary(c),
        "",
        "***",
        "",
        "[Checkout](agent:checkout) *[Keep shopping](agent:catalog)*",
    ])


def checkout(shop: Shop, address: str | None = None) -> str:
    address = address or shop.customer["address"]
    c = shop.cart_view()
    if not c["lines"]:
        return empty(shop, "cart")
    return "\n".join([
        "# Checkout",
        "",
        f"- 📍 - __Deliver to__ : _{address}_ ... __[✏️](agent:change-address)__",
        "- ⏱️ - __Arrives in__ : _about 20 minutes_",
        "- 💳 - __Payment__ : _Secure payment window_ ... `Test mode`",
        "",
        summary(c, first="Items"),
        "",
        "***",
        "",
        f"[Pay {money(c['total'])}](agent:checkout) *[Back to cart](agent:cart)*",
    ])


def success(shop: Shop, order_id: str | None = None) -> str:
    v = shop.order_view(shop.order(order_id))
    return "\n".join([
        "## {#success-1}",
        "",
        "*✔️*",
        "",
        "__Payment successful__",
        f"___{money(v['total'])}___",
        f"\"💳\" {v['card']}",
        "",
        "---",
        "",
        f"- Order ... **{v['order_id']}**",
        f"- Arrives ... **about {v['arrives']}**",
        f"- Items ... **{v['item_count']}**",
        "",
        f"[Track order](agent:order-status?id={v['order_id']}) *[Back to home](agent:home)*",
    ])


# An order's stage in words, as its chip reads; the chip's spelling says whether it is still
# open (***), went well (**) or went wrong (__), and the theme pins the colour of the two
# final words, so a fed chip that turns Delivered or Cancelled takes their look.
STAGE_WORD = {"received": "Received", "preparing": "Preparing", "on_the_way": "On the way",
              "delivered": "Delivered", "cancelled": "Cancelled"}
STATUS_MARK = {"delivered": "**", "cancelled": "__"}  # every other stage is open: ***
STATUS_CHIP = {status: f"{STATUS_MARK.get(status, '***')}`{word}`{STATUS_MARK.get(status, '***')}"
               for status, word in STAGE_WORD.items()}
FINISHED = frozenset({"delivered", "cancelled"})
PROGRESS = "Progress"  # the bar's key, which the feed moves


# --- a running order's live values: feed slots ------------------------------------
# While an order runs, a page that shows it marks its stage and arrival as md2ui feed
# slots (ADR-206), named by the order, and the shop's feed writes them as the order moves
# (order_feeds.py). A finished order's are plain: a receipt's values do not change.
def stage_slot(order_id: str) -> str:
    return f"stage-{order_id}"


def arrives_slot(order_id: str) -> str:
    return f"arrives-{order_id}"


def stage_chip(v: dict) -> str:
    if v["status"] in FINISHED:
        return STATUS_CHIP[v["status"]]
    return f"***[`{STAGE_WORD[v['status']]}`](feed:{stage_slot(v['order_id'])})***"


def arrival(v: dict) -> str:
    return v["arrives"] if v["status"] in FINISHED else f"[{v['arrives']}](feed:{arrives_slot(v['order_id'])})"


def live_values(v: dict) -> dict[str, str | int]:
    """What the feed writes for the order *v*: its stage, its arrival, and the bar while it
    has one (a cancelled order has none)."""
    out: dict[str, str | int] = {stage_slot(v["order_id"]): STAGE_WORD[v["status"]],
                                 arrives_slot(v["order_id"]): v["arrives"]}
    if v["progress"] is not None:
        out[PROGRESS] = v["progress"]
    return out
STATUS_BADGE = {"received": "🧾", "preparing": "👨‍🍳", "on_the_way": "🛵", "delivered": "🏁", "cancelled": "❌"}


def order_lines(v: dict) -> str:
    """An order's items; a size other than the product's default is said after the name."""
    rows = [f"- {l['quantity']} × {l['name']}" + ("" if l["default_options"] else f" ({l['options_label']})")
            + f" ... **{money(l['line_total'])}**" for l in v["lines"]]
    fee = "`Free`" if v["delivery"] == 0 else f"**{money(v['delivery'])}**"
    rows.append(f"- Delivery ... {fee}")
    rows.append(f"- __Total__ ... __{money(v['total'])}__")
    return "\n".join(rows)


def order_status(shop: Shop, order_id: str | None = None) -> str:
    try:
        o = shop.order(order_id)
    except ShopError:
        return empty(shop, "orders")
    v = shop.order_view(o)
    updates = [f"- {u['badge']} - __{u['title']}__ : _{u['detail']}_ ... _{u['time']}_" for u in v["updates"]]
    updates += [f"- ~~{u['badge']}~~ - _{u['title']}_ ... _{u['time']}_" for u in v["upcoming"]]
    head = ["## {#status-1}", "", f"*{v['badge']}*", ""]
    if v["status"] == "cancelled":
        head += [f"___{v['headline']}___", f"{v['cancel_reason']}. {money(v['total'])} went back to {v['card']}.",
                 f"_Order {v['order_id']} • placed {v['placed']} at {v['placed_time']}_"]
    elif v["status"] == "delivered":
        head += [f"___{v['headline']}___", "Your order was delivered. Enjoy!",
                 f"_Order {v['order_id']} • delivered {v['placed']} at {v['arrives']}_"]
    else:  # running: nothing on the card says the stage but its fed chip, so nothing goes stale
        head += [f"___Order {v['order_id']}___", f"_Arriving around {arrival(v)}_ ... {stage_chip(v)}",
                 f"{PROGRESS}: {v['progress']}%"]
    actions = [f"*[Contact support](agent:support?order={v['order_id']})*"]
    if v["can_cancel"]:
        actions.append(f"*[Cancel order](agent:cancel-order?id={v['order_id']})*")
    else:
        actions.append(f"*[Order again](agent:reorder?id={v['order_id']})*")
    return "\n".join(head + ["", "## Updates", "", "\n".join(updates), "", "## Items", "", order_lines(v), "",
                             "... " + " ".join(actions) + " ..."])


def orders(shop: Shop) -> str:
    """The order history, newest first, then the customer's usual items and new ones to try."""
    history = shop.history()
    if not history:
        return empty(shop, "orders")
    recs = shop.recommendations()
    rows = [order_card(shop, o) for o in history]
    out = [f"# Your orders ... `{len(history)} orders`", ""]
    if recs["usual_spend"]:
        out += [f"_{recs['orders_placed']} delivered, about {recs['usual_spend']} an order_", ""]
    out += ["\n".join(rows)]
    if recs["order_again"]:
        out += ["", picks(shop, recs)]
    return "\n".join(out)


def picks(shop: Shop, recs: dict | None = None) -> str:
    """Recommendations from the order history: the usual items, then new ones to try."""
    recs = recs or shop.recommendations()
    out = []
    if recs["order_again"]:
        out += ["## Your usual", "", rows(shop, [shop.product(r["id"]) for r in recs["order_again"]])]
    if recs["try_next"]:
        reason = recs["try_next"][0]["reason"]
        out += ["", "## Something new to try", "", f"_{reason}_", "",
                cards(shop, [shop.product(r["id"]) for r in recs["try_next"]])]
    return "\n".join(out) if out else empty(shop, "orders")


def cancel_sheet(shop: Shop, order_id: str) -> str:
    """The question before cancelling an order; the answer comes back to the agent."""
    o = shop.order(order_id)
    v = shop.order_view(o)
    if not v["can_cancel"]:
        state = "already cancelled" if v["status"] == "cancelled" else f"{v['headline'].lower()}"
        return "\n".join(["## {#sheet-1}", "", "*⚠️*", "", f"__Order {o.id} can't be cancelled__",
                          f"It is {state}, so it can no longer be cancelled.", "",
                          f"[Back to my order](agent:order-status?id={o.id}) *[Contact support](agent:support?order={o.id})*"])
    return "\n".join([
        "## {#sheet-1}", "", "*⚠️*", "",
        f"__Cancel order {o.id}?__",
        stage_chip(v),
        f"It can be cancelled until a rider picks it up. {money(v['total'])} goes back to {v['card']}.", "",
        f"[Cancel order](agent:confirm-cancel?id={o.id}) *[Keep my order](agent:order-status?id={o.id})*",
    ])


EMPTY = {
    "cart": ("🛒", "Your cart is empty",
             "Add a burger, a side or a shake and it will wait for you here. Every burger is smashed to order "
             "and delivered in about 20 minutes.",
             "[Browse burgers](agent:catalog) *[See offers](agent:offers)*"),
    "orders": ("🧾", "No orders yet",
               "When you place an order, you can follow it here from the kitchen to your door.",
               "[Browse burgers](agent:catalog) *[See offers](agent:offers)*"),
    "likes": ("🤍", "No favourites yet",
              "Tap the heart on any burger and it will be saved here for next time.",
              "[Browse burgers](agent:catalog) *[Best sellers](agent:catalog?sort=popular)*"),
    "search": ("🔍", "Nothing matches that",
               "Try another word, or browse the whole menu.",
               "[Show the whole menu](agent:catalog) *[See offers](agent:offers)*"),
}


def empty(shop: Shop, kind: str = "cart") -> str:
    badge, title, text, actions = EMPTY[kind]
    over = money(shop.cart_view()["free_delivery_over"]).replace(".00", "")
    return "\n".join([
        "## {#empty-1}", "", f"*{badge}*", "", f"___{title}___", text, "", "+++", "",
        f"✓ - __Free delivery over {over}__ : _No fees on bigger orders_", "", "+++", "", actions,
    ])


# --- includes ---------------------------------------------------------------------
# md2ui draws them (ADR-612): `Conversation.send` replaces each include line with what
# `render_include` returns, keeps the region it drew, and draws it again when a handler
# names it. The shop adds only what md2ui cannot know: an include line on a line of its
# own, and the context one include takes from the others on the page (`prepare`).
INCLUDES_HELP = """\
| Include line | Draws |
|---|---|
| `{{home}}` | the whole home dashboard in the shop's own words; only when you cannot write your own band and cards |
| `{{headline greeting="…" line="…" kicker="…" image=<product id> cta="…" action=<agent link> cta2="…" action2=<agent link>}}` | the home page's band, in your words: every key optional, the shop's own words where left out |
| `{{offer product=<id> kicker="…" title="…" chip="…" cta="…" action=<agent link>}}` or `{{offer promo=<id> …}}` | one of the three cards under the band, featuring a product or a promotion (its photo, and its words where you leave yours out); write three lines in a row, and each card takes the next brand colour. The band's and the cards' actions are product ones only: product, cart-add, offer, offers, catalog, picks |
| `{{home-rest note="…"}}` | the home page under the band and the cards: the orders section (the running order's status, the last order, and the suggestion to order again, worded by your `note`), then recommendations, today's offers, suggestions |
| `{{offers}}` / `{{track}}` / `{{suggestions}}` | one section of the home page, in the shop's own words |
| `{{menu}}` | the catalog page; filters as `key=value`: `category=burgers`, `query=bacon`, `max_price=10`, `label=Offer`, `spicy=true`, `vegetarian=true`, `liked=true`, `sort=popular|rating|price`, `page=2`, `title="Spicy picks"` |
| `{{cards id id …}}` | product cards for those product ids, in that order |
| `{{rows id id …}}` | product rows for those product ids |
| `{{product id}}` / `{{product id size=triple}}` | one product's full page, at its default size or the one named (burgers: single, double, triple; shakes: regular, large) |
| `{{cart}}` | the cart page (the empty state when the cart is empty) |
| `{{checkout}}` | the order review shown behind the payment window |
| `{{success}}` / `{{success BS-1042}}` | the payment-successful confirmation for the last order, or that one |
| `{{order}}` / `{{order BS-1042}}` | the order status page for the last order, or that one (the empty state when there is none) |
| `{{orders}}` | the order history, newest first, each row opening its order, then the customer's usual items and new ones to try |
| `{{picks}}` | recommendations from the order history: their usual items (rows), then new products to try (cards) |
| `{{cancel BS-1042}}` | the question before cancelling that order (or why it can't be cancelled) |
| `{{empty cart|orders|likes|search}}` | that empty state |"""

# The includes a cart line or a like shows in, and so the ones a ➕ ➖ or a 🤍 ❤️ handler
# names as changed: every stepper and heart is drawn by one of them.
DRAWS_CART = frozenset({"home", "home-rest", "for-you", "menu", "catalog", "cards", "rows", "product",
                        "cart", "checkout", "orders", "history", "picks", "recommendations"})
DRAWS_LIKES = frozenset({"home", "home-rest", "for-you", "menu", "catalog", "cards", "product",
                         "orders", "history", "picks", "recommendations"})
# The includes that draw an order's state (its stage, updates, actions, arrival), or that
# change when one moves (the recommendations count delivered orders), and so the ones the
# shop names to md2ui when the clock moves an order or a cancel ends it (order_feeds.py).
DRAWS_ORDERS = frozenset({"home", "home-rest", "for-you", "your-orders", "track", "orders", "history",
                          "order", "order-status", "cancel", "success", "picks", "recommendations"})
NAMES = sorted(DRAWS_CART | {"headline", "offers", "offer", "your-orders", "track", "suggestions",
                             "success", "cancel", "order", "order-status", "empty"})


HEADLINE_KEYS = {"greeting", "line", "kicker", "image", "cta", "action", "cta2", "action2"}
OFFER_KEYS = {"product", "promo", "kicker", "title", "chip", "cta", "action"}


def _words(named: dict[str, str], keys: set[str]) -> dict[str, str]:
    unknown = set(named) - keys
    if unknown:
        raise ShopError(f"unknown parameter {', '.join(sorted(unknown))}")
    return named


def _filters(named: dict[str, str]) -> dict:
    out: dict = {}
    for k, v in named.items():
        if k in ("max_price",):
            out[k] = float(v)
        elif k in ("spicy", "vegetarian", "liked"):
            out[k] = v.lower() in ("1", "true", "yes")
        elif k == "page":
            out[k] = int(v)
        elif k in ("category", "query", "label", "sort", "title"):
            out[k] = v
    return out


def render_include(shop: Shop, name: str, args: Args) -> str:
    """The Markdown the include *name* draws for *args*; ShopError, ValueError or
    IndexError when they do not read, and md2ui leaves the line for `check` to report."""
    positional, named = list(args.words), dict(args.named)
    match name:
        case "home":
            return home(shop)
        case "headline":
            return headline(shop, **_words(named, HEADLINE_KEYS))
        case "offers":
            return offer_cards(shop)
        case "offer":
            return offer_card(shop, int(named.pop("n")), **_words(named, OFFER_KEYS))
        case "home-rest" | "for-you":
            return home_rest(shop, set(named.get("featured", "").split(",")) - {""}, named.get("note"))
        case "your-orders":
            return orders_section(shop, named.get("note"))
        case "track":
            running = shop.running_order()
            return track_card(shop, running) if running else ""
        case "suggestions":
            return SUGGESTIONS
        case "menu" | "catalog":
            return menu(shop, **_filters(named))
        case "cards":
            return cards(shop, [shop.product(pid) for pid in positional])
        case "rows":
            return rows(shop, [shop.product(pid) for pid in positional])
        case "product":
            return product_page(shop, positional[0], named.get("size"))
        case "cart":
            return cart(shop)
        case "checkout":
            return checkout(shop)
        case "success":
            return success(shop, positional[0] if positional else None)
        case "orders" | "history":
            return orders(shop)
        case "picks" | "recommendations":
            return picks(shop)
        case "cancel":
            return cancel_sheet(shop, positional[0])
        case "order" | "order-status":
            return order_status(shop, positional[0] if positional else None)
        case "empty":
            return empty(shop, positional[0] if positional else "cart")
    raise ShopError(f"unknown include '{{{{{name}}}}}'")


def registry(shop: Shop) -> Includes:
    """Every include, for md2ui's `Conversation`: each drawn from `shop` as it is when drawn,
    and the line md2ui draws in its place when it cannot be (in the shop's words)."""
    includes = Includes()
    for name in NAMES:
        includes.add(name, f"the shop's {name}", lambda args, name=name: render_include(shop, name, args),
                     failure=f"Could not show the {name} right now.")
    return includes


def prepare(markdown: str) -> str:
    """The include lines of *markdown* as md2ui draws them: each on a line of its own between
    blank lines, `{{offer …}}` lines numbered in the order written (the theme colours each card
    by its number) with a `***` closing the row after the last, and the products the band and
    the cards feature passed to `{{home-rest}}`, so nothing shows twice."""
    lines = markdown.split("\n")
    found = [INCLUDE_LINE.match(line) for line in lines]
    offers = [i for i, m in enumerate(found) if m and m.group("name") == "offer"]
    featured = ",".join(
        [p for i in offers for p in re.findall(r"\bproduct=([a-z0-9-]+)", lines[i])]
        + [p for m in found if m and m.group("name") == "headline"
           for p in re.findall(r"\bimage=([a-z0-9-]+)", m.group("args"))])
    out: list[str] = []
    for i, (line, m) in enumerate(zip(lines, found)):
        if m is None:
            out.append(line)
            continue
        line = line.rstrip()
        if m.group("name") == "offer":
            line = f"{line[:-2].rstrip()} n={offers.index(i) + 1}}}}}"
        elif m.group("name") in ("home-rest", "for-you") and featured:
            line = f"{line[:-2].rstrip()} featured={featured}}}}}"
        out += ["", line, ""] + (["***", ""] if offers and i == offers[-1] else [])
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


def draw(shop: Shop, markdown: str) -> tuple[str, list[str]]:
    """*markdown* prepared and drawn as md2ui's `Conversation.send` draws it, and the include
    lines it could not draw (an unknown name, args that do not read)."""
    drawn, regions = expand(prepare(markdown), registry(shop))
    return drawn, [r.line for r in regions if r.failed]
