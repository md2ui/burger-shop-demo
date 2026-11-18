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
