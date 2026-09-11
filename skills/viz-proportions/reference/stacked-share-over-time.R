# Stacked shares over time: how the composition of a whole changed. The
# largest parts sit against the axis, where their shares can be read; the
# rest are lumped into Other at the top.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)
library(forcats)

shares <- ggplot2::txhousing |>
  group_by(city, year) |>
  summarise(sales = sum(sales, na.rm = TRUE), .groups = "drop") |>
  # Keep the four largest markets over the whole period; the rest are Other.
  mutate(city = fct_lump_n(city, n = 4, w = sales, other_level = "Other")) |>
  group_by(year, city) |>
  summarise(sales = sum(sales), .groups = "drop") |>
  group_by(year) |>
  mutate(share = sales / sum(sales)) |>
  ungroup() |>
  # Largest first so it sits on the baseline; Other last so it is on top.
  mutate(city = fct_reorder(city, sales, .fun = sum, .desc = TRUE),
         city = fct_relevel(city, "Other", after = Inf))

palette <- c(setNames(viz_palette[1:4], setdiff(levels(shares$city), "Other")),
             Other = viz_colours[["muted"]])

# Direct labels at the right edge, at the vertical middle of each band. The
# bands stack from the first level upwards, so the cumulative sum runs in
# level order.
ends <- shares |>
  filter(year == max(year)) |>
  arrange(city) |>
  mutate(mid = cumsum(share) - share / 2)

p <- ggplot(shares, aes(year, share, fill = city)) +
  geom_area(position = position_stack(reverse = TRUE), colour = "white", linewidth = 0.3) +
  geom_text(data = ends, aes(x = max(year) + 0.3, y = mid, label = city),
            hjust = 0, family = viz_font(), size = 10 / .pt, colour = viz_colours[["text"]]) +
  scale_fill_manual(values = palette) +
  scale_x_continuous(breaks = seq(2000, 2015, 5), expand = c(0, 0)) +
  scale_y_continuous(labels = label_pct(), expand = c(0, 0)) +
  coord_cartesian(clip = "off") +
  labs(
    title = "Four markets have taken a steady half of Texas home sales",
    subtitle = "Share of homes sold per year, four largest markets and all others",
    x = NULL, y = "Share of homes sold (%)",
    caption = "Source: ggplot2::txhousing (Texas A&M Real Estate Center)"
  ) +
  theme_viz(grid = "none") +
  theme(plot.margin = margin(5.5, 80, 5.5, 5.5))

path <- file.path(out_dir, "stacked-share-over-time.png")
ggsave(path, p, width = 8, height = 5, dpi = 300, bg = "white")
message("wrote ", path)
