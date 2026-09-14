# Paired measurements on one scatter, with the x = y line drawn so the eye
# reads "above the line" as "higher than its pair". Equal axis scales are
# what make the diagonal mean equality.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)

cars <- ggplot2::mpg
advantage <- label_short(accuracy = 0.1)(mean(cars$hwy - cars$cty))
lim <- range(c(cars$cty, cars$hwy))

p <- ggplot(cars, aes(cty, hwy)) +
  # The reference line first, the points over it.
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", colour = viz_colours[["reference"]]) +
  geom_point(colour = viz_colours[["single"]], alpha = 0.4, size = 2.2) +
  annotate("text", x = lim[2] - 1, y = lim[2] - 1, label = "highway = city", hjust = 1, vjust = -0.6,
           angle = 45, family = viz_font(), size = 9 / .pt, colour = viz_colours[["grey_text"]]) +
  coord_equal(xlim = lim, ylim = lim) +
  labs(
    title = paste("Every car does better on the highway,<br>by", advantage, "mpg on average"),
    subtitle = "Highway against city fuel economy, 234 models",
    x = "City fuel economy (miles per gallon)", y = "Highway fuel economy (miles per gallon)",
    caption = "Source: ggplot2::mpg (US EPA)"
  ) +
  theme_viz(grid = "both")

path <- file.path(out_dir, "paired-xy-line.png")
ggsave(path, p, width = 6.5, height = 6.5, dpi = 300, bg = "white")
message("wrote ", path)
