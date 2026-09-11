---
name: viz-trends
description: >-
  Show change over time in ggplot2 — lines labelled at their ends instead of a
  legend, series rebased to an index, a log axis for growth with real-value
  labels, a slope graph for a few paired values. Use when asked for a "time
  series", "trend", "over time", "growth", "line chart", "before and after",
  or when the x-axis is a date or year.
---

# Trends: change over time

A time series has one left neighbour and one right neighbour per point, so a
line is the honest mark: it draws the order the data already has. Everything
else here is about making several lines readable without a legend, and
making growth comparable when levels are not.

Setup as in `viz-index`. All four templates render with the installed
packages.

## Which chart

| Situation | Reach for | Template |
|---|---|---|
| A few series, compared in levels | Lines, each named at its right-hand end | [line-direct-labels.R](reference/line-direct-labels.R) |
| Series with different levels, compared in growth | Lines rebased to 100 at a common start, dashed line at 100 | [index-rebased.R](reference/index-rebased.R) |
| One series growing by a roughly constant rate | A log axis labelled in real values, with the fitted rate | [log-axis-growth.R](reference/log-axis-growth.R) |
| Two points in time for a handful of named items | Slope graph, one item in colour, the rest grey | [slope-graph.R](reference/slope-graph.R) |

Wilke's rule for dots: the denser the series, the less you need them. Monthly
data over decades is a line; five annual points are dots joined by a line;
unevenly spaced observations are dots and a line. A filled area is only honest
when the y-axis starts at zero, because the area is then the value — see
`viz-proportions` for stacked shares.

## The template

The direct-labelling idiom, from `line-direct-labels.R`. The label sits just
past the last point; clipping is switched off so it can leave the panel, and
the right margin makes room for it.

```r
prices <- prices |>
  mutate(city = fct_reorder(city, median, .fun = last, .desc = TRUE))
ends <- prices |> filter(year == max(year))
palette <- setNames(viz_palette[seq_along(cities)], cities)   # keyed to names

ggplot(prices, aes(year, median, colour = city)) +
  geom_line(linewidth = 1.1) +
  geom_text(data = ends, aes(label = city), hjust = 0, nudge_x = 0.3,
            family = viz_font(), size = 11 / .pt, fontface = "bold") +
  scale_colour_manual(values = palette) +
  scale_y_continuous(labels = label_short()) +
  coord_cartesian(clip = "off") +
  labs(x = NULL, y = "Median price (USD)", caption = "Source: ggplot2::txhousing") +
  theme_viz() +
  theme(plot.margin = margin(5.5, 70, 5.5, 5.5))
```

## Rules that matter

**Label the line, not a legend.** The reader's eye arrives at the right-hand
end of each line anyway; put the name there. With four series or fewer the
title or subtitle can also carry the names in colour via `viz_span()`, which
is how the chart says which line it is about.

**Key colours to names, not to the sort order.** `setNames(viz_palette[1:4],
cities)` gives Houston the same colour in every chart of the set. A palette
assigned by factor level changes colour when the ranking changes.

**A line needs no zero.** Bars encode by length, so they start at zero; a line
encodes by position, so the axis can start where the data does. Forcing zero
flattens the differences the chart exists to show. The exception is a filled
area, which is a bar in disguise.

**Push apart labels that collide.** Two series ending within a few units of
each other overprint their labels. `index-rebased.R` carries a five-line
`spread()` that nudges each label up until it clears the one below; ggrepel
does the same with more machinery if it is installed.

**State the base of an index.** `Index (2000 = 100)` on the axis and the
subtitle, and a dashed reference line at 100 drawn *before* the series so
they pass over it.

**A log axis is labelled in real values.** `scale_y_log10(labels =
label_short(), breaks = c(5e11, 1e12, 2e12, 5e12, 1e13))` reads `500bn, 1tn,
2tn, 5tn, 10tn`. The axis title names the variable and says "log scale"; it
never says "log of". A straight line on that axis is a constant growth rate,
and `log-axis-growth.R` fits one with `lm(log(y) ~ years)` and puts the
resulting rate in the title and the Note.

**Say what the smooth is.** `geom_smooth()` defaults to loess and says so only
in the console. Write the method into the caption: `Note: dashed line is a
linear fit on the log scale`. Smoothing is least reliable at the ends of the
series; do not extrapolate a claim from the last few points of a loess.

**Highlight one, grey the rest.** The slope graph colours the class the title
is about with `viz_colours[["highlight"]]` and every other line
`viz_colours[["muted"]]`. The story is the one coloured line; the grey ones
are there so it has a context.

**Compute what the title claims.** Each template derives its headline figure
— the fastest-growing market, the fitted growth rate, the class with the
largest gain — from the data and pastes it in. A title typed by hand drifts
the first time the data is refreshed.

**Break a long title with `<br>`.** The title is markdown; a title wider than
the figure is clipped at the right edge with no warning. Two lines beat a
smaller font.

## On a Nexer slide

`theme_nexer()`, `nexer_use_fonts()`, `nexer_span()`. One series in
`nexer_colours[["purple"]]`, comparison series in `grey`, and `orange` only
for the line the slide's `###` is about. The end labels survive the PowerPoint
export because they are part of the image. Units go in `::: {.units}`.
`fig-width: 12, fig-height: 3.7` holds four labelled lines full width; in a
column use `8 × 4.6` and shorten the labels.

## What does not work

- **A legend for four lines.** The reader looks left, decodes, looks back,
  and has lost the line.
- **Dual y-axes.** Two scales on one panel let the author choose the crossing
  point. Rebase to an index, or draw two panels with `viz-compound`.
- **A connected scatterplot** (two variables against each other, time along
  the path). Readers confuse direction and order; two line charts are clearer.
- **Area from a non-zero base.** The shaded area then lies about the value.
- **`scale_y_log10()` on bars.** Bars on a log scale represent ratios and must
  start at 1. Use a line or dots.
- **Labels at the last point without `clip = "off"`.** They vanish at the
  panel edge.

## Before you ship

`viz-review`, with these lines first: every line named at its end, the base
of an index stated, the log axis in real values, the smoothing method in the
caption, and a title claim that the lines actually support.

## Related skills

`viz-index` for the conventions, `viz-labels` for annotating a point on a
line, `viz-uncertainty` for a confidence band around a trend,
`viz-proportions` for stacked shares over time, `viz-compound` for one panel
per series.
