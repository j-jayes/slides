# Nexer chart palette and ggplot2 theme.
#
# Colours match _brand.yml, which in turn matches the corporate deck's
# "Nexer colors" scheme. Source this from a deck's setup chunk:
#
#   source("R/nexer-ggplot.R")
#   nexer_use_fonts()

nexer_colours <- c(
  purple       = "#5A1F9F",
  purple_light = "#AA4BF4",
  orange       = "#FF5028",
  orange_light = "#FF875A",
  blue_pale    = "#D9E6F0",
  grey         = "#C8C8C8",
  grey_pale    = "#F0F0F0",
  ink          = "#000000"
)

# Ordered for categorical series: brand colour first, contrast second, then
# supporting tints. Grey is deliberately available for "everything else".
nexer_palette <- unname(nexer_colours[c(
  "purple", "orange", "purple_light", "orange_light", "blue_pale", "grey"
)])

# Set by nexer_use_fonts(). Until then the theme uses the device default,
# because naming a font Windows does not have produces one
# "font family not found in Windows font database" warning per text grob.
.nexer_fonts <- new.env(parent = emptyenv())
.nexer_fonts$heading <- ""
.nexer_fonts$body <- ""

#' Register the Nexer web fonts with R's graphics devices.
#'
#' Outfit and Inter are Google fonts and are not installed on Windows, so R
#' cannot draw with them until they are registered. This downloads and
#' registers them via showtext. Returns TRUE on success; on failure (offline,
#' packages missing) it leaves the theme on the device default rather than
#' emitting a warning for every label drawn.
#'
#' @param dpi Must match the chunk's fig-dpi, or showtext renders text at the
#'   wrong size. Quarto's HTML default is 96.
nexer_use_fonts <- function(dpi = 96) {
  have <- requireNamespace("sysfonts", quietly = TRUE) &&
    requireNamespace("showtext", quietly = TRUE)
  if (!have) {
    return(invisible(FALSE))
  }

  ok <- tryCatch({
    families <- sysfonts::font_families()
    if (!"Outfit" %in% families) sysfonts::font_add_google("Outfit", "Outfit")
    if (!"Inter" %in% families) sysfonts::font_add_google("Inter", "Inter")
    showtext::showtext_auto()
    showtext::showtext_opts(dpi = dpi)
    TRUE
  }, error = function(e) FALSE)

  if (ok) {
    .nexer_fonts$heading <- "Outfit"
    .nexer_fonts$body <- "Inter"
  }
  invisible(ok)
}

#' The font families currently registered, or "" for the device default.
#'
#' Use these instead of hardcoding "Inter" in geom_text(), so charts stay
#' warning-free when nexer_use_fonts() could not register the webfonts.
nexer_font_body <- function() .nexer_fonts$body
nexer_font_heading <- function() .nexer_fonts$heading

#' Minimal Nexer ggplot2 theme.
#'
#' Chart junk removed: no vertical grid, no legend by default (colour the
#' subtitle with ggtext instead), no axis titles unless the units are
#' non-obvious.
theme_nexer <- function(base_size = 20, base_family = NULL) {
  body_family <- base_family %||% .nexer_fonts$body
  heading_family <- .nexer_fonts$heading

  ggplot2::theme_minimal(base_size = base_size, base_family = body_family) +
    ggplot2::theme(
      plot.title = ggtext::element_markdown(
        family = heading_family, face = "bold", size = base_size * 1.15,
        colour = nexer_colours[["ink"]], margin = ggplot2::margin(b = 4)
      ),
      plot.subtitle = ggtext::element_markdown(
        family = body_family, size = base_size * 0.85, colour = "#6b6b6b",
        margin = ggplot2::margin(b = 10)
      ),
      plot.caption = ggtext::element_markdown(
        family = body_family, size = base_size * 0.65, colour = "#6b6b6b",
        hjust = 0
      ),
      plot.title.position = "plot",
      plot.caption.position = "plot",
      legend.position = "none",
      panel.grid.minor = ggplot2::element_blank(),
      panel.grid.major.x = ggplot2::element_blank(),
      panel.grid.major.y = ggplot2::element_line(colour = "#e6e6e6", linewidth = 0.4),
      axis.title = ggplot2::element_blank(),
      axis.text = ggplot2::element_text(colour = "#4a4a4a", size = base_size * 0.8)
    )
}

#' Wrap a label in a colour span, for use in ggtext titles/subtitles.
#'
#' Lets the subtitle act as the legend, so the reader decodes the colour and
#' reads the insight in one pass.
nexer_span <- function(text, colour) {
  sprintf("<span style='color:%s;'>**%s**</span>", colour, text)
}

#' Axis and value labels for large numbers: 1,000  25,000  5m  1.2bn  3tn.
#'
#' Below a million, comma thousands and `accuracy` decimals; from a million,
#' one decimal and a lowercase m, bn or tn with a trailing .0 dropped. Negative
#' numbers keep their sign; NA stays NA. Same function as in the viz-index
#' skill's R/viz.R, so a deck and a blog chart write numbers the same way.
#'
#' @param accuracy Rounding for values under a million: 1, 0.1, 0.01.
label_short <- function(accuracy = 1) {
  decimals <- max(0, -floor(log10(accuracy) + 1e-9))
  function(x) {
    a <- abs(x)
    small <- formatC(round(a / accuracy) * accuracy, format = "f",
                     digits = decimals, big.mark = ",")
    unit <- ifelse(a >= 1e12, 1e12, ifelse(a >= 1e9, 1e9, 1e6))
    suffix <- ifelse(a >= 1e12, "tn", ifelse(a >= 1e9, "bn", "m"))
    big <- paste0(sub("\\.0$", "", formatC(a / unit, format = "f", digits = 1)), suffix)
    out <- paste0(ifelse(x < 0, "-", ""), ifelse(a >= 1e6, big, small))
    out[is.na(x)] <- NA
    out
  }
}

#' Percent labels: 12%, or 12.5% with accuracy = 0.1.
#'
#' @param scale 100 when the data are proportions (0.12), 1 when they are
#'   already percentage points (12).
label_pct <- function(accuracy = 1, scale = 100) {
  scales::label_percent(accuracy = accuracy, scale = scale)
}

`%||%` <- function(a, b) if (is.null(a)) b else a
