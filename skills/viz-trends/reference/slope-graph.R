# Slope graph: two points in time for a handful of categories, each joined by
# a line whose slope is the change. For a few items whose identity matters;
# a scatter with an x = y line when there are many.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)

economy <- ggplot2::mpg |>
  group_by(class, year) |>
  summarise(hwy = mean(hwy), .groups = "drop")

# One class is the story; the rest are grey context.
star <- economy |>
  group_by(class) |>
  summarise(delta = hwy[year == 2008] - hwy[year == 1999], .groups = "drop") |>
  slice_max(delta, n = 1)

economy <- economy |>
  mutate(
    colour = if_else(class == star$class, viz_colours[["highlight"]], viz_colours[["muted"]]),
    label = paste(class, label_short(accuracy = 0.1)(hwy))
  )

p <- ggplot(economy, aes(year, hwy, group = class, colour = colour)) +
  geom_line(linewidth = 1) +
  geom_point(size = 2.5) +
  geom_text(data = filter(economy, year == 1999), aes(label = label),
            hjust = 1, nudge_x = -0.3, family = viz_font(), size = 10 / .pt) +
  geom_text(data = filter(economy, year == 2008), aes(label = label),
            hjust = 0, nudge_x = 0.3, family = viz_font(), size = 10 / .pt) +
  scale_colour_identity() +
  scale_x_continuous(breaks = c(1999, 2008), limits = c(1995, 2012)) +
  labs(
    title = paste0(viz_span(tools::toTitleCase(star$class), viz_colours[["highlight"]]),
                   " gained the most highway mileage between 1999 and 2008"),
    subtitle = "Mean highway fuel economy by vehicle class, miles per gallon",
    x = NULL, y = NULL,
    caption = "Source: ggplot2::mpg (US EPA)"
  ) +
  theme_viz(grid = "none") +
  theme(axis.text.y = element_blank())

path <- file.path(out_dir, "slope-graph.png")
ggsave(path, p, width = 8, height = 5.5, dpi = 300, bg = "white")
message("wrote ", path)
