# This theme

# Meanings

What each spelling means in the Burger Shop.

- Write only the spellings listed here. Anything not listed, write bare: `` `Tag` ``, `⭐`, `[Label](/x)`.
- A role or a place no row names takes the bare spelling: the primary one.
- `~~…~~` around any listed spelling is its muted state: inactive, unavailable, past.
- A fixed colour belongs to its token everywhere it appears. Never use one to mark a single item.
- A pattern may declare a spelling its own shape needs; one meant everywhere is declared here.

## Icons

| Write | Means |
|---|---|
| `⭐` | an icon leading a row or a label: what the row is, such as an order update, an address, a payment, a benefit |
| `*⭐*` | the icon a page or a card is about: an order's status, a successful payment, what an empty place is missing |
| `**⭐**` | a glyph beside a caption: the rating star, the delivery clock, the calories flame |
| `***⭐***` | an icon inside a compact element |
| `"⭐"` | the glyph alone, as part of the text around it |

## Chips

| Write | Means |
|---|---|
| `` `Tag` `` | a tag: an ingredient, a kind of product, an item count; and the four product labels below, spelled exactly |
| `` *`Tag`* `` | a second kind of tag on the same item |
| `` **`Tag`** `` | a status that went well: delivered, paid |
| `` ***`Tag`*** `` | a status still open: preparing, on the way, scheduled |
| `` __`Tag`__ `` | a status that went wrong: cancelled, refunded, payment failed |
| `` _`Tag`_ `` | a tag in a compact row |

## Buttons

| Write | Means |
|---|---|
| `[Label](/x)` | the main action, at the foot of a page, a section or a band: checkout, order now, track order |
| `*[Label](/x)*` | a quieter action there: an alternative to the main one; each of a line of suggestions |
| `**[Label](/x)**` | the main action inside a card: the one an offer card is for; the category tab showing now |
| `***[Label](/x)***` | a quieter action inside a card; the other category tabs |
| `_[Label](/x)_` | the main action at the edge of a row in a list |
| `__[Label](/x)__` | a quieter action at the edge of a row |
| `___[Label](/x)___` | an action inside a compact element |
| `` [`Label`](/x) `` | a product's name, which opens its page; a way in at the edge of a section's title (view more); a link to another place; a minor action |
| `"[Label](/x)"` | a link inside a sentence |

## Icon buttons

| Write | Means |
|---|---|
| `[▶️](/x)` | the main icon action |
| `*[📞](/x)*` | an icon action |
| `**[💬](/x)**` | the main icon action inside a card |
| `***[❤️](/x)***` | an icon action inside a card |
| `_[▶️](/x)_` | the main icon action at the edge of a row |
| `__[➕](/x)__` | the quiet icon action on a product: one more `➕`, one less `➖`, like `🤍` or unlike `❤️`; also an edit at a row's edge |

## Sections

| Write | Means |
|---|---|
| `# {#headline-1}` | the home page's opening band: the shop's rating, a headline, its two actions and the hero photo; one per page, first; `patterns/headline` shows it |
| `### {#offer-1}` | one promotion card; write three in a row, numbered 1 to 3, and each takes the next brand colour; `patterns/offer-cards` shows it |
| `### {#track-1}` | the running order's status card, at the top of the home page's orders section; `patterns/home-orders` shows it |
| `## {#summary-1}` | the totals panel of a cart or a checkout: subtotal or items, delivery, total; `patterns/cart` shows it |
| `## {#status-1}` | the head of an order's status page: the big badge, the status and its progress; `patterns/order-status` shows it |
| `## {#success-1}` | the payment-successful confirmation, centred; `patterns/order-success` shows it |
| `## {#sheet-1}` | a question the customer answers before something that cannot be undone, such as cancelling an order, with its two answers; `patterns/cancel-order` shows it |
| `## {#empty-1}` | a place with nothing in it yet: an empty cart, no orders, no favourites, no results; `patterns/empty-state` shows it |

## Fixed colours

| Token | Means |
|---|---|
| a chip reading `✨ New` | a product added to the menu recently |
| a chip reading `🔥 Offer` | a product with a lower price today; write its old price struck beside the new one |
| a chip reading `⏳ Limited edition` | a product sold for a short time only |
| a chip reading `👑 Chef's Pick` | a product the kitchen recommends |
| a chip reading `Free` | a cost that is nothing today, such as delivery |
| a chip reading `Delivered` | an order delivered: a status that went well, however it is spelled |
| a chip reading `Cancelled` | an order cancelled: a status that went wrong, however it is spelled |
| a chip ending in `% off` | a discount as a percentage |
| `⭐` | a rating |
| `❤️` | a product the user liked |
| `🔥` | spicy, or the calories line |
| `🧾` | an order received |
| `👨‍🍳` | an order being prepared |
| `🛵` | an order on the way |
| `🏁` | an order delivered |
| `✔️` | a payment that went through: the badge of the confirmation |
| `✅` | an action that succeeded |
| `⚠️` | a question before something that cannot be undone, or something that could not be done |
| a button whose label contains `Cancel order` | drawn as destructive: cancelling an order; whether it is the main action or the quieter one is still its spelling's |
| `❌` | a payment or an order that failed or was cancelled |

## Patterns

This theme's shapes. Read one with guide('theme/<name>'):

- cancel-order — The question before cancelling an order, centred, with its warning badge, what happens to the money, the destructive answer and the way to keep the order; use when the customer asks to cancel, before calling cancel_order.
- cart — The current cart: a title with the item count, one row per cart line with its photo, name, tags (its kind and its size), price and stepper, a cream summary with subtotal, delivery and total, then checkout; use when the user opens the cart or asks what is in it.
- catalog — The menu as a page: a title with the count, category tabs, then a grid of product cards with their photo, label, like button, price, rating, delivery time and stepper; use for the full catalog, a category, a search or a filter.
- checkout — The order review shown while the secure payment window is open: where and when it is delivered, how it is paid and the total, with the way to reopen the payment or go back; use right after you open checkout.
- deal-rows — Products on offer as rows, each with a photo, its name, the Offer chip, the new price beside the struck old one, and the quantity stepper; use for today's offers on the home page, or a short list the user reads down.
- empty-state — A place with nothing in it yet: an icon, a title, one sentence on what would fill it, a reassurance line, and the action that fills it; use for an empty cart, no orders yet, no favourites, or a search with no results.
- headline — The home page's opening band in the brand colour, with the rating, a headline, one line under it, two actions and a burger photo beside them; use once, first, on the home dashboard.
- home-orders — The home page's section for orders, under the coloured cards: the running order's status card, the last order, and a panel suggesting to order the usual again with a line written fresh; use on home whenever the customer has orders.
- home — The home dashboard as a whole page, written fresh for the customer each time: a greeting band and three product cards in your own words, then the orders section, recommendations, today's offers and suggestions; use when the user opens the shop or asks to go home.
- offer-cards — Three cards in a row, each a different brand colour, with a kicker, a short title, one fact as a chip, one action and a round photo, written fresh for the customer; use under the headline on the home dashboard, or when the user asks for deals.
- order-history — The customer's past orders, newest first, each row opening its order with the date, items, total and status, then their usual items to order again and new products to try; use when the customer asks for their orders or what to order.
- order-status — Where an order is now: a big status badge, the current stage and arrival time (moved live while the order runs), a progress bar, every update newest first with the steps still to come muted, its items, and the way to cancel it while it can be; use when the user asks about their order.
- order-success — The payment-successful confirmation, centred: the big check badge, the message, the amount paid, the card it was charged to, the order number and arrival time, then track or go home; use right after checkout reports the order paid.
- product-cards — A run of tappable product cards, each opening its product, with its photo, label chip and like button on the photo, then the name and price, the rating and delivery time, and the calories beside the quantity stepper; use for recommendations on the home page, the catalog, and "you may also like".
- product-details — One product in full as a form: its photo beside its label, name, rating, delivery time and calories, price, description and ingredients, then its size as a choice and the quantity as a count, both held until one Add to cart press carries them, then what goes well with it; use when the user opens a product.
- track-card — A compact card for an order already placed, with its status badge, its stage, the order number and arrival time (moved live), a progress bar and the way into the full status; use on the home dashboard while an order is running.

## theme/cancel-order

---
name: cancel-order
description: The question before cancelling an order, centred, with its warning badge, what happens to the money, the destructive answer and the way to keep the order; use when the customer asks to cancel, before calling cancel_order.
---
# Cancel order

**Use for:** the confirmation the customer answers before an order is cancelled. **Not for:** an
order a rider already has, or one already cancelled: `{{cancel …}}` then says why it can't be.

```markdown
## {#sheet-1}

*⚠️*

__Cancel order BS-1042?__
***[`Preparing`](feed:stage-BS-1042)***
It can be cancelled until a rider picks it up. $28.40 goes back to Visa •••• 4242.

[Cancel order](agent:confirm-cancel?id=BS-1042) *[Keep my order](agent:order-status?id=BS-1042)*
```

**Why each marker**
- `{#sheet-1}` asks for the centred question sheet; one per page. `MEANINGS.md`
- `*⚠️*` is the large badge of a question before something that cannot be undone.
- The question is the Lead line, with the order number; under it the order's stage, a feed slot the shop moves while the sheet is on screen (`order-status`); then the sentence on until when it can be cancelled and where the money goes.
- `Cancel order` is the main action, drawn as destructive by the theme because of its label; `confirm-cancel` comes back to you, and only then do you call `cancel_order`. Keeping the order is the quieter way out, back to its page.

## theme/cart

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

## theme/catalog

---
name: catalog
description: The menu as a page: a title with the count, category tabs, then a grid of product cards with their photo, label, like button, price, rating, delivery time and stepper; use for the full catalog, a category, a search or a filter.
---
# Catalog

**Use for:** many products to pick from: the whole menu, one category, a search result, a filter such as "under $10". **Not for:** one product (`product-details`), or a short read-down list (`deal-rows`).

```markdown
# Our menu

_Showing 6 of 17 items_

... **[All](agent:catalog)** ***[🍔 Burgers](agent:catalog?category=burgers)*** ***[🥡 Combos](agent:catalog?category=combos)*** ***[🍟 Sides](agent:catalog?category=sides)*** ***[🥤 Shakes](agent:catalog?category=shakes)*** ...

### 
[
![
`👑 Chef's Pick` ... __[🤍](agent:like?id=classic-smash)__
+++++
](https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800&md2ui.aspect_ratio=5:4)
__Classic Smash__ ... ___$9.50___
**⭐** 4.8 _(1,240)_ - **⏱️** _15–20 min_
---
_690 kcal_ ... ~~__[➖](agent:cart-remove?id=classic-smash)__~~ - **0** - __[➕](agent:cart-add?id=classic-smash)__
](agent:product?id=classic-smash)

### 
[
![
`⏳ Limited edition` ... __[🤍](agent:like?id=triple-stack)__
+++++
](https://images.unsplash.com/photo-1572802419224-296b0aeee0d9?w=800&md2ui.aspect_ratio=5:4)
__Triple Stack__ ... ___$14.90___
**⭐** 4.9 _(312)_ - **⏱️** _20–25 min_
---
_1,180 kcal_ ... ~~__[➖](agent:cart-remove?id=triple-stack)__~~ - **0** - __[➕](agent:cart-add?id=triple-stack)__
](agent:product?id=triple-stack)

### 
[
![
`✨ New` ... __[❤️](agent:unlike?id=double-pickle)__
+++++
](https://images.unsplash.com/photo-1607013251379-e6eecfffe234?w=800&md2ui.aspect_ratio=5:4)
__Double Cheese & Pickle__ ... ___$12.50___
**⭐** 4.7 _(86)_ - **⏱️** _15–20 min_
---
_940 kcal_ ... __[➖](agent:cart-remove?id=double-pickle)__ - **2** - __[➕](agent:cart-add?id=double-pickle)__
](agent:product?id=double-pickle)

### 
[
![
`🔥 Offer` ... __[🤍](agent:like?id=bacon-bbq)__
+++++
](https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=800&md2ui.aspect_ratio=5:4)
__Bacon BBQ__ ... ~~$13.90~~ - ___$11.90___
**⭐** 4.6 _(958)_ - **⏱️** _20–25 min_
---
_880 kcal_ ... ~~__[➖](agent:cart-remove?id=bacon-bbq)__~~ - **0** - __[➕](agent:cart-add?id=bacon-bbq)__
](agent:product?id=bacon-bbq)

### 
[
![
`👑 Chef's Pick` ... __[🤍](agent:like?id=golden-sesame)__
+++++
](https://images.unsplash.com/photo-1610440042657-612c34d95e9f?w=800&md2ui.aspect_ratio=5:4)
__Golden Sesame Double__ ... ___$12.90___
**⭐** 4.8 _(604)_ - **⏱️** _15–20 min_
---
_980 kcal_ ... ~~__[➖](agent:cart-remove?id=golden-sesame)__~~ - **0** - __[➕](agent:cart-add?id=golden-sesame)__
](agent:product?id=golden-sesame)

### 
[
![
... __[🤍](agent:like?id=garden-deluxe)__
+++++
](https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=800&md2ui.aspect_ratio=5:4)
__Garden Deluxe__ ... ___$10.50___
**⭐** 4.5 _(421)_ - **⏱️** _15–20 min_
---
_720 kcal_ ... ~~__[➖](agent:cart-remove?id=garden-deluxe)__~~ - **0** - __[➕](agent:cart-add?id=garden-deluxe)__
](agent:product?id=garden-deluxe)

***

... [Show more](agent:catalog?page=2) ...
```

**Why each marker**
- `# Our menu` names the page in the user's words: "Burgers", "Under $10", "Results for bacon". The muted line under it says how many items are shown out of how many there are.
- The category tabs are one centred line of medium buttons: the one showing is `**[…]**`, filled, and the others are `***[…]***`, outlined. A tap comes back to you and you send the catalog again for that category.
- Every product is the tappable card from `product-cards`, written alike so they grid. A product on offer shows its old price struck before its price.
- Its stepper and heart are the app's, as on `product-cards`: a tap costs no turn, and a bare stepper is the product's default size.
- Six to nine cards at a time; more is `Show more` under the run, never a longer page.
- When nothing matches, send `empty-state` instead.

## theme/checkout

---
name: checkout
description: The order review shown while the secure payment window is open: where and when it is delivered, how it is paid and the total, with the way to reopen the payment or go back; use right after you open checkout.
---
# Checkout

**Use for:** the page behind the payment window. Payment itself happens in the app's own secure window, opened by the `open_checkout` tool; you never see or ask for card details. **Not for:** the cart before the user chose to pay (`cart`), or after paying (`order-success`).

```markdown
# Checkout

- 📍 - __Deliver to__ : _221 Bun Street, Apt 4B_ ... __[✏️](agent:change-address)__
- ⏱️ - __Arrives in__ : _about 20 minutes_
- 💳 - __Payment__ : _Secure payment window_ ... `Test mode`

## {#summary-1}

Items (4) ... **$28.40**
Delivery ... `Free`
__Total__ ... ___$28.40___

***

[Pay $28.40](agent:checkout) *[Back to cart](agent:cart)*
```

**Why each marker**
- Each detail is a `- ` row in one white card: a badge naming it, the label in the Lead tier over its value as a caption. Only the address can change, with the small icon action at its edge.
- The payment row never shows a card number: payment is the secure window's. `Test mode` says no real money moves.
- The cream summary repeats the cart's totals, in the cart's spellings (`cart`).
- `Pay` is the main action with the total in its label; tapping it opens the payment window again if the user closed it. The quieter action goes back to the cart.

## theme/deal-rows

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

## theme/empty-state

---
name: empty-state
description: A place with nothing in it yet: an icon, a title, one sentence on what would fill it, a reassurance line, and the action that fills it; use for an empty cart, no orders yet, no favourites, or a search with no results.
---
# Empty state

**Use for:** a page that would show something, but nothing is there yet. **Not for:** an error (say what failed and offer a retry), or a cart with items (`cart`).

```markdown
## {#empty-1}

*🛒*

___Your cart is empty___
Add a burger, a side or a shake and it will wait for you here. Every burger is smashed to order and delivered in about 20 minutes.

+++

✓ - __Free delivery over $25__ : _No fees, no minimum on the next order_

+++

[Browse burgers](agent:catalog) *[See offers](agent:offers)*
```

| Write | Means |
|---|---|
| `*🛒*` | the cart is empty |
| `*🧾*` | there are no orders yet |
| `*🤍*` | there are no favourites yet |
| `*🔍*` | a search or filter found nothing |

**Why each marker**
- `{#empty-1}` asks for the white empty-state panel, left aligned; one per page. `MEANINGS.md`
- The large badge is what is missing, one of the four in the table.
- The title in the Display tier, which this panel draws green; one or two sentences under it say what fills the place.
- One reassurance row: the standard badge, a short benefit in the Lead tier over its detail. Leave it out when there is nothing true to say.
- The action that fills the place is the main one; a quieter alternative beside it. For a search with no results, the main action clears the filter.

## theme/headline

---
name: headline
description: The home page's opening band in the brand colour, with the rating, a headline, one line under it, two actions and a burger photo beside them; use once, first, on the home dashboard.
---
# Headline

**Use for:** the top of the home dashboard: why to order now, and the way into the menu. **Not for:** one product (`product-details`), or a promotion (`offer-cards`).

```markdown
# {#headline-1}

___
**⭐** __4.8__ _from 12,500+ happy customers_
___Juicy burgers at your door___
Smashed to order and delivered in about 20 minutes.
+++
[Order now](agent:catalog) *[See offers](agent:offers)*
::: 1 >
![A smash burger with cheese](https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=900&md2ui.aspect_ratio=4:3&md2ui.min_width=260&md2ui.corner_radius=24)
:::1
___
***
```

**Write it fresh.** On the home page the band's words are yours, new each time, from `get_home_context`: `{{headline greeting="…" line="…" kicker="…" image=<product id> cta="…" action=<agent link>}}` draws this shape with them. The example's words are the shop's fallback, not a template.

**Why each marker**
- `{#headline-1}` asks this theme for the forest band; one per page, first. `MEANINGS.md`
- `___` above and below opens and closes the row: the words beside the photo in wide space, above it in narrow (`::: 1 >`). `structure.md`
- The first line is a small kicker: a few words of yours, or, left out, the shop's rating (`**⭐**` with the score and a caption saying from how many).
- `___…___` is the greeting in the Display tier: warm and of the moment, never a name, at most eight words. The plain line under it is one sentence about food that is true and specific: their usual, what is new or on offer.
- `+++` gives the buttons a little air. The main action is a product one the greeting leads to (add the usual burger, open a new product, open the menu or an offer); the quieter one is an alternative. Orders never go in the band: their status and reorder live in `home-orders`. On the band the main button turns mustard and the quieter one white; that is the theme's, never yours.
- The photo is the product the band is about (`image=<product id>`), else the shop's hero burger, with `md2ui.corner_radius=24`, `4:3`, and a `min_width` so it never gets squeezed. `images.md`
- `***` closes the band so the next section starts outside it.

## theme/home-orders

---
name: home-orders
description: The home page's section for orders, under the coloured cards: the running order's status card, the last order, and a panel suggesting to order the usual again with a line written fresh; use on home whenever the customer has orders.
---
# Home orders

**Use for:** everything about the customer's orders on the home page: what is running now, what
they had last, and the nudge to order it again. **Not for:** the coloured band and cards above
it, which are for products only; or the full history (`order-history`) and one order
(`order-status`). `{{home-rest note="…"}}` draws it, with your `note` as the panel's line.

```markdown
## Your orders ... [`See all`](agent:orders)

### {#track-1}

*🛵* - ***[`On the way`](feed:stage-BS-1042)*** : _Order BS-1042 • arriving around [8:58 PM](feed:arrives-BS-1042)_ ... **[Track order](agent:order-status?id=BS-1042)**
Progress: 75%

***

- [
  🏁 - __Last order BS-1040__ ... **$30.80**
  _Nov 1 • 4 items • Classic Smash, Bacon BBQ and more_ ... **`Delivered`**
  ](agent:order-status?id=BS-1040)

#### 
🔁 - __Same again for Friday night?__ : _Classic Smash, Bacon BBQ, Crispy Fries and Strawberry Shake_ ... _[Order again](agent:reorder?id=BS-1040)_

***
```

**Why each marker**
- `## Your orders` titles the section, with `See all` at its edge opening the history (`{{orders}}`).
- `### {#track-1}` is the running order's status card, only while one runs: its badge, its stage, the arrival time, `Track order`, and the progress bar (`track-card`), moved live. `***` closes it.
- The last order (the one before a running order, else the latest) is a tappable two-line card that opens it, as in `order-history`.
- `#### ` makes the white panel of the suggestion: `🔁` and your line in the Lead tier over what they had, `Order again` at the edge (`reorder`). Your line is a short nudge of at most eight words, new each time: "Same again for Friday night?". `***` closes it.
- The section is left out when there are no orders.

## theme/home

---
name: home
description: The home dashboard as a whole page, written fresh for the customer each time: a greeting band and three product cards in your own words, then the orders section, recommendations, today's offers and suggestions; use when the user opens the shop or asks to go home.
---
# Home dashboard

**Use for:** the shop's first page, and whenever the user asks for home. **Not for:** the full menu (`catalog`).

The home page is written fresh every time it is shown, from `get_home_context`: the band and
the three cards are yours, in new words each time; the rest is the shop's live data. As includes:

```
{{headline greeting="Good evening, what are you craving?" line="Your Classic Smash is one tap away, or try the new Smokehouse." image=classic-smash cta="Add a Classic Smash" action=cart-add?id=classic-smash cta2="See the menu" action2=catalog}}

{{offer product=classic-smash kicker="Your usual" title="Classic Smash again?" chip="Ordered 3 times"}}
{{offer product=smokehouse kicker="New for you" title="Meet the Smokehouse" chip="✨ New"}}
{{offer promo=box-deal kicker="Combo deal" title="Burger, fries and a soda"}}

{{home-rest note="Same again for Friday night?"}}
```

Another visit, another page: `greeting="Happy Friday, burger time?"`, `line="The Bacon BBQ is $2 off today, and the Fries & BBQ Dip is new."`, the Bacon BBQ as the offer, the Fries & BBQ Dip as the new thing, the "Made fresh" promotion last, `note="Your fries are on the way, want a shake?"`. What the words say is always true: a time, a product, a price from the context.

**The band and the three coloured cards are for products** and their calls to action: product, cart-add, offer, offers, catalog, picks. **Orders have their own section** under the cards (`home-orders`): the running order's status, the last order, and your `note` suggesting to order again. Never an order number, a status or a reorder in the band or the cards.

The page, section by section:

1. `headline`, the forest band, always first: a greeting for the moment, one specific line, the main action.
2. `offer-cards`, three reasons to tap, all products: one of their usual products, something new for them, a live promotion.
3. `home-orders`, when they have orders: the running order's status, the last order, the nudge to order again.
4. `product-cards` under `## Recommended for you`: three products, the shop's top picks or the user's likes, then `View more burgers`.
5. `deal-rows` under `## Today's offers`: the products with a lower price today.
6. The suggestions line, written as below.

```markdown
## What are you craving?

... *[🔥 Something spicy](agent:catalog?filter=spicy)* *[🍔 Best sellers](agent:catalog?sort=popular)* *[🥤 Shakes](agent:catalog?category=shakes)* *[🍟 Sides](agent:catalog?category=sides)* *[🏷️ Under $10](agent:catalog?max_price=10)* ...
```

**Why each marker**
- The suggestions are peers on one line, each a quieter big button with its icon inside, so they wrap into centred rows at any width. Four to six, each a few words the user might ask next. `patterns/suggestions`
- Each is an `agent:` link that comes back to you as the request; answer it with the page it asks for, usually `catalog` filtered.
- Never repeat the same product twice on the home page: `{{home-rest}}` leaves out the products your cards feature, and a product in the recommendations is left out of today's offers.

## theme/offer-cards

---
name: offer-cards
description: Three cards in a row, each a different brand colour, with a kicker, a short title, one fact as a chip, one action and a round photo, written fresh for the customer; use under the headline on the home dashboard, or when the user asks for deals.
---
# Offer cards

**Use for:** three personal reasons to tap under the headline, all products: one of the customer's usual products, something new for them, a live promotion, side by side. **Never for orders**, which have `home-orders`. **Not for:** the single products on offer, which are `deal-rows`; or one product (`product-details`).

```markdown
### {#offer-1}
_Irresistibly tasty_
___Made fresh, served hot___
`Up to 40% off`
**[Order now](agent:offer?id=made-fresh)**
::: 1
![Burger with sauces](https://images.unsplash.com/photo-1776260486895-a35357e2505b?w=600&md2ui.aspect_ratio=1:1&md2ui.max_width=88&md2ui.min_width=88&md2ui.corner_radius=44)
:::0

### {#offer-2}
_Limited time_
___Loaded beef burgers___
`Up to 30% off`
**[Order now](agent:offer?id=loaded-beef)**
::: 1
![Deconstructed burger](https://images.unsplash.com/photo-1530554764233-e79e16c91d08?w=600&md2ui.aspect_ratio=1:1&md2ui.max_width=88&md2ui.min_width=88&md2ui.corner_radius=44)
:::0

### {#offer-3}
_Combo deal_
___Burger, fries and a soda___
`Box deal $16.90`
**[Get the box](agent:offer?id=box-deal)**
::: 1
![Burger box combo](https://images.unsplash.com/photo-1763689389824-dd2cea2e5772?w=600&md2ui.aspect_ratio=1:1&md2ui.max_width=88&md2ui.min_width=88&md2ui.corner_radius=44)
:::0

***
```

**Write them fresh.** On the home page the three cards are yours, chosen and worded new each time from `get_home_context`: three `{{offer product=<id> …}}` or `{{offer promo=<id> …}}` lines in a row draw this shape, numbered and coloured in the order written, with the product's or promotion's photo. Make them three different reasons to tap, all about products: one of their usual products, something new for them, a live promotion. Their actions are product ones (product, cart-add, offer, offers, catalog, picks): orders go in `home-orders`. Kicker two or three words, title at most five, chip one true fact, cta one or two words.

**Why each marker**
- `{#offer-N}` asks for the promo card, numbered 1, 2, 3. The theme deals each one the next colour (forest, mustard, orange), so write three and never pick a colour yourself. `MEANINGS.md`
- The three cards are written alike with no `___` between them, so they grid as one row and stack on a phone. `repetition.md`
- In each card the words come first: a muted kicker, the title in the Display tier, the deal as a chip, then the card's main action `**[…]**`. The card's colour flips the chip and the button so they stay legible.
- `::: 1` and `:::0` put the round photo beside the words at a fixed 88 px; `corner_radius` at half the width makes it a circle.
- A deal that is a percentage ends in `% off` (`Up to 40% off`); the theme pins that chip orange.
- `***` closes the last card, so what follows is not inside it.

## theme/order-history

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

## theme/order-status

---
name: order-status
description: Where an order is now: a big status badge, the current stage and arrival time (moved live while the order runs), a progress bar, every update newest first with the steps still to come muted, its items, and the way to cancel it while it can be; use when the user asks about their order.
---
# Order status

**Use for:** one order the user already paid (`get_order`). **Not for:** the moment of payment (`order-success`), or no order at all (`empty-state`).

```markdown
## {#status-1}

*👨‍🍳*

___Order BS-1042___
_Arriving around [8:22 PM](feed:arrives-BS-1042)_ ... ***[`Preparing`](feed:stage-BS-1042)***
Progress: 40%

## Updates

- 👨‍🍳 - __Preparing your order__ : _The kitchen started on 4 items_ ... _8:17 PM_
- 🧾 - __Order received__ : _Paid with Visa •••• 4242_ ... _8:16 PM_
- ~~🛵~~ - _On the way_ ... _about 8:19 PM_
- ~~🏁~~ - _Delivered_ ... _about 8:22 PM_

## Items

- 2 × Classic Smash ... **$19.00**
- 1 × Crispy Fries ... **$3.90**
- 1 × Strawberry Shake ... **$5.50**
- Delivery ... `Free`
- __Total__ ... __$28.40__

... *[Contact support](agent:support?order=BS-1042)* *[Cancel order](agent:cancel-order?id=BS-1042)* ...
```

| Write | Means |
|---|---|
| `*🧾*` | received: paid and sent to the kitchen |
| `*👨‍🍳*` | preparing: the kitchen is cooking it |
| `*🛵*` | on the way: a rider has it |
| `*🏁*` | delivered |
| `*❌*` | cancelled: the customer cancelled it, and the money went back |

**Why each marker**
- `{#status-1}` asks for the centred status card; one per page, first. `MEANINGS.md`
- The large badge is the current status, one of the four in the table, so the theme gives it the status's colour.
- While the order runs, the order number in the Display tier, then the arrival time as a caption with the stage chip at its far edge (`Received`, `Preparing`, `On the way`), and the bar. The stage and the arrival are feed slots named by the order (`feed:stage-BS-1042`, `feed:arrives-BS-1042`) and the bar is keyed `Progress`: the shop moves all three while the page is on screen, so nothing else on the card names the stage.
- A delivered or cancelled order is a receipt, with no slots: its status in the Display tier (`___Delivered___`), one sentence on what happened, then the order number and when as a caption.
- `Progress: 75%` is the bar: how far along the order is, from `get_order`.
- `## Updates` lists each update newest first: the status badge, what happened in the Lead tier over a detail, the time at the far edge. The steps still to come are muted: `~~🏁~~` and their words as a caption, with the expected time.
- `## Items` lists what was ordered, each line with its total, then delivery and the total in the Lead tier.
- Two quieter actions close the page, centred: contact support, and `Cancel order` while the order can still be cancelled (received or preparing), else `Order again`. `Cancel order` is drawn as destructive; it asks first (`cancel-order`).
- A cancelled order has no progress bar: its first update says why, and where the money went.

## theme/order-success

---
name: order-success
description: The payment-successful confirmation, centred: the big check badge, the message, the amount paid, the card it was charged to, the order number and arrival time, then track or go home; use right after checkout reports the order paid.
---
# Order success

**Use for:** the answer to a payment that went through. **Not for:** a payment that failed or was cancelled (a short message and `cart` again), or a later look at the order (`order-status`).

```markdown
## {#success-1}

*✔️*

__Payment successful__
___$28.40___
"💳" Visa •••• 4242

---

- Order ... **BS-1042**
- Arrives ... **about 7:42 PM**
- Items ... **4**

[Track order](agent:order-status?id=BS-1042) *[Back to home](agent:home)*
```

**Why each marker**
- `{#success-1}` asks for the centred white sheet; one per page. `MEANINGS.md`
- `*✔️*` is the large badge of a payment that went through; the theme gives it its colours.
- `__…__` says what happened in the Lead tier; the amount paid is the Display number; under it the card, masked, exactly as the payment window reported it, with the card glyph quoted so it sits in the line.
- `---` draws a rule under the head; the details below it sit in rows inside the sheet: the order number, when it arrives, how many items.
- Tracking is the main action; going home the quieter one.

## theme/product-cards

---
name: product-cards
description: A run of tappable product cards, each opening its product, with its photo, label chip and like button on the photo, then the name and price, the rating and delivery time, and the calories beside the quantity stepper; use for recommendations on the home page, the catalog, and "you may also like".
---
# Product cards

**Use for:** products the user picks by their photo, three or more of them. **Not for:** products the user reads down, such as offers or the cart (`deal-rows`, `cart`), or one product in full (`product-details`).

```markdown
## Recommended for you ... [`View more`](agent:catalog)

### 
[
![
`👑 Chef's Pick` ... __[🤍](agent:like?id=classic-smash)__
+++++
](https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800&md2ui.aspect_ratio=5:4)
__Classic Smash__ ... ___$9.50___
**⭐** 4.8 _(1,240)_ - **⏱️** _15–20 min_
---
_690 kcal_ ... ~~__[➖](agent:cart-remove?id=classic-smash)__~~ - **0** - __[➕](agent:cart-add?id=classic-smash)__
](agent:product?id=classic-smash)

### 
[
![
`✨ New` ... __[❤️](agent:unlike?id=double-pickle)__
+++++
](https://images.unsplash.com/photo-1607013251379-e6eecfffe234?w=800&md2ui.aspect_ratio=5:4)
__Double Cheese & Pickle__ ... ___$12.50___
**⭐** 4.7 _(86)_ - **⏱️** _15–20 min_
---
_940 kcal_ ... __[➖](agent:cart-remove?id=double-pickle)__ - **2** - __[➕](agent:cart-add?id=double-pickle)__
](agent:product?id=double-pickle)

### 
[
![
... __[🤍](agent:like?id=garden-deluxe)__
+++++
](https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=800&md2ui.aspect_ratio=5:4)
__Garden Deluxe__ ... ___$10.50___
**⭐** 4.5 _(421)_ - **⏱️** _15–20 min_
---
_720 kcal_ ... ~~__[➖](agent:cart-remove?id=garden-deluxe)__~~ - **0** - __[➕](agent:cart-add?id=garden-deluxe)__
](agent:product?id=garden-deluxe)

***

... [View more burgers](agent:catalog?category=burgers) ...
```

| Write | Means |
|---|---|
| `__[🤍](agent:like?id=…)__` | the product is not a favourite; tapping it likes it |
| `__[❤️](agent:unlike?id=…)__` | the product is a favourite; tapping it removes the like |
| `__[➖](agent:cart-remove?id=…)__ - **N** - __[➕](agent:cart-add?id=…)__` | the stepper: how many are in the cart, with one less and one more |
| `~~__[➖](…)__~~` | the minus when the cart holds none: nothing to remove |

**Why each marker**
- `### ` with no title makes one white card per product; the cards are written alike, so they grid three across and stack on a phone. `repetition.md`
- The photo leads at `5:4`, and the same params go on every card. Its alt slot is the top of the card, drawn on the photo: the product's label chip first (`✨ New`, `🔥 Offer`, `⏳ Limited edition`, `👑 Chef's Pick`, spelled exactly so the theme colours it, or nothing), then ` ... ` and the like button at the far corner. `+++++` gives the photo its height. `images.md`
- The name is in the Lead tier; the price is the card's Display number at the far edge. A product on offer shows its old price struck before it: `~~$13.90~~ - ___$11.90___`.
- The whole card is wrapped in `[ … ](agent:product?id=…)`, so a tap anywhere on it opens the product's page. The heart and the stepper inside it stay their own buttons: the innermost target wins. `elements.md`
- `**⭐**` and `**⏱️**` are the small glyphs beside their captions: the rating with its review count, and the delivery time as a range.
- `---` draws the light rule; under it, the calories as a caption and the stepper at the far edge. The stepper is the same on every card, with ` - ` between its three pieces, and the number is what the cart holds now, `0` included. The host updates every stepper and like by itself when the user taps one, so never send the page again just to change a number. `MEANINGS.md`
- The stepper is bare, `agent:cart-add?id=classic-smash`: with no `&size=` it is the product's default size, the one whose price the card shows. The ➕ ➖ and 🤍 ❤️ taps are the app's and cost no turn, so they stay buttons, though md2ui would write a held count for a quantity that comes back to you.
- `***` closes the run; "View more" is the main action under it, centred.

## theme/product-details

---
name: product-details
description: One product in full as a form: its photo beside its label, name, rating, delivery time and calories, price, description and ingredients, then its size as a choice and the quantity as a count, both held until one Add to cart press carries them, then what goes well with it; use when the user opens a product.
---
# Product details

**Use for:** one product, when the user taps its name or asks about it, with the size and the
quantity chosen on the page and sent in one turn. **Not for:** several products (`catalog`), or
what is in the cart (`cart`).

```markdown
___
![Classic Smash](https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=1200&md2ui.aspect_ratio=1:1&md2ui.min_width=300&md2ui.corner_radius=28)
::: 1 >
`👑 Chef's Pick` ... __[🤍](agent:like?id=classic-smash)__
# Classic Smash
**⭐** __4.8__ _1,240 reviews_ - **⏱️** _15–20 min_ - **🔥** _690 kcal_
+++
___$9.50___
+++
Two smashed beef patties with crispy edges, American cheese, white onion, pickles and house sauce on a toasted potato bun.

_Ingredients_
`Beef` `American cheese` `Onion` `Pickles` `House sauce` `Potato bun`
+++
_Size_
*[Single](agent:size?id=classic-smash&size=single&md2ui.choice=size)* | [Double](agent:size?id=classic-smash&size=double&md2ui.choice=size) | *[Triple](agent:size?id=classic-smash&size=triple&md2ui.choice=size)*

Quantity: ➖ [1/9] ➕

[Add to cart](agent:add?id=classic-smash&size=double&md2ui.commit=1)
:::1.2
___
***

## Goes well with

- ![Crispy Fries](https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=200&md2ui.max_width=64&md2ui.aspect_ratio=1:1&md2ui.corner_radius=16) - [`Crispy Fries`](agent:product?id=crispy-fries) : **$3.90** ... ~~__[➖](agent:cart-remove?id=crispy-fries)__~~ - **0** - __[➕](agent:cart-add?id=crispy-fries)__
- ![Cookies & Cream Shake](https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=200&md2ui.max_width=64&md2ui.aspect_ratio=1:1&md2ui.corner_radius=16) - [`Cookies & Cream Shake`](agent:product?id=cookie-shake) : **$5.90** ... ~~__[➖](agent:cart-remove?id=cookie-shake)__~~ - **0** - __[➕](agent:cart-add?id=cookie-shake)__
```

**Why each marker**
- `___` above and below holds the row: the photo beside the details in wide space and above them on a phone (`::: 1 >`); `:::1.2` gives the details a little more room. `structure.md`
- The photo is large, `1:1`, rounded, with a `min_width` so it never shrinks to a thumbnail.
- The first line is the label chip (or nothing) and the like button at the far edge, `🤍` or `❤️` as the product is liked now.
- `# ` is the product's name. Under it, the small star with the score and review count, the delivery time and the calories, ` - ` between them.
- The price is the page's one Display number, at the size shown; a product on offer shows the old price struck beside it: `___$11.90___ - ~~$13.90~~`. It stays the shown size's until the press: the page is not sent again for a held choice.
- The description is the product's own, then the ingredients as tags under a caption.
- `_Size_` is the choice's label, on its own line above its options. Each option is a link with `md2ui.choice=size`, the size shown the main variant and the others `*…*`; ` | ` between them draws one segmented control. Burgers come Single, Double, Triple; shakes Regular, Large; a side or a combo has no size row. A tap moves the choice on the page and sends nothing.
- `Quantity: ➖ [1/9] ➕` is a count: whole numbers from 0 to 9 between ➖ and ➕, starting at 1. Its taps send nothing either; the label before the colon is what the press reports.
- `[Add to cart](agent:add?id=…&size=…&md2ui.commit=1)` is the one press that keeps. Its link names the size shown (no `size` for a product without sizes), and it carries what the customer changed, in one turn: `User chose "Add to cart": add {id: classic-smash, size: double}, with size: "Triple", "Quantity" at 4`. A value the sentence leaves out is as the page drew it: the link's size, a quantity of 1. `md2ui.commit` is the app's, never part of the action. The answer is update_cart with that size and quantity added, then `{{cart}}` or a short confirmation.
- The heart and the ➕ ➖ steppers under "Goes well with" are the app's buttons: they change the likes or the cart with no turn, so md2ui's "write a count" advice does not apply to them.
- "Goes well with" is two or three sides or shakes as `deal-rows`.

## theme/track-card

---
name: track-card
description: A compact card for an order already placed, with its status badge, its stage, the order number and arrival time (moved live), a progress bar and the way into the full status; use on the home dashboard while an order is running.
---
# Track card

**Use for:** the running order's status, at the top of the home page's orders section (`home-orders`, where it is a `###` card). **Not for:** the full status with every update (`order-status`). Leave it out when there is no running order.

```markdown
## {#track-1}

*🛵* - ***[`On the way`](feed:stage-BS-1042)*** : _Order BS-1042 • arriving around [7:42 PM](feed:arrives-BS-1042)_ ... **[Track order](agent:order-status?id=BS-1042)**
Progress: 75%
```

| Write | Means |
|---|---|
| `*🧾*` | the order was received |
| `*👨‍🍳*` | the kitchen is preparing it |
| `*🛵*` | a rider is on the way with it |
| `*🏁*` | it was delivered |

**Why each marker**
- `{#track-1}` asks for the tracking card, outlined like the product cards; one per page, right after the headline and offers. `MEANINGS.md`
- The large badge leads the row: one of the four status glyphs in the table, so the theme gives it the status's colour.
- ` : ` stacks the stage chip over the order number and arrival time as a caption. The stage and the arrival are feed slots named by the order, and the bar is keyed `Progress`: the shop moves them while the card is on screen.
- ` ... ` puts the card's main action at the far edge.
- `Progress: 75%` on its own line is the progress bar: the status's words, then how far along the order is, from `get_order`.
