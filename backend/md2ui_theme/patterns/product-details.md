---
name: product-details
description: One product in full as a form: its photo beside its label, name, rating, delivery time and calories, price, description and ingredients, then its size as a choice and the quantity as a count, both held until one Add to cart press carries them, then what goes well with it; use when the user opens a product.
---
# Product details

**Use for:** one product, when the user taps its name or asks about it, with the size and the
quantity chosen on the page and sent in one turn. **Not for:** several products (`catalog`), or
what is in the cart (`cart`).

```markdown
___
![Classic Smash](https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=1200&md2ui.aspect_ratio=1:1&md2ui.min_width=300&md2ui.corner_radius=28)
::: 1 >
`👑 Chef's Pick` ... __[🤍](agent:like?id=classic-smash)__
# Classic Smash
**⭐** __4.8__ _1,240 reviews_ - **⏱️** _15–20 min_ - **🔥** _690 kcal_
+++
___$9.50___
+++
Two smashed beef patties with crispy edges, American cheese, white onion, pickles and house sauce on a toasted potato bun.

_Ingredients_
`Beef` `American cheese` `Onion` `Pickles` `House sauce` `Potato bun`
+++
_Size_
*[Single](agent:size?id=classic-smash&size=single&md2ui.choice=size)* | [Double](agent:size?id=classic-smash&size=double&md2ui.choice=size) | *[Triple](agent:size?id=classic-smash&size=triple&md2ui.choice=size)*

Quantity: ➖ [1/9] ➕

[Add to cart](agent:add?id=classic-smash&size=double&md2ui.commit=1)
:::1.2
___
***

## Goes well with

- ![Crispy Fries](https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=200&md2ui.max_width=64&md2ui.aspect_ratio=1:1&md2ui.corner_radius=16) - [`Crispy Fries`](agent:product?id=crispy-fries) : **$3.90** ... ~~__[➖](agent:cart-remove?id=crispy-fries)__~~ - **0** - __[➕](agent:cart-add?id=crispy-fries)__
- ![Cookies & Cream Shake](https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=200&md2ui.max_width=64&md2ui.aspect_ratio=1:1&md2ui.corner_radius=16) - [`Cookies & Cream Shake`](agent:product?id=cookie-shake) : **$5.90** ... ~~__[➖](agent:cart-remove?id=cookie-shake)__~~ - **0** - __[➕](agent:cart-add?id=cookie-shake)__
```

**Why each marker**
- `___` above and below holds the row: the photo beside the details in wide space and above them on a phone (`::: 1 >`); `:::1.2` gives the details a little more room. `structure.md`
- The photo is large, `1:1`, rounded, with a `min_width` so it never shrinks to a thumbnail.
- The first line is the label chip (or nothing) and the like button at the far edge, `🤍` or `❤️` as the product is liked now.
- `# ` is the product's name. Under it, the small star with the score and review count, the delivery time and the calories, ` - ` between them.
- The price is the page's one Display number, at the size shown; a product on offer shows the old price struck beside it: `___$11.90___ - ~~$13.90~~`. It stays the shown size's until the press: the page is not sent again for a held choice.
- The description is the product's own, then the ingredients as tags under a caption.
- `_Size_` is the choice's label, on its own line above its options. Each option is a link with `md2ui.choice=size`, the size shown the main variant and the others `*…*`; ` | ` between them draws one segmented control. Burgers come Single, Double, Triple; shakes Regular, Large; a side or a combo has no size row. A tap moves the choice on the page and sends nothing.
- `Quantity: ➖ [1/9] ➕` is a count: whole numbers from 0 to 9 between ➖ and ➕, starting at 1. Its taps send nothing either; the label before the colon is what the press reports.
- `[Add to cart](agent:add?id=…&size=…&md2ui.commit=1)` is the one press that keeps. Its link names the size shown (no `size` for a product without sizes), and it carries what the customer changed, in one turn: `User chose "Add to cart": add {id: classic-smash, size: double}, with size: "Triple", "Quantity" at 4`. A value the sentence leaves out is as the page drew it: the link's size, a quantity of 1. `md2ui.commit` is the app's, never part of the action. The answer is update_cart with that size and quantity added, then `{{cart}}` or a short confirmation.
- The heart and the ➕ ➖ steppers under "Goes well with" are the app's buttons: they change the likes or the cart with no turn, so md2ui's "write a count" advice does not apply to them.
- "Goes well with" is two or three sides or shakes as `deal-rows`.
