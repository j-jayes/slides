# Scatterplot with a stated fit. Points are semi-transparent so overlaps
# show as darker; the line is a linear fit and the caption says so.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)

cars <- ggplot2::mpg

# The slope is the claim: how many mpg each extra litre costs.
fit <- lm(hwy ~ displ, data = cars)
slope <- label_short(accuracy = 0.1)(-coef(fit)[["displ"]])

p <- ggplot(cars, aes(displ, hwy)) +
  geom_point(colour = viz_colours[["single"]], alpha = 0.45, size = 2.2) +
  geom_smooth(method = "lm", formula = y ~ x, se = TRUE,
              colour = viz_colours[["highlight"]], fill = viz_colours[["muted"]],
              linewidth = 0.9) +
  scale_x_continuous(breaks = 2:7) +
  labs(
    title = paste("Each extra litre of engine costs about", slope, "mpg on the highway"),
    subtitle = "Highway fuel economy against engine displacement, 234 models",
    x = "Engine displacement (litres)", y = "Highway fuel economy (miles per gallon)",
    caption = "Note: line is a linear fit with its 95% confidence band. Source: ggplot2::mpg (US EPA)"
  ) +
  theme_viz(grid = "both")

path <- file.path(out_dir, "scatter-alpha-smooth.png")
ggsave(path, p, width = 8, height = 5.5, dpi = 300, bg = "white")
message("wrote ", path)
