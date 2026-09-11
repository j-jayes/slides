# Dot plot: amounts whose axis should not start at zero. A bar's length is the
# value, so a bar axis must start at zero; a dot's position is the value, so
# the axis can be zoomed to where the differences are.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)
library(forcats)

# Mean highway fuel economy per vehicle class. Every class sits between 12 and
# 30 mpg; bars from zero would spend most of the panel on the part nobody is
# comparing.
economy <- ggplot2::mpg |>
  group_by(class) |>
  summarise(hwy = mean(hwy), n = n(), .groups = "drop") |>
  mutate(class = fct_reorder(class, hwy))

# The title's number is computed, so the claim cannot outrun the data.
gap <- label_pct()(max(economy$hwy) / min(economy$hwy) - 1)

p <- ggplot(economy, aes(hwy, class)) +
  geom_point(colour = viz_colours[["single"]], size = 4) +
  geom_text(
    aes(label = label_short(accuracy = 0.1)(hwy)),
    hjust = -0.5, family = viz_font(), size = 11 / .pt, colour = viz_colours[["text"]]
  ) +
  scale_x_continuous(limits = c(10, 32), breaks = seq(10, 30, 5)) +
  labs(
    title = paste("A compact goes", gap, "further on a gallon than a pickup"),
    subtitle = "Mean highway fuel economy by class, 234 models sold 1999 and 2008",
    x = "Highway fuel economy (miles per gallon)", y = NULL,
    caption = "Source: ggplot2::mpg (US EPA)"
  ) +
  theme_viz(grid = "v")

path <- file.path(out_dir, "dot-plot.png")
ggsave(path, p, width = 8, height = 5, dpi = 300, bg = "white")
message("wrote ", path)
