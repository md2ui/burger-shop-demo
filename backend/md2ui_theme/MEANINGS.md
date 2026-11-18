# Meanings

What each spelling means in the Burger Shop.

- Write only the spellings listed here. Anything not listed, write bare: `` `Tag` ``, `⭐`, `[Label](/x)`.
- A role or a place no row names takes the bare spelling: the primary one.
- `~~…~~` around any listed spelling is its muted state: inactive, unavailable, past.
- A fixed colour belongs to its token everywhere it appears. Never use one to mark a single item.
- A pattern may declare a spelling its own shape needs; one meant everywhere is declared here.

<!-- For theme authors. This file is the project's whole contract (THEME_GUIDE.md §10): it
does not extend md2ui's defaults. Means is what agents read: never a colour, a size or a
measurement. Size is for the lint; Slot is md2ui's; agents see neither. -->

## Icons

| Write | Means | Size | Slot |
|---|---|---|---|
| `⭐` | an icon leading a row or a label: what the row is, such as an order update, an address, a payment, a benefit | standard | icon-label |
| `*⭐*` | the icon a page or a card is about: an order's status, a successful payment, what an empty place is missing | large | icon-subject |
| `**⭐**` | a glyph beside a caption: the rating star, the delivery clock, the calories flame | small | icon-dense |
| `***⭐***` | an icon inside a compact element | extra small | compact |
| `"⭐"` | the glyph alone, as part of the text around it | | inline |

## Chips

| Write | Means | Size |
|---|---|---|
| `` `Tag` `` | a tag: an ingredient, a kind of product, an item count; and the four product labels below, spelled exactly | |
| `` *`Tag`* `` | a second kind of tag on the same item | |
| `` **`Tag`** `` | a status that went well: delivered, paid | |
| `` ***`Tag`*** `` | a status still open: preparing, on the way, scheduled | |
| `` __`Tag`__ `` | a status that went wrong: cancelled, refunded, payment failed | |
| `` _`Tag`_ `` | a tag in a compact row | small |

## Buttons

| Write | Means | Size | Slot |
|---|---|---|---|
| `[Label](/x)` | the main action, at the foot of a page, a section or a band: checkout, order now, track order | | foot-main |
| `*[Label](/x)*` | a quieter action there: an alternative to the main one; each of a line of suggestions | | foot-quieter |
| `**[Label](/x)**` | the main action inside a card: the one an offer card is for; the category tab showing now | medium | card-main |
| `***[Label](/x)***` | a quieter action inside a card; the other category tabs | medium | card-quieter |
| `_[Label](/x)_` | the main action at the edge of a row in a list | small | row-main |
| `__[Label](/x)__` | a quieter action at the edge of a row | small | row-quieter |
| `___[Label](/x)___` | an action inside a compact element | extra small | compact |
| `` [`Label`](/x) `` | a product's name, which opens its page; a way in at the edge of a section's title (view more); a link to another place; a minor action | | title-edge, card-way-in, nav, minor |
| `"[Label](/x)"` | a link inside a sentence | | inline |

## Icon buttons

| Write | Means | Size | Slot |
|---|---|---|---|
| `[▶️](/x)` | the main icon action | | foot-main |
| `*[📞](/x)*` | an icon action | | foot-quieter |
| `**[💬](/x)**` | the main icon action inside a card | medium | card-main |
| `***[❤️](/x)***` | an icon action inside a card | medium | card-quieter |
| `_[▶️](/x)_` | the main icon action at the edge of a row | small | row-main |
| `__[➕](/x)__` | the quiet icon action on a product: one more `➕`, one less `➖`, like `🤍` or unlike `❤️`; also an edit at a row's edge | small | row-quieter, title-edge |

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
