---
name: catalog
description: The menu as a page: a title with the count, category tabs, then a grid of product cards with their photo, label, like button, price, rating, delivery time and stepper; use for the full catalog, a category, a search or a filter.
---
# Catalog

**Use for:** many products to pick from: the whole menu, one category, a search result, a filter such as "under $10". **Not for:** one product (`product-details`), or a short read-down list (`deal-rows`).

```markdown
# Our menu

_Showing 6 of 17 items_

... **[All](agent:catalog)** ***[🍔 Burgers](agent:catalog?category=burgers)*** ***[🥡 Combos](agent:catalog?category=combos)*** ***[🍟 Sides](agent:catalog?category=sides)*** ***[🥤 Shakes](agent:catalog?category=shakes)*** ...

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
`⏳ Limited edition` ... __[🤍](agent:like?id=triple-stack)__
+++++
](https://images.unsplash.com/photo-1572802419224-296b0aeee0d9?w=800&md2ui.aspect_ratio=5:4)
__Triple Stack__ ... ___$14.90___
**⭐** 4.9 _(312)_ - **⏱️** _20–25 min_
---
_1,180 kcal_ ... ~~__[➖](agent:cart-remove?id=triple-stack)__~~ - **0** - __[➕](agent:cart-add?id=triple-stack)__
](agent:product?id=triple-stack)

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
`🔥 Offer` ... __[🤍](agent:like?id=bacon-bbq)__
+++++
](https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=800&md2ui.aspect_ratio=5:4)
__Bacon BBQ__ ... ~~$13.90~~ - ___$11.90___
**⭐** 4.6 _(958)_ - **⏱️** _20–25 min_
---
_880 kcal_ ... ~~__[➖](agent:cart-remove?id=bacon-bbq)__~~ - **0** - __[➕](agent:cart-add?id=bacon-bbq)__
](agent:product?id=bacon-bbq)

### 
[
![
`👑 Chef's Pick` ... __[🤍](agent:like?id=golden-sesame)__
+++++
](https://images.unsplash.com/photo-1610440042657-612c34d95e9f?w=800&md2ui.aspect_ratio=5:4)
__Golden Sesame Double__ ... ___$12.90___
**⭐** 4.8 _(604)_ - **⏱️** _15–20 min_
---
_980 kcal_ ... ~~__[➖](agent:cart-remove?id=golden-sesame)__~~ - **0** - __[➕](agent:cart-add?id=golden-sesame)__
](agent:product?id=golden-sesame)

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

... [Show more](agent:catalog?page=2) ...
```

**Why each marker**
- `# Our menu` names the page in the user's words: "Burgers", "Under $10", "Results for bacon". The muted line under it says how many items are shown out of how many there are.
- The category tabs are one centred line of medium buttons: the one showing is `**[…]**`, filled, and the others are `***[…]***`, outlined. A tap comes back to you and you send the catalog again for that category.
- Every product is the tappable card from `product-cards`, written alike so they grid. A product on offer shows its old price struck before its price.
- Its stepper and heart are the app's, as on `product-cards`: a tap costs no turn, and a bare stepper is the product's default size.
- Six to nine cards at a time; more is `Show more` under the run, never a longer page.
- When nothing matches, send `empty-state` instead.
