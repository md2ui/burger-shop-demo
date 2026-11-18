---
name: empty-state
description: A place with nothing in it yet: an icon, a title, one sentence on what would fill it, a reassurance line, and the action that fills it; use for an empty cart, no orders yet, no favourites, or a search with no results.
---
# Empty state

**Use for:** a page that would show something, but nothing is there yet. **Not for:** an error (say what failed and offer a retry), or a cart with items (`cart`).

```markdown
## {#empty-1}

*🛒*

___Your cart is empty___
Add a burger, a side or a shake and it will wait for you here. Every burger is smashed to order and delivered in about 20 minutes.

+++

✓ - __Free delivery over $25__ : _No fees, no minimum on the next order_

+++

[Browse burgers](agent:catalog) *[See offers](agent:offers)*
```

| Write | Means |
|---|---|
| `*🛒*` | the cart is empty |
| `*🧾*` | there are no orders yet |
| `*🤍*` | there are no favourites yet |
| `*🔍*` | a search or filter found nothing |

**Why each marker**
- `{#empty-1}` asks for the white empty-state panel, left aligned; one per page. `MEANINGS.md`
- The large badge is what is missing, one of the four in the table.
- The title in the Display tier, which this panel draws green; one or two sentences under it say what fills the place.
- One reassurance row: the standard badge, a short benefit in the Lead tier over its detail. Leave it out when there is nothing true to say.
- The action that fills the place is the main one; a quieter alternative beside it. For a search with no results, the main action clears the filter.
