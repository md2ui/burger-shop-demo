---
name: cart
description: The current cart: a title with the item count, one row per cart line with its photo, name, tags (its kind and its size), price and stepper, a cream summary with subtotal, delivery and total, then checkout; use when the user opens the cart or asks what is in it.
---
# Cart

**Use for:** what the cart holds now (`get_cart`). **Not for:** an empty cart (`empty-state`), or an order already paid (`order-success`, `order-status`).

```markdown
# Your cart ... `4 items`

- ![Classic Smash](https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=200&md2ui.max_width=72&md2ui.aspect_ratio=1:1&md2ui.corner_radius=18) - [`Classic Smash`](agent:product?id=classic-smash&size=double) : `Burger` *`Double`* : **$19.00** ... __[➖](agent:cart-remove?id=classic-smash&size=double)__ - **2** - __[➕](agent:cart-add?id=classic-smash&size=double)__
- ![Crispy Fries](https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=200&md2ui.max_width=72&md2ui.aspect_ratio=1:1&md2ui.corner_radius=18) - [`Crispy Fries`](agent:product?id=crispy-fries) : `Side` : **$3.90** ... __[➖](agent:cart-remove?id=crispy-fries)__ - **1** - __[➕](agent:cart-add?id=crispy-fries)__
- ![Strawberry Shake](https://images.unsplash.com/photo-1579954115545-a95591f28bfc?w=200&md2ui.max_width=72&md2ui.aspect_ratio=1:1&md2ui.corner_radius=18) - [`Strawberry Shake`](agent:product?id=strawberry-shake&size=large) : `Shake` *`Large`* : **$7.00** ... __[➖](agent:cart-remove?id=strawberry-shake&size=large)__ - **1** - __[➕](agent:cart-add?id=strawberry-shake&size=large)__

## {#summary-1}

Subtotal ... **$29.90**
Delivery ... `Free`
__Total__ ... ___$29.90___

***

[Checkout](agent:checkout) *[Keep shopping](agent:catalog)*
```

**Why each marker**
- `# Your cart` with the item count as a chip at the far edge: the number of items, quantities added up.
- Each cart line is one `- ` row in one white card: its photo at `72`, `1:1`, rounded; ` : ` stacks the name (a text link to the product at that size), its kind as a tag with its size beside it as the second kind of tag, `` `Burger` *`Double`* ``, and the line's total (price at that size × quantity) in bold; the stepper at the far edge shows the quantity. `MEANINGS.md`
- A cart line is a product at one size: a Double and a Triple Classic Smash are two rows. A row always spells its size, in its name link and its stepper, `agent:cart-add?id=classic-smash&size=double`; a side or a combo has no size, so its row has one tag and a bare stepper.
- The ➕ ➖ steppers are the app's: a tap changes that line and the host updates its stepper, its line total, the rows and the summary by itself, with no turn. That is why they stay buttons, though md2ui would write a held count for a quantity that comes back to you.
- `{#summary-1}` asks for the cream totals panel. Its lines are glued, each a label and its value at the far edge: subtotal, delivery (`Free` as a chip when it costs nothing, else the fee in bold), and the total as the panel's Display number. Spell the three labels exactly so: the host finds and updates them.
- Checkout is the main action; it opens the secure payment window (`checkout`). Keep shopping is the quieter way back to the menu.
