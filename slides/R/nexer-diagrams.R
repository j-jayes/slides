# Labelled-box diagrams in the Nexer palette, drawn with ggplot2.
#
#   source("R/nexer-ggplot.R")
#   source("R/nexer-diagrams.R")
#
# Why ggplot and not Mermaid: a knitr figure is a paragraph holding a lone
# Image, which pptx-nexer.lua wraps in a pandoc.Figure -- and pandoc will not
# split a slide before a Figure. Mermaid output slips past that guard, so the
# slide splits and the node text is clipped (Quarto 1.8.25, 2026-09-10). These
# helpers go through the same image path as the charts, so a diagram and a
# chart share fonts, colours and export behaviour.
#
# Everything is placed on an explicit x/y grid in arbitrary units -- there is no
# layout engine. That is the point: a diagram on a slide has five to fifteen
# boxes and hand-placing them is faster than fighting a solver.

#' Lay out n boxes evenly across a horizontal band.
#'
#' Every diagram is built from these rows, which is what keeps spacing
#' consistent between them and between decks. Widths are derived, never typed:
#' give it the labels and the band, and it divides what is left after the gaps.
#'
#' @param labels Character vector, one per box. Newlines are honoured.
#' @param y Bottom edge of the band.
#' @param h Box height.
#' @param x0,x1 Left and right edge of the band. The default `x0` leaves a
#'   gutter wide enough for `nexer_band_labels()`; start at 0.15 instead when
#'   the diagram carries no band labels.
#' @param gap Space between boxes, in the same units.
#' @return A data frame with the columns `nexer_boxes()` expects.
row_of <- function(labels, y, h, x0 = 2.05, x1 = 11.5, gap = 0.15,
                   fill = nexer_colours[["grey_pale"]],
                   ink = nexer_colours[["ink"]]) {
  n <- length(labels)
  w <- (x1 - x0 - gap * (n - 1)) / n
  data.frame(
    x = x0 + (seq_len(n) - 1) * (w + gap), y = y, w = w, h = h,
    label = labels, fill = fill, ink = ink
  )
}

#' A blank canvas: no axes, no grid, nothing but the shapes you draw.
theme_nexer_diagram <- function() {
  ggplot2::theme_void(base_family = nexer_font_body()) +
    ggplot2::theme(
      legend.position = "none",
      plot.margin = ggplot2::margin(2, 2, 2, 2),
      plot.title = ggtext::element_markdown(
        family = nexer_font_heading(), face = "bold", size = 15,
        colour = nexer_colours[["ink"]], margin = ggplot2::margin(b = 2)
      ),
      plot.subtitle = ggtext::element_markdown(
        family = nexer_font_body(), size = 12, colour = "#6b6b6b",
        margin = ggplot2::margin(b = 6)
      ),
      plot.title.position = "plot"
    )
}

#' Filled boxes with centred labels.
#'
#' @param d A data frame with x, y (bottom-left corner), w, h, label, and
#'   optionally fill and ink (label colour). Newlines in `label` are honoured.
#' @param size Label size in mm, as ggplot2 counts it.
nexer_boxes <- function(d, size = 4, bold = FALSE) {
  if (is.null(d$fill)) d$fill <- nexer_colours[["grey_pale"]]
  if (is.null(d$ink)) d$ink <- nexer_colours[["ink"]]
  list(
    ggplot2::geom_rect(
      data = d, inherit.aes = FALSE,
      ggplot2::aes(xmin = x, xmax = x + w, ymin = y, ymax = y + h, fill = fill)
    ),
    ggplot2::geom_text(
      data = d, inherit.aes = FALSE,
      ggplot2::aes(x = x + w / 2, y = y + h / 2, label = label, colour = ink),
      family = nexer_font_body(), size = size, lineheight = 0.95,
      fontface = if (bold) "bold" else "plain"
    ),
    ggplot2::scale_fill_identity(),
    ggplot2::scale_colour_identity()
  )
}

#' Outlined boxes -- used for the gaps, which are not there yet.
nexer_ghost_boxes <- function(d, size = 3.6, colour = nexer_colours[["orange"]]) {
  list(
    ggplot2::geom_rect(
      data = d, inherit.aes = FALSE, fill = "white", colour = colour,
      linetype = "22", linewidth = 0.6,
      ggplot2::aes(xmin = x, xmax = x + w, ymin = y, ymax = y + h)
    ),
    ggplot2::geom_text(
      data = d, inherit.aes = FALSE, colour = colour,
      ggplot2::aes(x = x + w / 2, y = y + h / 2, label = label),
      family = nexer_font_body(), size = size, lineheight = 0.95
    )
  )
}

#' A row label sitting to the left of a band of boxes.
nexer_band_labels <- function(d, size = 3.6) {
  ggplot2::geom_text(
    data = d, inherit.aes = FALSE, hjust = 1,
    ggplot2::aes(x = x, y = y, label = label),
    family = nexer_font_body(), size = size, colour = "#6b6b6b",
    lineheight = 0.95
  )
}

#' Arrows between boxes, drawn as straight segments.
nexer_arrows <- function(d, colour = nexer_colours[["grey"]], linewidth = 0.7) {
  ggplot2::geom_segment(
    data = d, inherit.aes = FALSE, colour = colour, linewidth = linewidth,
    ggplot2::aes(x = x, y = y, xend = xend, yend = yend),
    arrow = grid::arrow(length = grid::unit(0.16, "cm"), type = "closed")
  )
}
