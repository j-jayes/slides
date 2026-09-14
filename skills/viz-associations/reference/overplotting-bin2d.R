# Two-dimensional bins for a scatter with too many points to draw. Each
# rectangle is coloured by how many points fall in it, which alpha alone
# cannot show past a few thousand points. (geom_hex() needs the hexbin
# package; geom_bin2d() needs nothing.)
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)

stones <- ggplot2::diamonds |> filter(carat <= 3)
typical <- median(stones$carat)

p <- ggplot(stones, aes(carat, price)) +
  geom_bin2d(bins = 60) +
  scale_fill_viridis_c(labels = label_short(), option = "D") +
  # Price spans two orders of magnitude: a log axis, labelled in dollars.
  scale_y_log10(labels = label_short(), breaks = c(500, 1000, 2000, 5000, 10000, 20000)) +
  scale_x_continuous(breaks = seq(0, 3, 0.5)) +
  labs(
    title = paste0("Half of all diamonds weigh under ", typical,
                   " carats,<br>and price climbs steeply above that"),
    subtitle = "Price against weight, 54,000 diamonds, log scale",
    x = "Weight (carats)", y = "Price (USD, log scale)", fill = "Diamonds per bin",
    caption = "Source: ggplot2::diamonds"
  ) +
  theme_viz(grid = "both") +
  theme(
    legend.position = "bottom",
    legend.title.position = "top",
    legend.key.width = unit(2.4, "cm"),
    legend.key.height = unit(0.35, "cm")
  )

path <- file.path(out_dir, "overplotting-bin2d.png")
ggsave(path, p, width = 8, height = 6.5, dpi = 300, bg = "white")
message("wrote ", path)
