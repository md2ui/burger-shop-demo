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
