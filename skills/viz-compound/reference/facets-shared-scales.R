# Small multiples: the same chart repeated for each group, panels sharing
# both axes so the reader compares instead of re-learning, ordered by
# something meaningful rather than alphabetically.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)
library(forcats)

cities <- c("Houston", "Dallas", "Austin", "San Antonio", "Fort Worth", "El Paso")

sales <- ggplot2::txhousing |>
  filter(city %in% cities) |>
  group_by(city, year) |>
  summarise(sales = sum(sales, na.rm = TRUE), .groups = "drop") |>
  # Panels in order of size, largest first, so the grid reads as a ranking.
  mutate(city = fct_reorder(city, sales, .fun = sum, .desc = TRUE))

# Each panel's peak year is marked, and the title reports how many peaked
# before the 2008 crash. The count is spelled out: a title should not open
# with a numeral, and "4 of the six" mixes two ways of writing a number.
peaks <- sales |> group_by(city) |> slice_max(sales, n = 1) |> ungroup()
before <- c("One", "Two", "Three", "Four", "Five", "Six")[sum(peaks$year < 2008)]

p <- ggplot(sales, aes(year, sales)) +
  geom_area(fill = viz_colours[["single"]], alpha = 0.15) +
  geom_line(colour = viz_colours[["single"]], linewidth = 0.9) +
  geom_point(data = peaks, colour = viz_colours[["highlight"]], size = 2.4) +
  geom_text(data = peaks, aes(label = year), vjust = -0.8,
            family = viz_font(), size = 9 / .pt, colour = viz_colours[["highlight"]]) +
  # One scale for every panel: a bar or line means the same height everywhere.
  facet_wrap(vars(city), ncol = 3) +
  scale_x_continuous(breaks = c(2000, 2010)) +
  scale_y_continuous(labels = label_short(), limits = c(0, NA),
                     expand = expansion(mult = c(0, 0.15))) +
  labs(
    title = paste(before, "of the six largest Texas markets peaked before the 2008 crash"),
    subtitle = "Homes sold per year; the dot marks each market's best year",
    x = NULL, y = "Homes sold",
    caption = "Source: ggplot2::txhousing (Texas A&M Real Estate Center)"
  ) +
  theme_viz() +
  theme(panel.spacing = unit(1.2, "lines"))

path <- file.path(out_dir, "facets-shared-scales.png")
ggsave(path, p, width = 8, height = 5.5, dpi = 300, bg = "white")
message("wrote ", path)
