# The one pie chart that is allowed: a single whole, three or fewer parts,
# fractions the eye can check against a clock face. Anything else is bars.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)

# Seats in the 1976 Bundestag (Wilke's example): a coalition against an
# opposition, where "just over half" is the message.
seats <- tibble::tibble(
  party = c("CDU/CSU", "SPD", "FDP"),
  seats = c(243, 214, 39)
) |>
  mutate(
    share = seats / sum(seats),
    # Slices are drawn bottom-up in the stacking order, so reverse the factor
    # to read clockwise from the top in the order of the rows.
    party = factor(party, levels = rev(party)),
    label = paste0(party, "\n", seats, " seats, ", label_pct()(share)),
    # A slice under 15% cannot hold its label: push it outside, in dark text.
    label_x = if_else(share < 0.15, 1.75, 1),
    label_colour = if_else(share < 0.15, viz_colours[["text"]], "white")
  )

# The coalition in one colour and a tint of it, the opposition in grey: the
# pie is about the coalition's half, so only the coalition gets colour.
coalition <- viz_palette[1]
palette <- c(`CDU/CSU` = viz_colours[["muted"]], SPD = coalition,
             FDP = adjustcolor(coalition, alpha.f = 0.55))

p <- ggplot(seats, aes(x = 1, y = share, fill = party)) +
  geom_col(width = 1, colour = "white", linewidth = 1) +
  # Labels at the angular midpoint of each slice.
  geom_text(aes(x = label_x, label = label, colour = label_colour),
            position = position_stack(vjust = 0.5),
            family = viz_font(), size = 10 / .pt, lineheight = 1) +
  coord_polar(theta = "y", start = 0, direction = -1) +
  scale_fill_manual(values = palette) +
  scale_colour_identity() +
  scale_x_continuous(limits = c(0.5, 2)) +
  labs(
    title = paste(viz_span("SPD and FDP", coalition), "held just over half the seats"),
    subtitle = "Bundestag, 1976 election, 496 seats",
    x = NULL, y = NULL,
    caption = "Source: Bundestag; example from Wilke, Fundamentals of Data Visualization"
  ) +
  theme_viz(grid = "none") +
  theme(axis.text = element_blank())

path <- file.path(out_dir, "pie-one-whole.png")
ggsave(path, p, width = 6, height = 5.5, dpi = 300, bg = "white")
message("wrote ", path)
