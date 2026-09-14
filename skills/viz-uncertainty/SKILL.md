---
name: viz-uncertainty
description: >-
  Show how sure an estimate is in ggplot2 — a coefficient plot with
  intervals, a confidence band around a mean over time, and the difference
  between a standard deviation, a standard error and a confidence interval,
  each drawn as what it is. Use when asked to "plot the model", "coefficient
  plot", "error bars", "confidence interval", "show the uncertainty", "how
  reliable is this", or when a chart has a fitted model behind it.
---

# Uncertainty: how sure the estimate is

Wilke's rule has one sentence: whenever you draw error bars, say what they
are. A standard deviation describes the data; a standard error and a
confidence interval describe how well you know a number derived from the
data. They differ by a factor of the square root of the sample size, and a
chart that does not say which it drew is a chart the reader cannot use.

Setup as in `viz-index`. All three templates render with the installed
packages; `confint()` is base R, so a single model needs no broom.

## Which chart

| Situation | Reach for | Template |
|---|---|---|
| A regression: which terms matter and by how much | Coefficient plot, terms sorted by estimate, 95% intervals, dashed zero | [coefficient-plot.R](reference/coefficient-plot.R) |
| A mean over time and how precisely it is known | Line with a ribbon of ± 1.96 standard errors | [confidence-band.R](reference/confidence-band.R) |
| Explaining SD against SE against CI, or choosing one | The same means with all three bars, faceted | [sd-se-ci.R](reference/sd-se-ci.R) |
| The spread of the data, not the precision of an estimate | Not this family: `viz-distributions` | — |

## The template

The coefficient plot from `coefficient-plot.R`:

```r
fit <- lm(mpg ~ wt + hp + disp + qsec + drat, data = cars)   # predictors standardised
coefs <- tibble::tibble(term = names(coef(fit)), estimate = coef(fit),
                        low = confint(fit)[, 1], high = confint(fit)[, 2]) |>
  filter(term != "(Intercept)") |>
  mutate(term = fct_reorder(term, estimate),
         colour = if_else(low > 0 | high < 0, viz_colours[["single"]], viz_colours[["grey_text"]]))

ggplot(coefs, aes(estimate, term, colour = colour)) +
  geom_vline(xintercept = 0, linetype = "dashed", colour = viz_colours[["reference"]]) +
  geom_pointrange(aes(xmin = low, xmax = high), linewidth = 0.8, size = 0.6) +
  scale_colour_identity() +
  labs(x = "Change in fuel economy (mpg per standard deviation)", y = NULL,
       caption = "Note: points are OLS estimates, lines their 95% confidence intervals.") +
  theme_viz(grid = "v")
```

## Rules that matter

**Say what the interval is, every time.** In the caption: `lines are 95%
confidence intervals`, `band is ± 1.96 standard errors`, `bars are ± 1
standard deviation`. `sd-se-ci.R` exists to show how different the three
look on identical means.

**SD is about the data; SE and CI are about the estimate.** A standard
deviation does not shrink as the sample grows; a standard error does, as
one over the square root of n. Drawing SD bars on a mean and calling them
error bars is Wilke's confusion to avoid. If the question is "how spread
out", draw the distribution instead.

**Coefficient plots: terms on y, sorted, zero dashed.** `fct_reorder(term,
estimate)` so the plot is a ranking. The dashed line at zero, drawn first.
Colour the intervals that exclude zero and grey the rest, so the eye finds
the terms that matter without a p-value column. Standardise the predictors
when they are in different units, and say so in the subtitle, or the
coefficients cannot share an axis.

**Bands for dense series, bars for sparse ones.** A ribbon around a line
reads as one object; error bars at every month read as a hedge. Draw the
ribbon first (`geom_ribbon(alpha = 0.18)`) and the line over it, in the
same colour.

**Never compare error bars by whether they overlap.** Wilke: the rules of
thumb are unreliable. If the question is whether two means differ, compute
the interval of the difference and draw that.

**No caps on error bars in a dense chart.** `geom_pointrange()` and
`geom_linerange()` draw none; `geom_errorbar(width = 0.3)` draws small
ones when the ends need to be found. Caps add ink and say nothing.

**Compute the claim.** The template titles name the terms whose intervals
exclude zero, or the rise in a mean, from the fitted objects. A title that
says "rose by half" when the data say 75% is wrong, and was, in a first
draft.

**Show the uncertainty of a fit as its band.** `geom_smooth(se = TRUE)`
draws the 95% band of the fitted line — see `viz-associations`. The band is
curved even for a straight fit, because the line can tilt as well as
shift; that is not a bug.

## On a Nexer slide

`theme_nexer()`; intervals that exclude zero in `nexer_colours[["purple"]]`,
the rest in `grey`, the one term the slide is about in `orange`. The
interval definition goes in the `::: {.source}` rail as the Note. A
coefficient plot with five terms fits `8 × 4.6` in a column; with more,
give it the full width.

## What does not work

- **Error bars with no definition.** The reader cannot tell a SD from a CI
  by looking.
- **Symmetric bars on skewed data**, or on a proportion near 0 or 1.
- **A coefficient plot with unstandardised predictors** in different units
  on one axis: the largest unit wins.
- **The intercept in the plot.** It is on a different scale from every
  slope; drop it.
- **Stars and p-values as the only signal.** Colour the intervals that
  exclude zero; the interval carries more information than the star.
- **Caps on every error bar in a crowded panel.**

## Before you ship

`viz-review`, with these lines first: every interval says what it is; SD
is not standing in for SE; terms sorted with zero dashed; the ribbon is
drawn under the line; the title's figure comes from the fit.

## Related skills

`viz-index` for the conventions, `viz-distributions` for spread rather than
precision, `viz-associations` for the fitted line and its band,
`viz-amounts` for a dot plot without intervals.
