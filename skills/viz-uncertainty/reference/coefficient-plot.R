# Coefficient plot: one row per model term, a point for the estimate and a
# line for its 95% confidence interval, a dashed line at zero. Terms sorted
# by estimate so the plot reads as a ranking; the interval says what it is.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)
library(forcats)

# Predictors are standardised so the coefficients share a scale: each is the
# change in mpg for one standard deviation of the predictor.
cars <- datasets::mtcars |>
  mutate(across(c(wt, hp, disp, qsec, drat), ~ as.numeric(scale(.x))))
fit <- lm(mpg ~ wt + hp + disp + qsec + drat, data = cars)

# confint() is base R, so no broom needed for a single model.
coefs <- tibble::tibble(
  term = names(coef(fit)),
  estimate = coef(fit),
  low = confint(fit)[, 1],
  high = confint(fit)[, 2]
) |>
  filter(term != "(Intercept)") |>
  mutate(
    term = recode(term, wt = "Weight", hp = "Horsepower", disp = "Displacement",
                  qsec = "Quarter-mile time", drat = "Rear axle ratio"),
    term = fct_reorder(term, estimate),
    # An interval that excludes zero is the story; one that crosses it is grey.
    colour = if_else(low > 0 | high < 0, viz_colours[["single"]], viz_colours[["grey_text"]])
  )

decisive <- coefs |> filter(colour == viz_colours[["single"]]) |> pull(term)
verb <- if (length(decisive) == 1) "moves" else "move"

p <- ggplot(coefs, aes(estimate, term, colour = colour)) +
  geom_vline(xintercept = 0, linetype = "dashed", colour = viz_colours[["reference"]]) +
  geom_pointrange(aes(xmin = low, xmax = high), linewidth = 0.8, size = 0.6) +
  scale_colour_identity() +
  scale_x_continuous(labels = label_short(accuracy = 0.1)) +
  labs(
    title = paste0("Only ", tolower(paste(decisive, collapse = " and ")),
                   " ", verb, " fuel economy once the others are held fixed"),
    subtitle = "Effect on miles per gallon of one standard deviation of each predictor, 32 cars",
    x = "Change in fuel economy (mpg per standard deviation)", y = NULL,
    caption = "Note: points are OLS estimates, lines their 95% confidence intervals. Source: datasets::mtcars"
  ) +
  theme_viz(grid = "v")

path <- file.path(out_dir, "coefficient-plot.png")
ggsave(path, p, width = 8, height = 5, dpi = 300, bg = "white")
message("wrote ", path)
