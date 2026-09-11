# Top-n bars per group as facets: one panel per year, each sorted on its own,
# in place of a grouped bar chart. Reordering within a facet needs its own
# trick, done here without the tidytext package.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)
library(forcats)

# Five largest markets in each of three years. A factor has one order, so to
# sort each panel separately the level is "city|year" (unique per panel),
# ordered by value, and the axis labels strip the "|year" back off.
top <- ggplot2::txhousing |>
  filter(year %in% c(2005, 2010, 2015)) |>
  group_by(year, city) |>
  summarise(sales = sum(sales, na.rm = TRUE), .groups = "drop") |>
  group_by(year) |>
  slice_max(sales, n = 5) |>
  ungroup() |>
  mutate(key = fct_reorder(paste(city, year, sep = "|"), sales))

p <- ggplot(top, aes(sales, key)) +
  geom_col(fill = viz_colours[["single"]], width = 0.75) +
  facet_wrap(vars(year), ncol = 1, scales = "free_y") +
  scale_y_discrete(labels = function(x) sub("\\|.*$", "", x)) +
  scale_x_continuous(labels = label_short(), expand = expansion(mult = c(0, 0.05))) +
  labs(
    title = "The five largest Texas markets kept the same order for a decade",
    subtitle = "Homes sold per year, five largest metro areas in each year",
    x = "Homes sold", y = NULL,
    caption = "Source: ggplot2::txhousing (Texas A&M Real Estate Center)"
  ) +
  theme_viz(grid = "v") +
  theme(panel.spacing.y = unit(1, "lines"))

path <- file.path(out_dir, "bars-facets-topn.png")
ggsave(path, p, width = 8, height = 7, dpi = 300, bg = "white")
message("wrote ", path)
