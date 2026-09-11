---
name: ggplot-diagrams
description: >-
  Draw box-and-arrow diagrams — operating models, process flows, layered
  architectures — as ggplot figures, so one source renders to both Reveal.js
  and editable PowerPoint. Use when a slide needs a diagram rather than a
  chart, when a Mermaid diagram breaks the PowerPoint export, or when asked to
  "draw the architecture", "add a flow diagram" or "diagram this process".
---

# Diagrams that survive PowerPoint

A consulting deck needs three or four exhibits that are not charts: who owns
what, how work moves through gates, which platforms sit on which layer. Draw
them with `geom_rect()` and `geom_text()` on a hand-placed grid. That looks like
more work than Mermaid and is less, because it is the only route that reaches
PowerPoint intact — and a diagram then shares fonts, palette and export
behaviour with every chart in the deck.

The helpers are `slides/R/nexer-diagrams.R`. Source it **after**
`nexer-ggplot.R`, which it depends on for `nexer_colours` and
`nexer_font_body()`:

```r
source("R/nexer-ggplot.R")
source("R/nexer-diagrams.R")
nexer_use_fonts()
```

`slides/template.qmd` carries a working example — the "Target state" slide.
Copy it rather than starting from an empty canvas.

## Why ggplot and not Mermaid

A knitr figure arrives at pandoc as a paragraph holding a lone `Image`, and
`pptx-nexer.lua` wraps exactly that shape in a `pandoc.Figure`. **Pandoc never
splits a slide before a Figure**, so the diagram, its kicker, its rule and its
source rail stay together on one slide.

Mermaid output slips past that guard. Tested at Quarto 1.8.25 on 2026-09-10 —
two defects, both PowerPoint-only:

| Defect | What you see |
|---|---|
| The slide splits | Action title and diagram on one slide; the kicker, rule and source rail pushed onto an untitled next slide |
| Node text is clipped | Headless Chromium lays out with a font it does not have: "Intak", "Build on platf", "Scale and monit" |

Reveal.js renders Mermaid correctly, which is what makes this expensive to
discover — the deck looks right until someone opens the `.pptx`.

Raw HTML blocks are worse: the pptx writer drops them entirely.

## The helpers

| Function | Contract |
|---|---|
| `row_of(labels, y, h, ...)` | Lays out n boxes evenly across a band and returns the data frame the others expect. Widths are derived, never typed. |
| `nexer_boxes(d, size, bold)` | Filled rectangles with centred labels. A newline in a label is honoured. |
| `nexer_ghost_boxes(d, size, colour)` | Dashed outline, white fill, orange text — the "does not exist yet" idiom. Ignores `fill`/`ink`. |
| `nexer_band_labels(d, size)` | Right-aligned row label in the left gutter. Needs `x`, `y`, `label`. |
| `nexer_arrows(d, colour, linewidth)` | Straight segments with a closed head. Needs `x`, `y`, `xend`, `yend`. |
| `theme_nexer_diagram()` | A blank canvas — `theme_void()` plus markdown title and subtitle. |

`nexer_boxes()` returns a `list()` of layers including `scale_*_identity()`, so
`fill` and `ink` are literal hex and calling it several times per plot is safe.

## The grid

`x, y` is the **bottom-left corner** of a box, in arbitrary units. There is no
layout engine, and that is deliberate: a slide diagram has five to fifteen
boxes, and placing them by hand is faster than fighting a solver.

Build every band with `row_of()`, so spacing stays consistent within a diagram
and between decks:

```r
teams <- row_of(c("Commercial", "Operations", "Corporate"), y = 1.70, h = 0.85,
                fill = nexer_colours[["purple_light"]], ink = "white")
```

Its default band runs `x0 = 2.05` to `x1 = 11.5`, leaving a left gutter for
`nexer_band_labels()`. Pass `x0 = 0.15` when the diagram has no band labels.

Because the theme is `theme_void()` there are no axes, so
**`coord_cartesian(xlim=, ylim=)` is the only framing tool.** Set it explicitly
on every diagram and leave about 0.2 units of margin around the outermost box.

Derive positions from the boxes rather than retyping numbers. It is what keeps a
diagram correct after you add a column:

```r
arrows <- data.frame(
  x = teams$x + teams$w / 2, xend = teams$x + teams$w / 2,
  y = 3.55, yend = 2.65
)
```

## Sizing for both formats

The two formats disagree about what a figure size means, and this is the part
that bites:

- **Reveal.js** is 1600 × 900 and honours the absolute size.
- **PowerPoint ignores image `width`/`height` entirely.** Pandoc scales every
  image to fit its placeholder. Only the **aspect ratio** carries across.

So set `fig-width`/`fig-height` to get the aspect right, and never try to
control pptx size with an attribute. Ratios that work:

| Exhibit | Size |
|---|---|
| Full-width diagram | `fig-width: 12`, `fig-height: 4.2–5.0` |
| Full-width chart | `fig-width: 12`, `fig-height: 3.7` |
| Chart in a 50–55% column | `fig-width: 8`, `fig-height: 4.6` |

Text `size` is in **millimetres, set at the call site**, and is *not* inherited
from the theme. A figure that will be scaled down into a column therefore needs
visibly larger `size` values than a full-width one — around 5.4 in a column
against 3.6–4.6 full width.

## Layer order, and the four collisions

**Arrows first, boxes second.** Segments then disappear behind the rectangles
they connect, so an arrow can be aimed at a box's centre without being seen to
enter it.

**Punch a line through text with a label, not text.** Where an arrow passes
behind a sentence, `annotate("text", ...)` is struck through by it:

```r
annotate("label", x = 6.78, y = 4.03, label = "Sets standards and patterns.",
         family = nexer_font_body(), size = 3.9, colour = "#6b6b6b",
         fill = "white", linewidth = 0, label.padding = unit(0.2, "lines"))
```

`linewidth = 0` is what removes the border. Older examples pass
`label.size = NA`; that parameter was removed in ggplot2 4.0.0 and is now
silently ignored, leaving a rounded box drawn around the sentence.

**Route a loop away from the side carrying labels.** A rework arrow returning
from gate 4 to gate 2 runs *above* the boxes when the exit criteria sit below
them. Routed the other way it draws a line through six captions.

**Slice one `row_of()` rather than building two.** Solid and dashed boxes stay
on one grid that way:

```r
foundations <- row_of(c("Data platform", "Integration", "Identity", "Monitoring"),
                      y = 0.40, h = 1.0)
nexer_boxes(foundations[1:2, ])        # in place
nexer_ghost_boxes(foundations[3:4, ])  # missing
```

Override a single cell in place — `d$fill[1] <- nexer_colours[["purple"]]` — to
pick out the one box that anchors a layer.

Use `nexer_span()` in `labs(subtitle=)` as the legend, since the subtitle is
markdown. It tells the reader what solid and dashed mean without a legend box.

## Verifying it

A diagram is the slide element most likely to look right in HTML and be wrong in
PowerPoint, so render both and **look at them**. From `slides/`:

```bash
quarto render my-deck.qmd
python tools/check_pptx.py ../reports/my-deck.pptx
python tools/shoot_slides.py _site/my-deck.html --all
powershell -File tools/shoot_pptx.ps1 -Deck ../reports/my-deck.pptx
```

`check_pptx.py` must show the diagram slide on **`Title and Content`**. If it
reports `Content with Caption`, or the deck grew a slide, the figure was not
wrapped and the slide split — the exact failure this technique exists to avoid.

In the screenshots, look for clipped labels, arrows crossing text rather than
passing behind boxes, ghost boxes too faint to read, and band labels colliding
with the first column.

## What does not work

- **A diagram slide must be alone.** No `.columns` and no `.stats` beside it —
  pandoc splits the slide at a columns block, and the stat row is absolutely
  positioned over whatever else is there. A `::: {.source}` rail after the chunk
  is fine, and is what the filter is built for.
- **Nothing stops a tall figure overflowing.** The stylesheet sets no
  `max-height` on Reveal.js images, so a diagram taller than the 900px slide is
  cut off with no warning. Keep `fig-height` at or under 5.
- **`nexer_use_fonts()` is not optional.** R cannot draw with a font it has not
  registered, and without it you get one warning per label and the wrong face.
- **Do not "fix" the dpi mismatch.** `nexer_use_fonts()` sets showtext to a
  nominal 96 while knitr writes at 192 through `fig.retina: 2`. That pairing is
  what renders correctly; changing one without the other resizes every label.

## Related skills

`jonathan-slides` is the structure — two-tier titles, evidence over prose.
`nexer-slides` is the skin, and carries the placement rules for every other
branded component. `mckinsey-slides` is the rigour. This skill covers the one
exhibit type none of those do.

Three worked diagrams, with the reasoning behind each placement, are in
[reference/worked-diagrams.md](reference/worked-diagrams.md).
