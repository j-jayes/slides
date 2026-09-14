---
name: viz-compound
description: >-
  Put several ggplot2 panels in one figure — facets with shared scales and a
  meaningful order for the same chart repeated, or patchwork for different
  charts side by side with tags and one title. Use when asked for "small
  multiples", "one panel per", "side by side", "panel a and b", "combine
  these plots", or when one chart is carrying two claims.
---

# Compound figures: several panels, one figure

Two different jobs wear the same name. **Small multiples** repeat one chart
for each group, so the reader compares; every panel must then share its
scales or the comparison is a lie. A **compound figure** puts different
charts together, so the reader gets a sequence; each panel keeps its own
scales but they must share a visual language.

Setup as in `viz-index`. The facets template needs nothing; patchwork needs
`install.packages("patchwork")` and the template says so if it is missing.

## Which chart

| Situation | Reach for | Template |
|---|---|---|
| One chart repeated per group | `facet_wrap()`, shared scales, panels in a meaningful order | [facets-shared-scales.R](reference/facets-shared-scales.R) |
| Different charts that belong together | patchwork `\|` and `/`, tags a b c, one title | [patchwork-tagged.R](reference/patchwork-tagged.R) |
| Two series with different units | Two stacked panels, never a dual axis | `viz-trends` |

## The template

Facets, from `facets-shared-scales.R`. One scale for every panel, panels
ordered by size, and each panel's peak marked so the grid carries a
finding rather than being an inventory:

```r
sales <- sales |> mutate(city = fct_reorder(city, sales, .fun = sum, .desc = TRUE))
peaks <- sales |> group_by(city) |> slice_max(sales, n = 1) |> ungroup()

ggplot(sales, aes(year, sales)) +
  geom_area(fill = viz_colours[["single"]], alpha = 0.15) +
  geom_line(colour = viz_colours[["single"]], linewidth = 0.9) +
  geom_point(data = peaks, colour = viz_colours[["highlight"]], size = 2.4) +
  facet_wrap(vars(city), ncol = 3) +              # one scale for every panel
  scale_y_continuous(labels = label_short(), limits = c(0, NA)) +
  theme_viz() +
  theme(panel.spacing = unit(1.2, "lines"))
```

And the patchwork operators, from `patchwork-tagged.R`:

```r
(a | b | c) +                                   # | beside, / above
  plot_annotation(tag_levels = "a", title = "…", theme = theme_viz()) &
  panel_title &                                 # & applies to every panel
  theme(plot.tag = element_text(face = "bold", size = 12))
```

## Rules that matter

**Facets share scales. Say so when they do not.** The default `scales =
"fixed"` is the right default: a line at the same height means the same
number in every panel. `scales = "free_y"` makes each panel a different
chart that happens to be in a grid, and the reader will compare them
anyway. If you must free a scale, write it in the caption.

**A small market looks flat, and that is the point.** In the facets
template El Paso's line barely moves against Houston's, because it sells a
tenth as many homes. That is the honest comparison. If the shapes matter
more than the levels, index each panel to its own start — see `viz-trends`
— rather than freeing the axis.

**Order the panels.** `fct_reorder(city, sales, .fun = sum, .desc = TRUE)`
puts the largest first; time, size, or a ranking all beat alphabetical.
Wilke: always arrange the panels in a meaningful and logical order.

**Give the grid a finding.** A facet grid of six lines is an inventory. The
peak dot plus a title that counts them — "Four of the six largest Texas
markets peaked before the 2008 crash" — makes it an exhibit. Compute the
count; spelled out, since a title should not open with a numeral.

**`panel.spacing` and `strip.text` do the tidying.** `theme_viz()` already
left-aligns and bolds the strip; add `panel.spacing = unit(1.2, "lines")`
so the panels do not touch.

**Compound figures share a visual language, not a scale.** The same colour
means the same thing in every panel, the same font at the same size, the
same rounding. `&` in patchwork applies a theme to every panel at once; `+`
only touches the last one. That difference is the most common patchwork
mistake.

**Tag with lower-case letters.** `plot_annotation(tag_levels = "a")`.
Wilke: the tags should behave like page numbers — present, unobtrusive, not
bold 24-point. Demote the panel titles to plain weight so the compound
title is the only thing shouting.

**One title for the figure, short titles for the panels.** The compound
title carries the claim; each panel says what it shows in four words.

**Three panels wide is the practical limit** at 12 inches. Beyond that,
stack: `(a | b) / (c | d)`.

## On a Nexer slide

A facet grid is one image, so it survives the PowerPoint export like any
chart. A patchwork figure is also one image — which is the reason to use it
rather than two `.columns` blocks, since a stat row or a columns block
makes pandoc split the slide. `fig-width: 12, fig-height: 4.2` holds three
panels at `base_size = 16`; six facets need `fig-height: 5` and shorter
strip labels. Keep `theme_nexer()` on every panel via `&`.

## What does not work

- **`scales = "free_y"` by habit.** It removes the only reason to facet.
- **`+` instead of `&`** for a theme in patchwork: it lands on the last
  panel only, and the others silently keep the default theme.
- **A legend per panel.** Collect it once, or name the colours in the
  compound subtitle.
- **More than about six facets on a slide.** The labels shrink past
  reading.
- **`facet_wrap()` on a variable with one level.** That is a title.
- **Different rounding in different panels**: `1.2m` in one and `1,214,003`
  in the next.

## Before you ship

`viz-review`, with these lines first: panels share scales or the caption
says otherwise; the order is meaningful; the same colour means the same
thing in every panel; tags are unobtrusive; the compound title carries a
claim the panels support.

## Related skills

`viz-index` for the conventions, `viz-trends` for indexing instead of
freeing a scale, `viz-colour` for one colour language across panels,
`nexer-slides` for what a single image buys you in the pptx export.
