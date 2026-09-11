# Indexed lines: several series rebased to 100 at a common start, so growth
# can be compared when the levels cannot. The base is stated on the chart.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)
library(forcats)

cities <- c("Houston", "Dallas", "Austin", "San Antonio")

indexed <- ggplot2::txhousing |>
  filter(city %in% cities) |>
  group_by(city, year) |>
  summarise(median = median(median, na.rm = TRUE), .groups = "drop") |>
  group_by(city) |>
  mutate(index = 100 * median / median[year == min(year)]) |>
  ungroup() |>
  mutate(city = fct_reorder(city, index, .fun = last, .desc = TRUE))

# End labels that finish close together would overprint. Push each label up
# until it clears the one below by `gap` data units (ggrepel does this too,
# but this keeps the template free of extra packages).
spread <- function(y, gap) {
  o <- order(y)
  s <- y[o]
  for (i in seq_along(s)[-1]) s[i] <- max(s[i], s[i - 1] + gap)
  s[order(o)]
}
ends <- indexed |>
  filter(year == max(year)) |>
  mutate(label_y = spread(index, gap = 5))
# Colours are keyed to the city name, not to the sort order, so the same city
# keeps the same colour in every chart of the set.
palette <- setNames(viz_palette[seq_along(cities)], cities)

# The two fastest growers, named in the title from the data.
top <- levels(indexed$city)[1:2]

p <- ggplot(indexed, aes(year, index, colour = city)) +
  # The base line goes first, so the series draw over it.
  geom_hline(yintercept = 100, linetype = "dashed", colour = viz_colours[["reference"]]) +
  geom_line(linewidth = 1.1) +
  geom_text(
    data = ends, aes(y = label_y, label = paste0(city, "  ", round(index))),
    hjust = 0, nudge_x = 0.3,
    family = viz_font(), size = 11 / .pt, fontface = "bold"
  ) +
  scale_colour_manual(values = palette) +
  scale_x_continuous(breaks = seq(2000, 2015, 5)) +
  coord_cartesian(clip = "off") +
  labs(
    title = paste(viz_span(top[1], palette[[top[1]]]), "and",
                  viz_span(top[2], palette[[top[2]]]),
                  "prices grew fastest from a 2000 base"),
    subtitle = "Median sale price, index 2000 = 100",
    x = NULL, y = "Index (2000 = 100)",
    caption = "Source: ggplot2::txhousing (Texas A&M Real Estate Center)"
  ) +
  theme_viz() +
  theme(plot.margin = margin(5.5, 90, 5.5, 5.5))

path <- file.path(out_dir, "index-rebased.png")
ggsave(path, p, width = 8, height = 5, dpi = 300, bg = "white")
message("wrote ", path)
