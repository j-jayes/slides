---
name: viz-associations
description: >-
  Show how two quantitative variables relate in ggplot2 — a scatter with
  alpha and a stated fit, 2-D bins when the points pile up, an x = y line
  for paired measurements. Use when asked for a "scatter plot",
  "correlation", "relationship between", "x against y", "regression line",
  "does A predict B", or when both axes are numbers.
---

# Associations: two variables at once

A scatterplot is the honest chart for two numeric variables: every
observation is a point, nothing is summarised away. The work is in making
the cloud readable — transparency, then bins when there are too many — and
in being explicit about any line drawn through it.

Setup as in `viz-index`. All three templates render with the installed
packages; `geom_hex()` would need hexbin, so the binning template uses
`geom_bin2d()`.

## Which chart

| Situation | Reach for | Template |
|---|---|---|
| Up to a few thousand points, and a trend to state | Scatter with alpha, a linear fit and its band, the method in the Note | [scatter-alpha-smooth.R](reference/scatter-alpha-smooth.R) |
| Tens of thousands of points | 2-D bins coloured by count, log axes where the data span decades | [overplotting-bin2d.R](reference/overplotting-bin2d.R) |
| Two measurements of the same things | Scatter with a dashed x = y line and equal axis scales | [paired-xy-line.R](reference/paired-xy-line.R) |
| Three or more variables | One scatter per pair, or facets — not bubble sizes | `viz-compound` |

## The template

The scatter idiom from `scatter-alpha-smooth.R`, with the slope computed
into the title:

```r
fit <- lm(hwy ~ displ, data = cars)
slope <- label_short(accuracy = 0.1)(-coef(fit)[["displ"]])

ggplot(cars, aes(displ, hwy)) +
  geom_point(colour = viz_colours[["single"]], alpha = 0.45, size = 2.2) +
  geom_smooth(method = "lm", formula = y ~ x, se = TRUE,
              colour = viz_colours[["highlight"]], fill = viz_colours[["muted"]]) +
  labs(title = paste("Each extra litre of engine costs about", slope, "mpg on the highway"),
       x = "Engine displacement (litres)", y = "Highway fuel economy (miles per gallon)",
       caption = "Note: line is a linear fit with its 95% confidence band. Source: ggplot2::mpg") +
  theme_viz(grid = "both")
```

## Rules that matter

**Alpha first.** `alpha = 0.45` makes overlapping points darker, so the
density of the cloud shows through. Past a few thousand points alpha
saturates and the cloud goes solid; that is when to bin.

**Bin with rectangles, colour by count.** `geom_bin2d(bins = 60)` with
`scale_fill_viridis_c(labels = label_short())` and a colourbar at the
bottom. Hexagons are marginally better (points sit closer to a hexagon's
centre) and need the hexbin package; say so rather than fail.

**Say what the line is.** `geom_smooth()` defaults to loess, silently.
Write `method = "lm", formula = y ~ x` so the code says it, and put it in
the caption so the chart says it: `Note: line is a linear fit with its 95%
confidence band`. A loess is fine when the relationship is curved; state
the span.

**Put the slope in the title.** The fit's coefficient is the claim a
scatter with a line is making. Compute it and paste it: `Each extra litre of
engine costs about 3.5 mpg`.

**Paired data gets the diagonal, not a fit.** When x and y are the same
quantity measured twice, the question is which side of x = y the points
fall. `geom_abline(slope = 1, intercept = 0, linetype = "dashed")` drawn
first, `coord_equal()` so the diagonal is at 45°, and a small rotated label
saying what the line means.

**Both axes get a grid.** `theme_viz(grid = "both")`: a scatter has no
single variable of interest, so Wilke's full grid applies, and the axis
lines can go.

**Log axes when a variable spans decades.** Diamond prices run from 300 to
18,000; on a linear axis nine tenths of the points sit in the bottom tenth.
`scale_y_log10(labels = label_short(), breaks = c(500, 1000, 2000, 5000,
10000, 20000))`, and the axis title says `log scale`.

**Facets before colour, colour before size.** Groups within a scatter are
clearer as small multiples than as five colours, and a third variable is
clearer as colour than as point size — differences in area are hard to see.

**Correlation coefficients last.** A correlogram hides the shapes that a
scatter shows. Show the raw data first; summarise only when there are too
many pairs to show.

## On a Nexer slide

`theme_nexer()` blanks the axis titles, and a scatter cannot do without
them: add `theme(axis.title = element_text(colour = "#4a4a4a"))` back, or
name both axes in the subtitle. Points in `nexer_colours[["purple"]]` at
`alpha = 0.5`, the fit line in `orange`, its band in `grey_pale`. A scatter
wants a square-ish panel: `8 × 4.6` in a column rather than full width.

## What does not work

- **A bubble chart.** Size is the weakest channel; nobody can read a ratio
  of areas. Use a third axis of facets, or colour.
- **`geom_smooth()` with no method stated** anywhere the reader can see.
- **Extrapolating the fit** past the data. `geom_smooth()` stops at the
  last point for a reason.
- **A dual-axis chart to show a relationship.** Plot one against the other.
- **`coord_fixed()` on axes with different units.** Equal scales only mean
  something when x and y are the same quantity.
- **A correlogram as the first chart.** Wilke: it is always better to
  visualise the raw data than a derived quantity.

## Before you ship

`viz-review`, with these lines first: alpha or bins, never a solid blob;
the smoothing method in the caption; the slope in the title computed; the
x = y line only on paired data, with equal scales; units on both axis
titles.

## Related skills

`viz-index` for the conventions, `viz-uncertainty` for the confidence band
around a fit, `viz-compound` for one panel per group, `viz-labels` for
naming points.
