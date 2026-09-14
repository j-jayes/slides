# Choropleth: regions shaded by a rate, in a handful of bins, on an
# equal-area projection. A rate, because a big county with a big count
# reads as "more" whether or not it is; bins, because five shades can be
# told apart and read back off the legend, a gradient cannot.
# requires: sf
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

if (!requireNamespace("sf", quietly = TRUE)) {
  stop("This template needs sf: install.packages('sf')")
}

library(ggplot2)
library(dplyr)
library(sf)

# North Carolina counties, shipped with sf: births and sudden infant deaths
# 1974-78. The rate per 1,000 births is what a map can honestly colour.
nc <- st_read(system.file("shape/nc.shp", package = "sf"), quiet = TRUE) |>
  mutate(rate = 1000 * SID74 / BIR74)

# Equal-width bins on a rounded scale; four to six is Wilke's range.
nc <- nc |>
  mutate(bin = cut(rate, breaks = c(0, 1, 2, 3, 4, 10), right = FALSE,
                   labels = c("under 1", "1 to 2", "2 to 3", "3 to 4", "4 and over")))

worst <- nc |> slice_max(rate, n = 1)

p <- ggplot(nc) +
  geom_sf(aes(fill = bin), colour = "white", linewidth = 0.2) +
  # Albers equal-area for the conterminous US (EPSG 5070): areas honest,
  # shapes close enough at state scale.
  coord_sf(crs = 5070) +
  scale_fill_brewer(palette = "Blues", drop = FALSE) +
  labs(
    title = paste0("Sudden infant deaths were highest in ", worst$NAME, " County,<br>at ",
                   label_short(accuracy = 0.1)(worst$rate), " per 1,000 births"),
    subtitle = "North Carolina counties, 1974 to 1978",
    fill = "Deaths per 1,000 births",
    caption = "Source: sf's nc dataset (Cressie, 1993)"
  ) +
  theme_viz(grid = "none") +
  theme(
    # coord_sf() draws its own graticule, which theme_viz(grid = "none")
    # does not reach: blank the panel grid as well or lat/long lines show.
    panel.grid = element_blank(),
    axis.text = element_blank(),
    legend.position = "bottom",
    legend.title.position = "top",
    legend.key.width = unit(1.6, "cm"),
    legend.key.height = unit(0.35, "cm"),
    legend.key.spacing.x = unit(0, "cm")
  )

path <- file.path(out_dir, "choropleth-rate.png")
ggsave(path, p, width = 8, height = 5, dpi = 300, bg = "white")
message("wrote ", path)
