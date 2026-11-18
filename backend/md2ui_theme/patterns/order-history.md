---
name: order-history
description: The customer's past orders, newest first, each row opening its order with the date, items, total and status, then their usual items to order again and new products to try; use when the customer asks for their orders or what to order.
---
# Order history

**Use for:** "my orders", "what did I order last time", "order again", and recommendations from
what the customer usually orders (`get_orders`, `get_recommendations`). **Not for:** one order in
full (`order-status`), or no orders at all (`empty-state`). The include `{{orders}}` draws it all;
`{{picks}}` draws only the two recommendation sections.

```markdown
# Your orders ... `7 orders`

_5 delivered, about $26.72 an order_

- [
  👨‍🍳 - __Order BS-1042__ ... **$28.40**
  _Today • 4 items • Classic Smash, Crispy Fries and more_ ... ***`Preparing`***
  ](agent:order-status?id=BS-1042)
- [
  🏁 - __Order BS-1040__ ... **$30.80**
  _Nov 1 • 4 items • Classic Smash, Bacon BBQ and more_ ... **`Delivered`**
  ](agent:order-status?id=BS-1040)
- [
  ❌ - __Order BS-1039__ ... **$32.80**
  _Oct 27 • 4 items • Smokehouse, Classic Smash and more_ ... __`Cancelled`__
  ](agent:order-status?id=BS-1039)
- [
  🏁 - __Order BS-1037__ ... **$19.79**
  _Oct 22 • 2 items • Golden Sesame Double, Crispy Fries_ ... **`Delivered`**
  ](agent:order-status?id=BS-1037)

## Your usual

- ![Crispy Fries](https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=200&md2ui.max_width=64&md2ui.aspect_ratio=1:1&md2ui.corner_radius=16) - [`Crispy Fries`](agent:product?id=crispy-fries) : **$3.90** ... ~~__[➖](agent:cart-remove?id=crispy-fries)__~~ - **0** - __[➕](agent:cart-add?id=crispy-fries)__
- ![Classic Smash](https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=200&md2ui.max_width=64&md2ui.aspect_ratio=1:1&md2ui.corner_radius=16) - [`Classic Smash`](agent:product?id=classic-smash) : `👑 Chef's Pick` : **$9.50** ... ~~__[➖](agent:cart-remove?id=classic-smash)__~~ - **0** - __[➕](agent:cart-add?id=classic-smash)__

## Something new to try

_New on the menu, if you like the Classic Smash_

### 
[
![
`✨ New` ... __[🤍](agent:like?id=double-pickle)__
+++++
](https://images.unsplash.com/photo-1607013251379-e6eecfffe234?w=800&md2ui.aspect_ratio=5:4)
__Double Cheese & Pickle__ ... ___$12.50___
**⭐** 4.7 _(86)_ - **⏱️** _15–20 min_
---
_940 kcal_ ... ~~__[➖](agent:cart-remove?id=double-pickle)__~~ - **0** - __[➕](agent:cart-add?id=double-pickle)__
](agent:product?id=double-pickle)

***
```

| Write | Means |
|---|---|
| `🧾` `👨‍🍳` `🛵` | an order still running: received, preparing, on the way |
| `🏁` | an order delivered |
| `❌` | an order cancelled |

**Why each marker**
- `# Your orders` with the number of orders as a chip at the far edge; the caption under it says how many were delivered and the usual spend.
- Each order is a `- ` item whose two lines are wrapped in `[ … ](agent:order-status?id=…)`, so tapping anywhere on it opens that order; the items grid as cards. Two lines at least: one line inside a link is a button. The card holds no other button: a link card takes every tap inside it.
- The first line leads with the status badge, then the order number in the Lead tier and its total at the far edge. The caption line under it says the date, the item count and the first items' names, `•` between them, with the status chip at the far edge: `***`…`***` still running, `**`…`**` delivered, `__`…`__` cancelled. `MEANINGS.md` A running order's chip here is plain, not fed: a row is a link card, and a slot is never inside a link's label.
- `## Your usual` lists the products ordered most, as `deal-rows` with their steppers: one tap adds one again, at the product's default size, with no turn (the steppers are the app's).
- `## Something new to try` shows products never ordered, close to the usual ones, as `product-cards`; the caption says why, from `get_recommendations`.
