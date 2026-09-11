# Stacked bars scaled to 100%: the share of each part within several groups.
# Best with two or three parts; the outer segments share a baseline with the
# axis, so their shares can be compared across bars at a glance.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)
library(forcats)

shares <- ggplot2::mpg |>
  mutate(drive = recode(drv, f = "Front-wheel", `4` = "Four-wheel", r = "Rear-wheel")) |>
  count(class, drive) |>
  group_by(class) |>
  mutate(share = n / sum(n)) |>
  ungroup() |>
  # Sort the bars by the share of the part that matters.
  mutate(
    class = fct_reorder(class, share * (drive == "Four-wheel"), .fun = sum),
    drive = factor(drive, levels = c("Four-wheel", "Front-wheel", "Rear-wheel"))
  )

palette <- setNames(viz_palette[1:3], levels(shares$drive))

p <- ggplot(shares, aes(share, class, fill = drive)) +
  geom_col(position = position_fill(reverse = TRUE), width = 0.75) +
  # Percentages inside any segment wide enough to hold them.
  geom_text(
    aes(label = if_else(share >= 0.08, label_pct()(share), "")),
    position = position_fill(reverse = TRUE, vjust = 0.5),
    family = viz_font(), size = 10 / .pt, colour = "white"
  ) +
  scale_fill_manual(values = palette) +
  scale_x_continuous(labels = label_pct(), expand = c(0, 0)) +
  labs(
    title = paste("Every pickup and most SUVs are", viz_span("four-wheel", palette[["Four-wheel"]]), "drive"),
    subtitle = paste(
      "Share of models by drivetrain:", viz_span("four-wheel", palette[["Four-wheel"]]),
      viz_span("front-wheel", palette[["Front-wheel"]]), viz_span("rear-wheel", palette[["Rear-wheel"]])
    ),
    x = "Share of models (%)", y = NULL,
    caption = "Source: ggplot2::mpg (US EPA), 234 models"
  ) +
  theme_viz(grid = "none")

path <- file.path(out_dir, "stacked-bars-fill.png")
ggsave(path, p, width = 8, height = 5, dpi = 300, bg = "white")
message("wrote ", path)
