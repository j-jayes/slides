# Sorted horizontal bars: one amount per category, largest at the top, a lumped
# "Other" in grey at the bottom, values written on the bars.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)   # must equal the ggsave dpi below

library(ggplot2)
library(dplyr)
library(forcats)

# One row per city: total sales volume in 2014. fct_lump_n() keeps the nine
# largest and folds the rest into "Other"; fct_reorder() sorts by value, and
# fct_relevel("Other", after = 0) then pins Other to the bottom whatever its
# size, because "everything else" is not a competitor to the named bars.
sales <- ggplot2::txhousing |>
  filter(year == 2014) |>
  group_by(city) |>
  summarise(volume = sum(volume, na.rm = TRUE), .groups = "drop") |>
  mutate(city = fct_lump_n(city, n = 9, w = volume, other_level = "Other")) |>
  group_by(city) |>
  summarise(volume = sum(volume), .groups = "drop") |>
  mutate(
    city = fct_reorder(city, volume),
    city = fct_relevel(city, "Other", after = 0),
    fill = if_else(city == "Other", viz_colours[["muted"]], viz_colours[["single"]])
  )

# The title's number comes from the data, so the claim cannot drift from it.
top_two <- sales |> filter(city %in% c("Houston", "Dallas")) |> summarise(v = sum(volume)) |> pull(v)
share <- label_pct()(top_two / sum(sales$volume))

p <- ggplot(sales, aes(volume, city)) +
  geom_col(aes(fill = fill), width = 0.75) +
  geom_text(
    aes(label = label_short()(volume)),
    hjust = -0.15, family = viz_font(), size = 11 / .pt, colour = viz_colours[["text"]]
  ) +
  scale_fill_identity() +
  # Zero at the axis, room on the right for the value labels.
  scale_x_continuous(labels = label_short(), expand = expansion(mult = c(0, 0.12))) +
  labs(
    title = paste(viz_span("Houston and Dallas", viz_colours[["single"]]),
                  "sold", share, "of Texas homes by value in 2014"),
    subtitle = "Total sales volume by metro area; Other is the remaining 37 markets",
    x = "Sales volume (USD)", y = NULL,
    caption = "Source: ggplot2::txhousing (Texas A&M Real Estate Center)"
  ) +
  theme_viz(grid = "v")   # horizontal bars: grid lines perpendicular to the bars

path <- file.path(out_dir, "bars-sorted.png")
ggsave(path, p, width = 8, height = 5, dpi = 300, bg = "white")
message("wrote ", path)
