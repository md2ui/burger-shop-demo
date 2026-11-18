"""The mock shop, the pages it draws through md2ui's includes, and what a tap redraws. No Claude calls."""

import asyncio
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from md2ui.includes import INCLUDE_LINE, parse_args

import main
import pages
import tools
from shop import STAGE_SECONDS, OptionError, Shop, ShopError, clock_time, unit_price

THEME = Path(__file__).parent.parent / "md2ui_theme/THEME.md"
MD2UI = Path(sys.executable).parent / "md2ui"  # the md2ui requirements.txt installed beside pytest


class Clock:
    def __init__(self, t: float = 1_800_000_000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def shop(clock):
    return Shop(clock=clock)


def paid_order(shop: Shop):
    shop.set_qty("classic-smash", 2)
    shop.set_qty("crispy-fries", 1)
    s = shop.create_checkout()
    return shop.pay(s.id, "4242 4242 4242 4242", "12/30", "123")


# --- shop ----------------------------------------------------------------------------
def test_cart_totals_and_free_delivery(shop):
    shop.set_qty("classic-smash", 1)
    c = shop.cart_view()
    assert (c["subtotal"], c["delivery"], c["total"], c["item_count"]) == (9.5, 2.99, 12.49, 1)
    shop.set_qty("classic-smash", 3)
    c = shop.cart_view()
    assert (c["subtotal"], c["delivery"], c["total"]) == (28.5, 0.0, 28.5)
    shop.add("classic-smash", -3)
    assert shop.cart_view()["lines"] == []


def test_quantities_are_clamped_and_products_checked(shop):
    assert shop.add("crispy-fries", -1) == 0
    assert shop.set_qty("crispy-fries", 99) == 20
    with pytest.raises(ShopError):
        shop.add("no-such-burger")


def test_find_filters(shop):
    assert {p["id"] for p in shop.find(label="Offer")} == {"bacon-bbq", "sunset-crunch", "burger-box"}
    assert {p["id"] for p in shop.find(label="New")} == {"double-pickle", "smokehouse", "fries-dip"}
    assert all(p["price"] <= 10 for p in shop.find(max_price=10))
    assert [p["id"] for p in shop.find(query="bacon")][:1] == ["bacon-bbq"]
    shop.set_like("smokehouse", True)
    assert [p["id"] for p in shop.find(liked=True)] == ["smokehouse"]


def test_payment_creates_order_and_empties_cart(shop):
    s = paid_order(shop)
    assert s.status == "paid" and s.order_id == "BS-1042"
    assert shop.cart == {}
    o = shop.order()
    assert o.card == "Visa •••• 4242" and o.total == 25.89  # under $25: delivery is $2.99


def test_declined_card_and_bad_details(shop):
    shop.set_qty("classic-smash", 1)
    s = shop.create_checkout()
    with pytest.raises(ShopError):
        shop.pay(s.id, "4242", "12/30", "123")
    assert shop.pay(s.id, "4000 0000 0000 0002", "12/30", "123").status == "failed"
    assert shop.cart  # nothing paid, nothing emptied
    with pytest.raises(ShopError):
        shop.pay(s.id, "4242 4242 4242 4242", "12/30", "123")  # the session is closed


def test_checkout_needs_items(shop):
    with pytest.raises(ShopError):
        shop.create_checkout()


def test_order_moves_on_the_clock(shop, clock):
    paid_order(shop)
    o = shop.order()
    seen = []
    for stages in (0, 1, 3, 6):
        clock.t = o.placed_at + stages * STAGE_SECONDS + 1
        seen.append(shop.order_view(o)["status"])
    assert seen == ["received", "preparing", "on_the_way", "delivered"]
    assert shop.running_order() is None


def test_the_arrival_estimate_moves_like_a_delivery_estimate(clock):
    """Re-quoted at each stage and every half step on the way, from a seeded error that
    narrows to the door; never before now; delivered, it is the delivery time."""
    def life(seed: str) -> list[float]:
        shop = Shop(clock=clock, eta_seed=seed)
        paid_order(shop)
        o = shop.order()
        out = []
        for tick in range(0, 6 * 4):  # every quarter step until the door
            clock.t = o.placed_at + tick * STAGE_SECONDS / 4
            out.append(shop.arrival(o, clock.t))
            assert out[-1] >= clock.t
            assert shop.order_view(o)["arrives"] == clock_time(out[-1])
        door = o.placed_at + 6 * STAGE_SECONDS
        clock.t = door + 1
        assert shop.arrival(o, clock.t) == door and shop.order_view(o)["arrives"] == clock_time(door)
        return [q - o.placed_at for q in out]

    quotes = life("a")
    assert quotes == life("a")  # deterministic for a seed
    assert len(set(quotes)) >= 3  # it moves during the order's life
    by_stage = [quotes[0], quotes[4], quotes[12]]  # received, preparing, on the way
    assert by_stage[0] > by_stage[1] > by_stage[2]  # every stage change narrows it
    assert any(life(str(seed)) != quotes for seed in range(5))  # the seed picks the errors


# --- pages ---------------------------------------------------------------------------
def test_stepper_and_like_spellings():
    assert pages.stepper("x", 0) == "~~__[➖](agent:cart-remove?id=x)__~~ - **0** - __[➕](agent:cart-add?id=x)__"
    assert pages.stepper("x", 2) == "__[➖](agent:cart-remove?id=x)__ - **2** - __[➕](agent:cart-add?id=x)__"
    assert pages.like("x", True) == "__[❤️](agent:unlike?id=x)__"


def failure(shop, line: str) -> str:
    """Why md2ui could not draw *line*: the error `render_include` raised."""
    m = INCLUDE_LINE.match(line)
    assert m is not None, line
    with pytest.raises((ShopError, ValueError, IndexError)) as e:
        pages.render_include(shop, m.group("name"), parse_args(m.group("args")))
    return str(e.value)


def test_includes_expand_and_report_failures(shop):
    md, failed = pages.draw(shop, "# Hi\n\n{{cards classic-smash bacon-bbq}}\n\n{{product nope}}\n")
    assert md.count("### \n[\n![") == 2 and md.count("](agent:product?id=") == 2 and "agent:cart-add?id=bacon-bbq" in md
    assert failed == ["{{product nope}}"] and "nope" in failure(shop, failed[0])
    md, _ = pages.draw(shop, "{{menu category=sides title=\"Sides & dips\"}}")
    assert md.startswith("# Sides & dips") and "crispy-fries" in md and "classic-smash" not in md


def test_empty_states(shop, clock):
    assert "{#empty-1}" in pages.cart(shop)
    assert "No orders yet" in pages.order_status(Shop(clock=clock, with_history=False))
    assert "Nothing matches" in pages.menu(shop, query="pizza")


def test_home_shows_track_card_only_while_an_order_runs(shop):
    assert "{#track-1}" not in pages.home(shop)
    paid_order(shop)
    assert "{#track-1}" in pages.home(shop)


# --- history, cancelling, recommendations ------------------------------------------
def test_history_is_loaded_newest_first(shop):
    ids = [o.id for o in shop.history()]
    assert ids == ["BS-1040", "BS-1039", "BS-1037", "BS-1035", "BS-1033", "BS-1031"]
    statuses = {o.id: shop.order_view(o)["status"] for o in shop.history()}
    assert statuses["BS-1039"] == statuses["BS-1033"] == "cancelled"
    assert {statuses[i] for i in ("BS-1040", "BS-1037", "BS-1035", "BS-1031")} == {"delivered"}
    assert shop.running_order() is None


def test_an_order_can_be_cancelled_only_before_the_rider(shop, clock):
    paid_order(shop)
    o = shop.order()
    clock.t = o.placed_at + 1.5 * STAGE_SECONDS  # preparing
    assert shop.order_view(o)["can_cancel"]
    shop.cancel_order(o.id, "Changed my mind")
    v = shop.order_view(o)
    assert v["status"] == "cancelled" and v["progress"] is None and v["updates"][0]["title"] == "Order cancelled"
    assert shop.running_order() is None
    with pytest.raises(ShopError, match="already cancelled"):
        shop.cancel_order(o.id)
    paid_order(shop)
    late = shop.order()
    clock.t = late.placed_at + 3.5 * STAGE_SECONDS  # on the way
    with pytest.raises(ShopError, match="on the way"):
        shop.cancel_order(late.id)
    with pytest.raises(ShopError, match="can no longer"):
        shop.cancel_order("BS-1040")  # delivered


def test_recommendations_come_from_the_history(shop):
    r = shop.recommendations()
    assert [x["id"] for x in r["order_again"]] == ["crispy-fries", "classic-smash", "strawberry-shake"]
    assert r["order_again"][0]["times"] == 4  # cancelled orders do not count
    ordered = shop.ordered_counts()
    assert r["try_next"] and all(x["id"] not in ordered for x in r["try_next"])
    assert "Classic Smash" in r["try_next"][0]["reason"]
    assert shop.recommended()[0]["id"] == "classic-smash"  # the usual burger leads the home page


def test_without_history_recommendations_fall_back(clock):
    bare = Shop(clock=clock, with_history=False)
    assert bare.recommendations()["order_again"] == [] and bare.recommended()
    assert "No orders yet" in pages.orders(bare)


def test_order_pages(shop, clock):
    md = pages.orders(shop)
    assert md.count("](agent:order-status?id=") == 6 and "__`Cancelled`__" in md and "## Your usual" in md
    assert "agent:cancel-order" not in pages.order_status(shop, "BS-1040")
    assert "agent:reorder?id=BS-1040" in pages.order_status(shop, "BS-1040")
    paid_order(shop)
    o = shop.order()
    clock.t = o.placed_at + 1.5 * STAGE_SECONDS
    assert "*[Cancel order](agent:cancel-order?id=BS-1042)*" in pages.order_status(shop, o.id)
    assert "[Cancel order](agent:confirm-cancel?id=BS-1042)" in pages.cancel_sheet(shop, o.id)
    assert "can't be cancelled" in pages.cancel_sheet(shop, "BS-1040")


# --- the home page in the agent's words -----------------------------------------------
FRESH_HOME = """{{headline greeting="Good evening, hungry?" line="Your usual is one tap away." kicker="Wednesday treat?" image=smokehouse cta="Try the Smokehouse" action=product?id=smokehouse}}

{{offer product=classic-smash kicker="Your usual" title="Classic Smash again?" chip="Ordered 3 times"}}
{{offer product=double-pickle kicker="New for you" title="Try it" chip="✨ New"}}
{{offer promo=box-deal}}

{{home-rest note="Same again for Friday?"}}"""


def test_fresh_home_takes_the_agents_words(shop):
    md, failed = pages.draw(shop, FRESH_HOME)
    assert failed == []
    assert "___Good evening, hungry?___" in md and "_Wednesday treat?_" in md and "Your usual is one tap away." in md
    assert "[Try the Smokehouse](agent:product?id=smokehouse)" in md and "*[" not in md.split("::: 1 >")[0]
    orders = md.split("## Your orders")[1].split("## Recommended")[0]
    assert "__Last order BS-1040__" in orders and "__Same again for Friday?__" in orders
    assert "_[Order again](agent:reorder?id=BS-1040)_" in orders
    assert md.index("## Your orders") < md.index("## Recommended for you")
    assert "photo-1767065703793" in md.split("***")[0]  # the Smokehouse photo in the band
    assert [int(n) for n in re.findall(r"\{#offer-(\d)\}", md)] == [1, 2, 3]
    assert md.count("\n***\n") >= 2  # the band and the row of cards are both closed
    assert "**[Add one](agent:cart-add?id=classic-smash)**" in md and "**[Get the box](agent:offer?id=box-deal)**" in md
    recommended = md.split("## Recommended for you")[1].split("## ")[0]
    assert "classic-smash" not in recommended and "double-pickle" not in recommended  # featured above
    assert "smokehouse" not in recommended  # the band's photo counts as featured too


def test_agent_words_are_kept_plain_and_actions_checked(shop):
    md, failed = pages.draw(shop, '{{headline greeting="Hi **there** _now_ [x](https://e.x)" line="one   line"}}')
    assert failed == [] and "___Hi there now x(https://e.x)___" in md and "\none line\n" in md
    assert "not an action" in failure(shop, '{{headline greeting="Hi" action="https://evil.example"}}')
    assert "unknown promotion" in failure(shop, '{{offer promo=nope n=1}}')
    assert "unknown parameter" in failure(shop, '{{offer product=classic-smash colour=red n=1}}')
    assert pages.draw(shop, '{{offer promo=nope}}')[1] == ['{{offer promo=nope n=1}}']


def test_band_and_cards_take_product_actions_only(shop):
    for line in ('{{headline greeting="Hi" action=reorder?id=BS-1040}}',
                 '{{headline greeting="Hi" cta2="Track" action2=order-status?id=BS-1040}}',
                 '{{offer product=classic-smash action=orders}}'):
        offer = line.startswith("{{offer")
        assert "not a product action" in failure(shop, line.replace("}}", " n=1}}") if offer else line), line
    assert pages.draw(shop, '{{offer product=classic-smash action=product?id=classic-smash}}')[1] == []


def test_orders_section_follows_the_orders(shop, clock):
    assert "{#track-1}" not in pages.orders_section(shop)
    paid_order(shop)
    clock.t = shop.order().placed_at + 1
    section = pages.orders_section(shop)
    assert "### {#track-1}" in section and "__Last order BS-1040__" in section  # the running one is not "last"
    assert pages.orders_section(Shop(clock=clock, with_history=False)) == ""


def test_home_context_has_what_a_greeting_needs(shop):
    c = shop.home_context()
    assert "first_name" not in c and "Alex" not in json.dumps(c)  # no name: the demo greets the moment
    assert c["now"]["part_of_day"] in ("morning", "lunchtime", "afternoon", "evening", "late night")
    assert c["usual"][0]["id"] == "crispy-fries" and c["last_order"]["order_id"] == "BS-1040"
    assert c["running_order"] is None and {p["id"] for p in c["new_on_menu"]} == {"double-pickle", "smokehouse", "fries-dip"}
    assert [p["id"] for p in c["promotions"]] == ["made-fresh", "loaded-beef", "box-deal"]


def every_page(shop) -> dict[str, str]:
    shop.set_qty("classic-smash", 2)
    shop.set_like("double-pickle", True)
    out = {"home-empty-cart": pages.home(shop), "menu": pages.menu(shop), "burgers": pages.menu(shop, category="burgers"),
           "product": pages.product_page(shop, "bacon-bbq"), "product-sized": pages.product_page(shop, "classic-smash", "triple"),
           "product-side": pages.product_page(shop, "crispy-fries"),
           "product-shake": pages.product_page(shop, "strawberry-shake", "large")}
    shop.set_qty("classic-smash", 1, {"size": "triple"})
    shop.set_qty("strawberry-shake", 1, {"size": "large"})
    out |= {"cart": pages.cart(shop), "checkout": pages.checkout(shop)}
    paid_order(shop)
    out |= {"home": pages.home(shop), "success": pages.success(shop), "order": pages.order_status(shop),
            "empty": pages.empty(shop, "likes"), "orders": pages.orders(shop), "picks": pages.picks(shop),
            "cancel": pages.cancel_sheet(shop, shop.order().id), "cancelled": pages.order_status(shop, "BS-1039"),
            "fresh-home": pages.draw(shop, FRESH_HOME)[0]}
    return out


@pytest.mark.skipif(not MD2UI.exists() or shutil.which("true") is None, reason="md2ui is not installed beside this Python")
def test_every_page_passes_md2ui_check(shop, tmp_path):
    for name, md in every_page(shop).items():
        doc = tmp_path / f"{name}.md"
        doc.write_text(md)
        run = subprocess.run([MD2UI, "check", doc, "--theme", THEME], capture_output=True, text=True)
        issues = [l for l in run.stdout.splitlines()
                  if l and not l.startswith("[") and "repeated-offer" not in l]
        assert run.returncode == 0 and not [i for i in issues if i.startswith("error")], (name, issues)


# --- sizes ---------------------------------------------------------------------------
def test_sizes_price_each_line_and_key_it(shop):
    assert shop.options("classic-smash") == {"size": "double"}  # two patties: Double is its listed price
    assert shop.options("bacon-bbq") == {"size": "single"} and shop.options("strawberry-shake") == {"size": "regular"}
    assert shop.options("crispy-fries") == {} and shop.options("burger-box") == {}
    shop.add("classic-smash", 2)  # no options: the default line
    shop.add("classic-smash", 1, {"size": "triple"})
    shop.add("classic-smash", 1, {"size": "single"})
    shop.add("strawberry-shake", 1, {"size": "large"})
    shop.add("crispy-fries")
    assert shop.cart == {"classic-smash?size=double": 2, "classic-smash?size=triple": 1, "classic-smash?size=single": 1,
                         "strawberry-shake?size=large": 1, "crispy-fries": 1}
    lines = {l["key"]: l for l in shop.cart_view()["lines"]}
    assert lines["classic-smash?size=double"]["line_total"] == 19.0 and lines["classic-smash?size=double"]["default_options"]
    assert lines["classic-smash?size=triple"]["unit_price"] == 12.0 and lines["classic-smash?size=triple"]["options_label"] == "Triple"
    assert lines["classic-smash?size=single"]["unit_price"] == 7.5
    assert lines["strawberry-shake?size=large"]["unit_price"] == 7.0 and lines["crispy-fries"]["options"] == {}
    assert shop.cart_view()["subtotal"] == 19.0 + 12.0 + 7.5 + 7.0 + 3.9
    assert shop.qty("classic-smash") == 2 and shop.qty("classic-smash", {"size": "triple"}) == 1
    assert shop.product_qty("classic-smash") == 4
    shop.add("classic-smash", -1, {"size": "triple"})
    assert "classic-smash?size=triple" not in shop.cart


def test_unknown_options_are_refused(shop):
    with pytest.raises(OptionError, match="no size 'large'"):
        shop.add("classic-smash", 1, {"size": "large"})
    with pytest.raises(OptionError, match="no option 'size'"):
        shop.add("crispy-fries", 1, {"size": "large"})
    with pytest.raises(OptionError):
        shop.add("classic-smash", 1, {"sauce": "extra"})
    assert shop.cart == {}


def test_every_listed_price_is_its_default_size(shop):
    for p in shop.products.values():
        options = shop.options(p["id"])
        assert unit_price(p, options) == p["price"], p["id"]
        if p["category"] in ("burgers", "shakes"):
            assert options, p["id"]


def test_an_order_keeps_its_sizes_and_reorders_them(shop):
    shop.set_qty("classic-smash", 2, {"size": "triple"})
    s = shop.create_checkout()
    shop.pay(s.id, "4242 4242 4242 4242", "12/30", "123")
    o = shop.order()
    assert o.lines[0]["options"] == {"size": "triple"} and o.total == 26.99
    assert "- 2 × Classic Smash (Triple) ... **$24.00**" in pages.order_status(shop, o.id)
    assert "- 2 × Classic Smash ... " in pages.order_status(shop, "BS-1035")  # a default size is not said
    asyncio.run(tools.call_backend_tool(shop, "reorder", {"order_id": o.id}))
    assert shop.cart == {"classic-smash?size=triple": 2}


# --- spellings with sizes --------------------------------------------------------------
def test_sized_stepper_spellings():
    assert pages.stepper("x", 1, {"size": "triple"}) == (
        "__[➖](agent:cart-remove?id=x&size=triple)__ - **1** - __[➕](agent:cart-add?id=x&size=triple)__")
    assert pages.stepper("x", 0, {}) == pages.stepper("x", 0)


def test_cart_rows_spell_their_size(shop):
    shop.set_qty("classic-smash", 1, {"size": "triple"})
    shop.set_qty("crispy-fries", 1)
    md = pages.cart(shop)
    assert ("[`Classic Smash`](agent:product?id=classic-smash&size=triple) : `Burger` *`Triple`* : **$12.00** ... "
            "__[➖](agent:cart-remove?id=classic-smash&size=triple)__ - **1** - ") in md
    assert "[`Crispy Fries`](agent:product?id=crispy-fries) : `Side` : **$3.90** ... __[➖](agent:cart-remove?id=crispy-fries)__" in md
    shop.set_qty("classic-smash", 1)  # the default size is spelled too
    assert "agent:cart-add?id=classic-smash&size=double)" in pages.cart(shop)


def test_product_page_at_a_size(shop):
    shop.set_qty("classic-smash", 3, {"size": "triple"})
    md, failed = pages.draw(shop, "{{product classic-smash size=triple}}")
    assert failed == [] and "___$12.00___" in md
    assert ("_Size_\n*[Single](agent:size?id=classic-smash&size=single&md2ui.choice=size)* | "
            "*[Double](agent:size?id=classic-smash&size=double&md2ui.choice=size)* | "
            "[Triple](agent:size?id=classic-smash&size=triple&md2ui.choice=size)\n\nQuantity: ➖ [1/9] ➕\n\n"
            "[Add to cart](agent:add?id=classic-smash&size=triple&md2ui.commit=1)\n") in md
    assert "agent:cart-add?id=classic-smash" not in md  # the form holds the quantity: no stepper for it
    assert "agent:cart-add?id=crispy-fries)" in md  # the rows under it keep their steppers
    md = pages.product_page(shop, "bacon-bbq", "double")  # on offer: both prices move with the size
    assert "___$13.90___ - ~~$15.90~~" in md
    side = pages.product_page(shop, "crispy-fries")
    assert "_Size_" not in side and "[Add to cart](agent:add?id=crispy-fries&md2ui.commit=1)" in side
    assert "no size 'large'" in failure(shop, "{{product classic-smash size=large}}")


def test_the_product_pattern_is_what_the_page_draws(shop):
    text = (THEME.parent / "patterns" / "product-details.md").read_text()
    example = re.search(r"```markdown\n(.*?)\n```", text, re.S).group(1)
    assert example == pages.product_page(shop, "classic-smash").strip()


# --- taps: md2ui's handlers redraw the includes ------------------------------------------
@pytest.fixture
def served(shop, monkeypatch):
    """md2ui's conversation as the backend builds it, over this test's shop, with no socket."""
    monkeypatch.setattr(main, "shop", shop)
    return main.served()


TAPS: list[int] = []  # every tap's `q`, unique as a window numbers its events


def send(md, text: str) -> str:
    return asyncio.run(md.send(pages.prepare(text)))


def press(md, action: str, params: dict[str, str]) -> str:
    """A tap on the button of the page shown that *action* and *params* name, as main.tap
    hands it to md2ui; returns the page shown after it."""
    shown = md.latest
    x = next(i for i, t in enumerate(md.log.targets(shown))
             if t.action and t.action.action == action and dict(t.action.params) == params)
    TAPS.append(x)
    asyncio.run(md.receive({"t": "e", "m": shown, "x": x, "q": len(TAPS), "a": action}, "test"))
    assert md.latest != shown, "md2ui did not answer the tap"
    return md.log.markdown(md.latest)


def test_a_tap_redraws_every_stepper_of_the_product(shop, served):
    send(served, "{{home}}")
    before = served.log.markdown(served.latest)
    out = press(served, "cart-add", {"id": "classic-smash"})
    assert shop.qty("classic-smash") == 1 and pages.stepper("classic-smash", 1) in out
    assert pages.stepper("classic-smash", 0) not in out
    assert out.replace(pages.stepper("classic-smash", 1), pages.stepper("classic-smash", 0)) == before
    (line,) = served.take_handled()
    assert line.startswith('User chose "➕": cart-add {id: classic-smash}') and "redrawing {{home}}" in line


def test_a_like_redraws_its_heart(shop, served):
    send(served, "{{product triple-stack}}")
    out = press(served, "like", {"id": "triple-stack"})
    assert "triple-stack" in shop.likes
    assert "agent:unlike?id=triple-stack" in out and "agent:like?id=triple-stack" not in out


def test_the_cart_page_is_redrawn_whole(shop, served):
    shop.set_qty("classic-smash", 2)
    shop.set_qty("crispy-fries", 1)
    send(served, "{{cart}}")
    assert "`3 items`" in served.log.markdown(served.latest)
    md = press(served, "cart-add", {"id": "classic-smash", "size": "double"})
    assert "`4 items`" in md and "**$28.50**" in md and "___$32.40___" in md and "Delivery ... `Free`" in md
    assert md.strip() == pages.cart(shop).strip()  # the page the include draws
    md = press(served, "cart-remove", {"id": "crispy-fries"})
    assert "crispy-fries" not in md and md.strip() == pages.cart(shop).strip()
    shop.set_qty("classic-smash", 1)
    assert "{#empty-1}" in press(served, "cart-remove", {"id": "classic-smash", "size": "double"})


def test_the_agents_own_words_stay_and_its_rows_are_redrawn(shop, served):
    shop.set_qty("classic-smash", 1)
    send(served, "{{cart}}\n\n## You may also like\n\n{{rows crispy-fries}}")
    out = press(served, "cart-add", {"id": "crispy-fries"})
    rows = [l for l in out.split("\n") if l.startswith("- ") and "`Side`" in l]
    assert len(rows) == 1 and "`2 items`" in out and "## You may also like" in out
    assert pages.stepper("crispy-fries", 1) in out.split("## You may also like")[1]


def test_the_checkout_page_pay_label(shop, served):
    shop.set_qty("classic-smash", 1)
    send(served, "{{checkout}}\n\n{{rows classic-smash}}")  # the order review has no stepper of its own
    out = press(served, "cart-add", {"id": "classic-smash"})
    assert "[Pay $21.99](agent:checkout)" in out and re.search(r"^Items \(2\) \.\.\. \*\*\$19\.00\*\*$", out, re.M)


# --- taps with sizes -------------------------------------------------------------------
def test_a_bare_tap_is_the_default_line_and_redraws_its_spelled_row(shop, served):
    shop.set_qty("classic-smash", 1)
    send(served, "{{cart}}\n\n{{cards classic-smash}}")
    out = press(served, "cart-add", {"id": "classic-smash"})  # a bare ➕ on the card: the default line
    assert pages.stepper("classic-smash", 2) in out and pages.stepper("classic-smash", 2, {"size": "double"}) in out


def test_another_size_leaves_the_default_steppers(shop, served):
    shop.set_qty("classic-smash", 1, {"size": "triple"})
    send(served, "{{cart}}\n\n{{cards classic-smash}}")
    out = press(served, "cart-add", {"id": "classic-smash", "size": "triple"})
    assert pages.stepper("classic-smash", 2, {"size": "triple"}) in out
    assert pages.stepper("classic-smash", 0) in out  # the card is the Double, still none in the cart


def test_the_cart_page_per_sized_line(shop, served):
    shop.set_qty("classic-smash", 1)
    shop.set_qty("classic-smash", 1, {"size": "triple"})
    send(served, "{{cart}}")
    md = press(served, "cart-add", {"id": "classic-smash", "size": "triple"})
    assert md.strip() == pages.cart(shop).strip() and "**$24.00**" in md and "`3 items`" in md
    md = press(served, "cart-remove", {"id": "classic-smash", "size": "double"})  # the Double gone: only its row goes
    assert md.strip() == pages.cart(shop).strip() and "*`Double`*" not in md and "*`Triple`*" in md



@pytest.mark.parametrize("expiry", ["1230", "12/30", "12 / 2030", "122030"])
def test_an_expiry_pays_with_or_without_its_slash(shop, expiry):
    # A phone's number pad has no `/`: 1230 is December 2030, as 12/30 is.
    shop.set_qty("classic-smash", 1)
    s = shop.create_checkout()
    assert shop.pay(s.id, "4242 4242 4242 4242", expiry, "123").status == "paid"


@pytest.mark.parametrize("expiry", ["1330", "12", "ab/cd", "12/3"])
def test_a_malformed_expiry_is_refused(shop, expiry):
    shop.set_qty("classic-smash", 1)
    s = shop.create_checkout()
    with pytest.raises(ShopError):
        shop.pay(s.id, "4242 4242 4242 4242", expiry, "123")
