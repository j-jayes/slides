# Heatmap: amounts for two categories at once, when bars would be too many.
# The exact values are harder to read than on bars; the pattern is easier.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)
library(forcats)

# Median sale price per city and year for the twelve largest markets. Rows are
# ordered by the last year's value, so the eye reads the ranking down the
# right-hand edge and the history to its left.
prices <- ggplot2::txhousing |>
  group_by(city, year) |>
  summarise(median = median(median, na.rm = TRUE), volume = sum(volume, na.rm = TRUE), .groups = "drop") |>
  group_by(city) |>
  filter(sum(volume) > 0) |>
  mutate(total = sum(volume)) |>
  ungroup() |>
  filter(city %in% (distinct(pick(city, total)) |> slice_max(total, n = 12) |> pull(city))) |>
  mutate(city = fct_reorder(city, median, .fun = last))

dearest <- levels(prices$city)[nlevels(prices$city)]   # top row = highest last value

p <- ggplot(prices, aes(year, city, fill = median)) +
  geom_tile(width = 0.95, height = 0.95) +
  scale_fill_viridis_c(labels = label_short(), option = "D") +
  scale_x_continuous(breaks = seq(2000, 2015, 5), expand = c(0, 0)) +
  labs(
    title = paste0("Every large Texas market got dearer, and ", dearest, " is now the dearest"),
    subtitle = "Median sale price by year, twelve largest markets by volume",
    x = NULL, y = NULL, fill = "Median price (USD)",
    caption = "Source: ggplot2::txhousing (Texas A&M Real Estate Center)"
  ) +
  theme_viz(grid = "none") +
  # A continuous scale gets a colourbar: wide, flat, at the bottom.
  theme(
    legend.position = "bottom",
    legend.title.position = "top",
    legend.key.width = unit(2.4, "cm"),
    legend.key.height = unit(0.35, "cm")
  )

path <- file.path(out_dir, "heatmap.png")
ggsave(path, p, width = 8, height = 6, dpi = 300, bg = "white")
message("wrote ", path)
