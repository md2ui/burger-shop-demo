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
