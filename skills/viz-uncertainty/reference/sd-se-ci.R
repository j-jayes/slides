# The same means drawn with three different bars: standard deviation (how
# spread the data are), standard error (how well the mean is known), and a
# 95% confidence interval (about two standard errors). Wilke: never confuse
# the first with the other two, and always say which one you drew.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)
library(forcats)
library(tidyr)

stats <- ggplot2::mpg |>
  group_by(class) |>
  summarise(mean = mean(hwy), sd = sd(hwy), n = n(), .groups = "drop") |>
  mutate(se = sd / sqrt(n), ci = 1.96 * se,
         class = fct_reorder(class, mean)) |>
  pivot_longer(c(sd, se, ci), names_to = "bar", values_to = "half") |>
  mutate(bar = factor(bar, levels = c("sd", "se", "ci"),
                      labels = c("± 1 standard deviation\nhow spread out the cars are",
                                 "± 1 standard error\nhow precisely the mean is known",
                                 "95% confidence interval\n± 1.96 standard errors")))

p <- ggplot(stats, aes(mean, class)) +
  geom_errorbar(aes(xmin = mean - half, xmax = mean + half), width = 0.3,
                colour = viz_colours[["single"]], linewidth = 0.6) +
  geom_point(colour = viz_colours[["single"]], size = 2.6) +
  facet_wrap(vars(bar), ncol = 3) +
  scale_x_continuous(breaks = seq(10, 40, 10)) +
  labs(
    title = "Three bars, three meanings: the same means look sure or unsure depending on which you draw",
    subtitle = "Mean highway fuel economy by class, 234 models",
    x = "Highway fuel economy (miles per gallon)", y = NULL,
    caption = "Source: ggplot2::mpg (US EPA)"
  ) +
  theme_viz(grid = "v") +
  theme(panel.spacing.x = unit(1.5, "lines"))

path <- file.path(out_dir, "sd-se-ci.png")
ggsave(path, p, width = 11, height = 4.5, dpi = 300, bg = "white")
message("wrote ", path)
