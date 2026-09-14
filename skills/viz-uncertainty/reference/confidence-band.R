# A mean over time with its confidence band: the line is the estimate, the
# ribbon is how precisely the estimate is known, and the caption says what
# the band is. A band, not error bars, because the series is dense.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)

# Mean of the monthly median price across all Texas markets, per year, with
# the standard error of that mean. SE, not SD: the band is about the mean,
# not about how much markets differ from each other.
prices <- ggplot2::txhousing |>
  filter(!is.na(median)) |>
  group_by(year) |>
  summarise(
    mean = mean(median),
    se = sd(median) / sqrt(n()),
    n = n(),
    .groups = "drop"
  ) |>
  mutate(low = mean - 1.96 * se, high = mean + 1.96 * se)

# The rise in the title is computed, not typed.
rise <- label_pct()(last(prices$mean) / first(prices$mean) - 1)

p <- ggplot(prices, aes(year, mean)) +
  # The ribbon first, so the line draws over it.
  geom_ribbon(aes(ymin = low, ymax = high), fill = viz_colours[["single"]], alpha = 0.18) +
  geom_line(colour = viz_colours[["single"]], linewidth = 1.1) +
  scale_x_continuous(breaks = seq(2000, 2015, 5)) +
  scale_y_continuous(labels = label_short()) +
  labs(
    title = paste("The typical Texas market's median home price rose", rise, "since 2000"),
    subtitle = "Mean of monthly median sale prices across 46 markets, by year",
    x = NULL, y = "Mean median price (USD)",
    caption = "Note: band is the 95% confidence interval of the mean (± 1.96 standard errors). Source: ggplot2::txhousing"
  ) +
  theme_viz()

path <- file.path(out_dir, "confidence-band.png")
ggsave(path, p, width = 8, height = 5, dpi = 300, bg = "white")
message("wrote ", path)
