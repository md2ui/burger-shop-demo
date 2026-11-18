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
