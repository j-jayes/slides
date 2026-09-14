# A compound figure: different charts side by side, tagged a, b, c, sharing
# a title and one theme. patchwork's operators: | beside, / above, & to
# apply something to every panel.
# requires: patchwork
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

if (!requireNamespace("patchwork", quietly = TRUE)) {
  stop("This template needs patchwork: install.packages('patchwork')")
}

library(ggplot2)
library(dplyr)
library(forcats)
library(patchwork)

cars <- ggplot2::mpg

# a: amounts. b: distribution. c: association. The same colour language in
# all three: one series in midnightblue.
a <- cars |>
  count(class) |>
  mutate(class = fct_reorder(class, n)) |>
  ggplot(aes(n, class)) +
  geom_col(fill = viz_colours[["single"]], width = 0.75) +
  scale_x_continuous(expand = expansion(mult = c(0, 0.05))) +
  labs(title = "Models by class", x = "Models", y = NULL) +
  theme_viz(grid = "v")

b <- ggplot(cars, aes(hwy)) +
  geom_histogram(binwidth = 2, fill = viz_colours[["single"]]) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
  labs(title = "Highway fuel economy", x = "Miles per gallon", y = "Models") +
  theme_viz()

c <- ggplot(cars, aes(displ, hwy)) +
  geom_point(colour = viz_colours[["single"]], alpha = 0.4) +
  labs(title = "Economy against engine size", x = "Displacement (litres)",
       y = "Highway miles per gallon") +
  theme_viz(grid = "both")

# Panel titles are demoted to plain text, since the compound title is the
# one that carries the claim.
panel_title <- theme(plot.title = ggtext::element_markdown(face = "plain", size = 12))

p <- (a | b | c) +
  plot_annotation(
    tag_levels = "a",
    title = "Most cars are SUVs or compacts, and the bigger the engine the thirstier the car",
    subtitle = "234 models sold in 1999 and 2008",
    caption = "Source: ggplot2::mpg (US EPA)",
    theme = theme_viz()
  ) &
  panel_title &
  theme(plot.tag = element_text(family = viz_font(), face = "bold", size = 12,
                                colour = viz_colours[["grey_text"]]))

path <- file.path(out_dir, "patchwork-tagged.png")
ggsave(path, p, width = 12, height = 4.5, dpi = 300, bg = "white")
message("wrote ", path)
