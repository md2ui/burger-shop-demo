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
