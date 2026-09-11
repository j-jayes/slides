---
name: viz-proportions
description: >-
  Show parts of a whole in ggplot2 — stacked bars scaled to 100% for shares
  across groups, stacked areas for a composition over time, and the one case
  where a pie is right. Use when asked for "share of", "percentage breakdown",
  "composition", "market share over time", "pie chart", or when the numbers
  add up to a whole.
---

# Proportions: parts of a whole

Wilke's table settles the old argument. A pie emphasises simple fractions
and works for one small whole; stacked bars work for many groups or a time
series; side-by-side bars let the reader compare the individual fractions.
No one of them fits every case, and the pie fits the fewest.

Setup as in `viz-index`. All three templates render with the installed
packages.

## Which chart

| Situation | Reach for | Template |
|---|---|---|
| Two or three parts, several groups, compare the shares | Bars with `position_fill()`, sorted by the part that matters | [stacked-bars-fill.R](reference/stacked-bars-fill.R) |
| The composition of a whole over time | Stacked area from a zero base, largest part on the baseline, Other on top | [stacked-share-over-time.R](reference/stacked-share-over-time.R) |
| One whole, two or three parts, and the point is a simple fraction | A pie, labelled inside, coloured for the part that matters | [pie-one-whole.R](reference/pie-one-whole.R) |
| Compare the same fraction across many groups | Sorted bars of that one share, from `viz-amounts` | — |

More than three parts to compare across groups is neither a pie nor a stack:
the interior segments have no shared baseline. Facet one sorted bar chart
per part instead.

## The template

The filled-bar idiom from `stacked-bars-fill.R`:

```r
shares <- ggplot2::mpg |>
  count(class, drive) |>
  group_by(class) |>
  mutate(share = n / sum(n)) |>
  ungroup() |>
  mutate(class = fct_reorder(class, share * (drive == "Four-wheel"), .fun = sum))

ggplot(shares, aes(share, class, fill = drive)) +
  geom_col(position = position_fill(reverse = TRUE), width = 0.75) +
  geom_text(aes(label = if_else(share >= 0.08, label_pct()(share), "")),
            position = position_fill(reverse = TRUE, vjust = 0.5),
            family = viz_font(), size = 10 / .pt, colour = "white") +
  scale_fill_manual(values = palette) +
  scale_x_continuous(labels = label_pct(), expand = c(0, 0)) +
  labs(x = "Share of models (%)", y = NULL) +
  theme_viz(grid = "none")
```

## Rules that matter

**Sort by the part the chart is about.** `fct_reorder(class, share *
(drive == "Four-wheel"), .fun = sum)` ranks the bars by one part's share, so
that part's segment forms a staircase against the axis and the ranking reads
top to bottom. The part sorted on goes first in the stack, against the
baseline, where its length can be compared.

**Write the percentage inside the segment**, and only where it fits:
`if_else(share >= 0.08, label_pct()(share), "")`. A number in a sliver
overprints its neighbour.

**`position_fill(reverse = TRUE)`** stacks the first factor level at the
axis. Without it the first level lands furthest from the axis, and the
legend order (or the coloured words) reads the opposite way to the bars.

**A stacked area starts at zero and has the largest part on the baseline.**
The baseline band is the only one whose height can be read directly; the
band on top of the stack is the next best, because its upper edge is the
100% line. Put the part the reader cares about in one of those two places
and Other, in grey, on top. `stacked-share-over-time.R` labels each band at
its right-hand end from the stacked midpoints — compute the cumulative sum in
factor-level order, since that is the stacking order.

**The pie, when it is allowed.** One whole. Three parts or fewer. A message
that is a simple fraction — half, a third, a quarter — which the eye checks
against a clock face. Colour the part the message is about and grey the
rest; label inside the slice, or outside if the slice is under about 15%.
`coord_polar(theta = "y", direction = -1)` reads clockwise from twelve. In
ggplot2 the pie is a single stacked bar bent round, so it needs
`labs(x = NULL, y = NULL)` and blank axis text or the bar's axes show.

**A share needs its base.** "43%" of what? The subtitle or the axis title
says: `Share of models (%)`, `Bundestag, 496 seats`.

**Two parts are the best case for a stack.** With exactly two, both segments
touch an edge and both can be read. A single filled bar per group is then a
cleaner chart than two bars per group.

## On a Nexer slide

`theme_nexer()`. The part the slide is about in `nexer_colours[["purple"]]`,
the other parts in `grey` and `grey_pale`, Other in `grey`. Percentages in
white inside the purple segment only. A stacked area at `fig-width: 12,
fig-height: 3.7` carries its band labels in the image, so no legend is
needed in PowerPoint either. Base and units in the `::: {.units}` rail.

## What does not work

- **A pie with five slices**, or two pies side by side to show change.
  Stacked bars, or a slope graph of the shares.
- **A donut.** The hole removes the angle at the centre, which is the only
  thing a pie lets the eye measure.
- **A stack of four parts compared across ten groups.** The middle parts
  float; nobody can compare them.
- **A stacked area where the interesting part is in the middle.** Move it
  to the baseline or the top.
- **Percentages that do not sum to 100** in a filled bar, because of
  rounding shown to no decimals. Say so in the Note, or show one decimal.

## Before you ship

`viz-review`, with these lines first: bars sorted by the part that matters,
that part against the baseline, Other grey and on top, every percentage
inside a segment that can hold it, the base of the share stated, and no pie
that fails the one-whole-three-parts test.

## Related skills

`viz-index` for the conventions, `viz-amounts` for the shares of one part
as sorted bars, `viz-trends` for shares as lines when the composition has
more than four parts, `viz-colour` for the highlight scheme.
