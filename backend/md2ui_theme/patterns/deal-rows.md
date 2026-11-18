---
name: deal-rows
description: Products on offer as rows, each with a photo, its name, the Offer chip, the new price beside the struck old one, and the quantity stepper; use for today's offers on the home page, or a short list the user reads down.
---
# Deal rows

**Use for:** a few products the user scans down, usually the ones with a lower price today. **Not for:** products picked by their photo (`product-cards`), or what is already in the cart (`cart`).

```markdown
## Today's offers

- ![Bacon BBQ](https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=200&md2ui.max_width=64&md2ui.aspect_ratio=1:1&md2ui.corner_radius=16) - [`Bacon BBQ`](agent:product?id=bacon-bbq) : `🔥 Offer` : **$11.90** ~~$13.90~~ ... ~~__[➖](agent:cart-remove?id=bacon-bbq)__~~ - **0** - __[➕](agent:cart-add?id=bacon-bbq)__
- ![Sunset Crunch](https://images.unsplash.com/photo-1603064752734-4c48eff53d05?w=200&md2ui.max_width=64&md2ui.aspect_ratio=1:1&md2ui.corner_radius=16) - [`Sunset Crunch`](agent:product?id=sunset-crunch) : `🔥 Offer` : **$9.90** ~~$11.90~~ ... __[➖](agent:cart-remove?id=sunset-crunch)__ - **1** - __[➕](agent:cart-add?id=sunset-crunch)__
- ![Burger Box Combo](https://images.unsplash.com/photo-1763689389824-dd2cea2e5772?w=200&md2ui.max_width=64&md2ui.aspect_ratio=1:1&md2ui.corner_radius=16) - [`Burger Box Combo`](agent:product?id=burger-box) : `🔥 Offer` : **$16.90** ~~$19.90~~ ... ~~__[➖](agent:cart-remove?id=burger-box)__~~ - **0** - __[➕](agent:cart-add?id=burger-box)__
```

**Why each marker**
- Each product is one `- ` line; the theme draws the list as one white card with a rule between rows.
- The small photo leads at `64`, `1:1`, rounded, with the same params on every row, then ` - `. `images.md`
- ` : ` stacks the name (a text link to the product), its label chip, then the price: the new one bold and the old one struck after it.
- ` ... ` sends the stepper to the far edge; it is the same stepper as on the cards (`product-cards`), with the cart's quantity now.
- The stepper is bare, `agent:cart-add?id=bacon-bbq`: with no `&size=` it is the product's default size, the one whose price the row shows. Only the cart and the product page name a size.
- The ➕ ➖ steppers are the app's: a tap changes the cart and the host updates every stepper of that line by itself, with no turn. That is why they stay buttons, though md2ui would write a held count for a quantity that comes back to you.
