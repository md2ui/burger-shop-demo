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
