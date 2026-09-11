# Lines over time, labelled at their ends instead of with a legend. The reader
# finds the name where the line stops, which is where the eye arrives anyway.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)
library(forcats)

cities <- c("Houston", "Dallas", "Austin", "San Antonio")

prices <- ggplot2::txhousing |>
  filter(city %in% cities) |>
  group_by(city, year) |>
  summarise(median = median(median, na.rm = TRUE), .groups = "drop") |>
  # Order the factor by the final value, so the series stack in the same order
  # top to bottom that their end labels do.
  mutate(city = fct_reorder(city, median, .fun = last, .desc = TRUE))

ends <- prices |> filter(year == max(year))
# Colours are keyed to the city name, not to the sort order, so the same city
# keeps the same colour in every chart of the set.
palette <- setNames(viz_palette[seq_along(cities)], cities)

# The title's figure is computed: which market rose most, and by how much.
growth <- prices |>
  group_by(city) |>
  summarise(rise = last(median) / first(median) - 1, .groups = "drop") |>
  slice_max(rise, n = 1)

p <- ggplot(prices, aes(year, median, colour = city)) +
  geom_line(linewidth = 1.1) +
  geom_text(
    data = ends, aes(label = city), hjust = 0, nudge_x = 0.3,
    family = viz_font(), size = 11 / .pt, fontface = "bold"
  ) +
  scale_colour_manual(values = palette) +
  scale_x_continuous(breaks = seq(2000, 2015, 5)) +
  # A line's position is the value, so unlike a bar it needs no zero baseline.
  scale_y_continuous(labels = label_short()) +
  # The labels sit outside the panel: switch clipping off and leave room.
  coord_cartesian(clip = "off") +
  labs(
    # <br> breaks a markdown title; a title wider than the plot is clipped.
    title = paste0(viz_span(growth$city, palette[[as.character(growth$city)]]),
                   " prices rose ", label_pct()(growth$rise),
                   " since 2000,<br>the most of the four big markets"),
    subtitle = "Median sale price by year",
    x = NULL, y = "Median price (USD)",
    caption = "Source: ggplot2::txhousing (Texas A&M Real Estate Center)"
  ) +
  theme_viz() +
  theme(plot.margin = margin(5.5, 70, 5.5, 5.5))

path <- file.path(out_dir, "line-direct-labels.png")
ggsave(path, p, width = 8, height = 5, dpi = 300, bg = "white")
message("wrote ", path)
