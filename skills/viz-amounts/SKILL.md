---
name: viz-amounts
description: >-
  Show one number per category in ggplot2 — sorted horizontal bars, a dot plot
  when the axis must not start at zero, facets instead of grouped bars, a
  heatmap when there are too many for bars. Use when asked to "compare
  categories", "rank these", "bar chart", "top 10 by", "which is biggest", or
  when the data is one amount per label.
---

# Amounts: one number per category

The most common chart, and the one most often drawn badly. Wilke's rules are
few: bars start at zero, the order carries information, and text should be
horizontal. Jonathan's habit on top of those is to put the category on the
y-axis and sort it so the eye reads top to bottom like a ranking, which is
what a reader does with a list anyway.

Setup as in `viz-index`: `source("R/viz.R")`, `viz_use_fonts()`, ggplot2,
dplyr, forcats. Every template here renders with the installed packages.

## Which chart

| Situation | Reach for | Template |
|---|---|---|
| One amount per category, up to ~15 categories | Horizontal bars, sorted largest at top | [bars-sorted.R](reference/bars-sorted.R) |
| The same, for several groups (years, regions) | One facet per group, each sorted on its own | [bars-facets-topn.R](reference/bars-facets-topn.R) |
| Values all sit far from zero and the differences are the point | Dot plot on a zoomed axis | [dot-plot.R](reference/dot-plot.R) |
| Two categorical dimensions, dozens of cells | Heatmap, rows ordered by a meaningful column | [heatmap.R](reference/heatmap.R) |

Not on the list: grouped bars. Wilke: "grouped bar plots show a lot of
information at once and they can be confusing." Facet instead. Stacked bars
only when the total of the stack is itself a meaningful number — then see
`viz-proportions`.

## The template

The whole of `bars-sorted.R` is the shape every bar chart here takes. The
data step does the work; the plot step is short.

```r
sales <- ggplot2::txhousing |>
  filter(year == 2014) |>
  group_by(city) |>
  summarise(volume = sum(volume, na.rm = TRUE), .groups = "drop") |>
  mutate(city = fct_lump_n(city, n = 9, w = volume, other_level = "Other")) |>
  group_by(city) |>
  summarise(volume = sum(volume), .groups = "drop") |>
  mutate(
    city = fct_reorder(city, volume),            # largest at the top
    city = fct_relevel(city, "Other", after = 0), # Other always last
    fill = if_else(city == "Other", viz_colours[["muted"]], viz_colours[["single"]])
  )

ggplot(sales, aes(volume, city)) +
  geom_col(aes(fill = fill), width = 0.75) +
  geom_text(aes(label = label_short()(volume)), hjust = -0.15,
            family = viz_font(), size = 11 / .pt, colour = viz_colours[["text"]]) +
  scale_fill_identity() +
  scale_x_continuous(labels = label_short(), expand = expansion(mult = c(0, 0.12))) +
  labs(x = "Sales volume (USD)", y = NULL, caption = "Source: ggplot2::txhousing") +
  theme_viz(grid = "v")
```

## Rules that matter

**Category on `y`, never `coord_flip()`.** Map `aes(value, category)`. Every
scale and label then refers to the axis it is on, and the labels are
horizontal — Wilke: "I am not a big proponent of rotated labels."

**Sort with `fct_reorder()`, unless the order is natural.** Age bands,
months, Likert levels keep their own order even when sorting by value would
look tidier. Everything else is sorted, largest at the top. The level order of
a factor runs bottom to top on the y-axis, so `fct_reorder(city, volume)`
ascending puts the largest at the top without a `.desc`.

**"Other" is the bottom bar, in grey.** `fct_lump_n()` makes it,
`fct_relevel("Other", after = 0)` pins it, and a grey fill says it is not a
competitor to the named bars. Lump *after* choosing the sort key, not before.

**Bars start at zero.** That is what makes length mean amount. A bar axis with
`limits = c(3, 3.3)` is Wilke's definition of *wrong*. When the interesting
range is far from zero, draw dots: their position is the value, so the axis
can be zoomed. `dot-plot.R` does this for fuel economy that sits between 17
and 28 mpg.

**The base touches the axis.** `expand = expansion(mult = c(0, 0.05))` removes
ggplot's default gap at zero and leaves room at the far end. Widen the far end
(`0.12`) when values are written beside the bars.

**Value labels beside the bar, formatted.** `label_short()` on the label and
on the axis, so the bar says `22.1bn` and the axis says `20bn`. With labels on
the bars the axis text can go (`axis.text.x = element_blank()`), but keep the
axis title: it holds the units.

**Grid perpendicular to the bars.** `theme_viz(grid = "v")` for horizontal
bars. Horizontal lines behind horizontal bars add nothing.

**Sorting inside facets needs a unique level.** A factor has one order, so to
sort each panel separately, build a level that is unique per panel and strip
the suffix in the axis labels — `bars-facets-topn.R` does it without tidytext:

```r
mutate(key = fct_reorder(paste(city, year, sep = "|"), sales)) |>
ggplot(aes(sales, key)) +
  facet_wrap(vars(year), ncol = 1, scales = "free_y") +
  scale_y_discrete(labels = function(x) sub("\\|.*$", "", x))
```

**Put the number in the title, computed.** `bars-sorted.R` computes the two
largest markets' share and pastes it into the title, so the claim cannot drift
from the data when the input changes. Do this whenever the title carries a
figure.

**A heatmap trades precision for pattern.** Order its rows by something the
reader cares about — `fct_reorder(city, median, .fun = last)` ranks by the
final year — and give the continuous fill a wide, flat colourbar at the
bottom, since a legend is the only way to decode a continuous scale:

```r
theme(legend.position = "bottom", legend.title.position = "top",
      legend.key.width = unit(2.4, "cm"), legend.key.height = unit(0.35, "cm"))
```

## On a Nexer slide

`theme_nexer()` in place of `theme_viz()`; it already drops the vertical grid,
so add `theme(panel.grid.major.x = element_line(colour = "#e6e6e6"),
panel.grid.major.y = element_blank())` for horizontal bars. Bars in
`nexer_colours[["purple"]]`, Other and comparison bars in `grey`, the one bar
the slide is about in `orange`. Units go in the `::: {.units}` rail, since the
theme blanks axis titles. `fig-width: 12, fig-height: 3.7` full width holds
about eight bars at `base_size = 20`; a column at `8 × 4.6` holds six.

## What does not work

- **Rotated x-axis labels** to fit long category names. Turn the chart.
- **`reorder()` inside `aes()`** for anything but a one-off; the sort belongs
  in the data step where `fct_relevel()` can act on it too.
- **`fct_lump()` before deciding what to sort on.** The Other bar then
  inherits whatever position its size gives it.
- **A grouped bar chart with more than two groups.** The eye cannot compare
  the second bar of cluster one with the second bar of cluster four.
- **A log axis on bars.** Bars on a log scale represent ratios and must start
  at 1, which nobody reads that way. Use dots.

## Before you ship

Run the `viz-review` checklist on the rendered PNG. For this family the lines
that catch most errors: bars from zero, largest at top, Other last and grey,
`1,000`-style numbers, units in the axis title, and a title whose claim is
true of the bars drawn.

## Related skills

`viz-index` for the conventions, `viz-proportions` when the bars are parts of
a whole, `viz-colour` for highlighting one bar, `viz-labels` for the title
rule on slides, `nexer-slides` for the deck.
