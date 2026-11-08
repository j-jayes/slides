---
name: web-design
description: >-
  Twenty concrete rules that stop web interfaces looking AI-generated. Use when
  building, restyling or reviewing any web UI: landing pages, pricing pages,
  dashboards, forms, components, HTML artifacts. Also use when asked to "unslop"
  a design, make it look less AI-generated or more polished, or when a design
  feels generic.
---

# Web design

AI-generated interfaces fail in predictable ways: decoration that says nothing, copy
that could describe anything, and everything shouting at the same volume. Work through
the five passes in order, because there is no point polishing what you are about to delete.

**Building something new:** treat the rules as defaults.
**Reviewing something:** render it, run the passes, and report each hit as
`rule → where → fix` before changing anything.

Every rule is conditional on the problem being present. Do not restyle what already
works. Never delete information to satisfy a rule. An existing brand or design system
outranks anything here.

## Pass 1: Cut

| # | Rule | Do this | Keep it when |
|---|------|---------|--------------|
| 1 | Delete filler badges | Remove "New" pills and announcement chips above the hero. | It marks a real, current choice ("Most popular"). |
| 2 | Drop redundant labels | Remove eyebrows that repeat the heading, such as "FAQ" above "Questions, answered". | The label adds context the heading lacks. |
| 3 | Unitalicize random words | Set headlines in one style. No italic word for flavour. | Real emphasis or a work's title. |
| 4 | Mono only where needed | Monospace is for code, commands and IDs. Remove it from headlines and eyebrows, along with fake terminal cursors. | The text is literally machine text. |
| 13 | Remove embellishments | Remove glows, gradient borders and ambient blobs. | It signals state, such as a focus ring. |

## Pass 2: Say something

| # | Rule | Do this |
|---|------|---------|
| 9 | Make headlines specific | Replace slogans ("X, meet Y") with what the product delivers. Test: could a competitor use this headline unchanged? If yes, rewrite it. |
| 6 | Show the actual product | Replace abstract art (globes, orbs) with real UI: a sample query and its actual result. |

Never invent a claim, metric, customer or screenshot to make these work. If the real
fact or product view is missing, ask for it or mark a visible placeholder.

## Pass 3: Set the hierarchy

| # | Rule | Do this |
|---|------|---------|
| 7 | Enlarge the main feature | Break up rows of equal cards: one large feature, the rest smaller and secondary. Only when one really does matter most. |
| 10 | Emphasize the CTA | One filled primary action per view. Everything beside it is outlined or ghost, even on pricing tables. |
| 11 | Add an accent colour | Pick one accent and spend it on the primary action, so it means "act here". Not on decoration. |
| 15 | Improve text contrast | No faded grey lines for style. Body text at least 4.5:1, large text at least 3:1. |
| 8 | Group with spacing | Remove boxes and dividers that whitespace can do alone. Gaps inside a group must be smaller than gaps between groups. Keep rules in dense data tables. |

## Pass 4: Make it consistent and exact

| # | Rule | Do this |
|---|------|---------|
| 5 | Use a design system | Take colour, type, spacing, radius and buttons from shared tokens. A one-off tinted button among neutral siblings is a bug. Use the project's system if it has one. |
| 12 | Keep icons consistent | One icon family, one stroke weight, one size scale. No emoji as UI icons. |
| 14 | Nest radii concentrically | `inner radius = outer radius − padding`, floored at 0. |
| 16 | Wrap headlines properly | No orphaned last word. Keep a highlighted phrase on one line. |
| 17 | Align by eye, not pixels | Centre asymmetric shapes by visual weight. A play triangle needs nudging toward its point inside a circle. |
| 18 | Use tabular nums | Fixed-width digits wherever numbers change or stack: prices, counters, timers, table columns. |

```css
.card  { --r: 16px; --pad: 8px; border-radius: var(--r); padding: var(--pad); }
.inner { border-radius: max(0px, calc(var(--r) - var(--pad))); }

h1, h2 { text-wrap: balance; }
p      { text-wrap: pretty; }

.price, td.num, .timer { font-variant-numeric: tabular-nums; }
```

## Pass 5: Make it feel alive

| # | Rule | Do this |
|---|------|---------|
| 19 | Add loading states | Skeletons that match the final layout, never blank rows under real headers. Design the empty and error states too. |
| 20 | Animate useful feedback | Animate state changes the user caused ("Add to cart" → "Added ✓"). Keep it to about 150–250 ms, and honour `prefers-reduced-motion`. No motion that reports nothing. |

## Before calling it done

Render it and look at it, at desktop and phone widths. Then check:

- Trigger every state you touched: hover, loading, empty, error, success.
- Measure contrast rather than judging it by eye.
- Squint: the one thing you want clicked should still stand out.

---

Rules from [20 Ways to Unslop AI Designs](https://www.instagram.com/p/DfcnAJFhAa1/) by
charles.unemployed. The CSS, contrast ratios, timings and "keep it when" exceptions were
added here.
