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
