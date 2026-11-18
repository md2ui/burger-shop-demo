---
name: headline
description: The home page's opening band in the brand colour, with the rating, a headline, one line under it, two actions and a burger photo beside them; use once, first, on the home dashboard.
---
# Headline

**Use for:** the top of the home dashboard: why to order now, and the way into the menu. **Not for:** one product (`product-details`), or a promotion (`offer-cards`).

```markdown
# {#headline-1}

___
**⭐** __4.8__ _from 12,500+ happy customers_
___Juicy burgers at your door___
Smashed to order and delivered in about 20 minutes.
+++
[Order now](agent:catalog) *[See offers](agent:offers)*
::: 1 >
![A smash burger with cheese](https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=900&md2ui.aspect_ratio=4:3&md2ui.min_width=260&md2ui.corner_radius=24)
:::1
___
***
```

**Write it fresh.** On the home page the band's words are yours, new each time, from `get_home_context`: `{{headline greeting="…" line="…" kicker="…" image=<product id> cta="…" action=<agent link>}}` draws this shape with them. The example's words are the shop's fallback, not a template.

**Why each marker**
- `{#headline-1}` asks this theme for the forest band; one per page, first. `MEANINGS.md`
- `___` above and below opens and closes the row: the words beside the photo in wide space, above it in narrow (`::: 1 >`). `structure.md`
- The first line is a small kicker: a few words of yours, or, left out, the shop's rating (`**⭐**` with the score and a caption saying from how many).
- `___…___` is the greeting in the Display tier: warm and of the moment, never a name, at most eight words. The plain line under it is one sentence about food that is true and specific: their usual, what is new or on offer.
- `+++` gives the buttons a little air. The main action is a product one the greeting leads to (add the usual burger, open a new product, open the menu or an offer); the quieter one is an alternative. Orders never go in the band: their status and reorder live in `home-orders`. On the band the main button turns mustard and the quieter one white; that is the theme's, never yours.
- The photo is the product the band is about (`image=<product id>`), else the shop's hero burger, with `md2ui.corner_radius=24`, `4:3`, and a `min_width` so it never gets squeezed. `images.md`
- `***` closes the band so the next section starts outside it.
