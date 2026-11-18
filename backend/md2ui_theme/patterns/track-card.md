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
