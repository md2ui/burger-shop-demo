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
