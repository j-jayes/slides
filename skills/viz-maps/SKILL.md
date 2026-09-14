---
name: viz-maps
description: >-
  Draw a choropleth in ggplot2 with sf — a rate rather than a count, four to
  six bins, an equal-area projection, a quiet outline. Use when asked for a
  "map", "choropleth", "by county", "by region", "by country", "shade the
  areas by", or when the data has a geography column.
---

# Maps: a choropleth that does not lie

A map colours regions, and a region's area is doing work whether you meant
it or not. Wilke's two rules follow from that: colour a **density or rate**,
because area already multiplies a count; and use an **equal-area
projection**, because a projection that distorts area distorts the data.

Setup as in `viz-index`, plus `install.packages("sf")`. The template uses
the North Carolina shapefile that ships inside sf, so it needs no download.

## Which chart

| Situation | Reach for | Template |
|---|---|---|
| A rate or share by region | Choropleth, 4–6 bins, sequential palette, equal-area projection | [choropleth-rate.R](reference/choropleth-rate.R) |
| A count by region | Not a choropleth: sorted bars (`viz-amounts`), or a cartogram |
| Points with coordinates | `geom_sf()` on a point layer over a quiet base layer |
| A value that must be read exactly | A table or bars beside the map, not colour |

## The template

```r
nc <- st_read(system.file("shape/nc.shp", package = "sf"), quiet = TRUE) |>
  mutate(rate = 1000 * SID74 / BIR74,                     # a rate, not a count
         bin = cut(rate, breaks = c(0, 1, 2, 3, 4, 10), right = FALSE,
                   labels = c("under 1", "1 to 2", "2 to 3", "3 to 4", "4 and over")))

ggplot(nc) +
  geom_sf(aes(fill = bin), colour = "white", linewidth = 0.2) +
  coord_sf(crs = 5070) +                                  # Albers equal-area
  scale_fill_brewer(palette = "Blues", drop = FALSE) +
  theme_viz(grid = "none") +
  theme(panel.grid = element_blank(), axis.text = element_blank(),
        legend.position = "bottom", legend.title.position = "top",
        legend.key.width = unit(1.6, "cm"), legend.key.height = unit(0.35, "cm"),
        legend.key.spacing.x = unit(0, "cm"))
```

## Rules that matter

**Colour a rate, never a raw count.** Deaths per thousand births, sales per
capita, share of the population. A count map shows you where the people
are, which you already knew.

**Bin the scale: four to six classes.** Wilke's number. A binned legend can
be read back off the map — "this county is in the 2-to-3 band" — where a
continuous gradient can only be read as darker or lighter. `cut()` with
round breaks, and `drop = FALSE` on the scale so an empty class still
appears in the legend and the bands stay evenly spaced.

**Equal-area projection.** `coord_sf(crs = 5070)` is Albers for the
conterminous United States; 3035 for Europe, 3577 for Australia, and
Goode homolosine (54052) for a world map. Web Mercator (3857) is for tiles,
not for data: it makes Greenland look larger than Africa.

**`theme_viz(grid = "none")` is not enough.** `coord_sf()` draws its own
graticule, which lives in `panel.grid` and survives the theme's grid
argument. Blank `panel.grid` explicitly or lat/long lines run across the
map — a mistake this template made on its first render.

**Quiet outlines.** `colour = "white", linewidth = 0.2`. Black borders at
full weight turn a map of 100 counties into a drawing of 100 borders.

**A single-hue sequential palette.** Blues, Greens, viridis. A diverging
palette only when the values genuinely diverge from a meaningful midpoint,
and then see `viz-colour` for the symmetric-limits rule.

**Name the extreme in the title.** "Sudden infant deaths were highest in
Anson County, at 9.6 per 1,000 births" — computed with `slice_max()`, so
the claim tracks the data. A map without a title is a lookup table.

**Drop the axes.** Latitude and longitude tick labels tell the reader
nothing they want. `axis.text = element_blank()`.

**A world map needs rnaturalearth**, which downloads its data — so it is
not in the template. `rnaturalearth::ne_countries(scale = "medium",
returnclass = "sf")` with `coord_sf(crs = "+proj=igh")` is the world
equivalent of the above.

## On a Nexer slide

A map is a full-width exhibit: `fig-width: 12, fig-height: 5`, alone on the
slide, with the source in the `::: {.source}` rail. Fill with a purple
sequential ramp — `scale_fill_brewer()` has no Nexer palette, so use
`scale_fill_manual()` with a ramp from `grey_pale` to
`nexer_colours[["purple"]]` across the bins, and `orange` for a single
highlighted region. Legend at the bottom, since `theme_nexer()` hides it by
default.

## What does not work

- **A choropleth of counts.** Big empty regions shout.
- **Web Mercator for data.** Area distortion grows with latitude.
- **A continuous gradient with 100 regions.** Nobody can read a value off
  it; bin.
- **Leaving `panel.grid` on.** The graticule cuts across the regions.
- **A map when the question is "which is biggest".** That is a bar chart;
  geography is a distraction unless location is part of the answer.
- **`coord_fixed()` or `coord_cartesian()` on longitude and latitude.**
  Degrees are not a flat grid; `coord_sf()` projects properly.

## Before you ship

`viz-review`, with these lines first: a rate not a count; four to six bins
with a legend that can be read back; an equal-area projection; no
graticule; the extreme named in the title and computed.

## Related skills

`viz-index` for the conventions, `viz-colour` for the sequential and
diverging rules, `viz-amounts` for the bar chart a map often should have
been.
