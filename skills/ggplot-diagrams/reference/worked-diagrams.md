# Three worked diagrams

Source: the operating model, delivery lifecycle and target architecture slides
of a real client deck built with this kit, genericised. Every block below has
been rendered — the placement comments record decisions that were made after
looking at a screenshot, not before.

Each assumes the standard setup chunk:

```r
source("R/nexer-ggplot.R")
source("R/nexer-diagrams.R")
nexer_use_fonts()
library(ggplot2)
```

## 1. Stacked bands — an operating model

Four bands, with arrows carrying authority downwards. The shape to reach for
when the question is *who owns what*.

```r
#| fig-width: 12
#| fig-height: 4.9

coe_header <- row_of("Center of Excellence", y = 5.75, h = 0.7,
                     fill = nexer_colours[["purple"]], ink = "white")

coe_roles <- row_of(c(
  "Head of function\nstrategy and roadmap",
  "Enterprise architect\nstandards and patterns",
  "Data governance\nquality and lineage",
  "Security\nrisk and compliance",
  "Change lead\nadoption and training"
), y = 4.6, h = 1.0)

teams <- row_of(c(
  "Commercial", "Supply chain", "Operations", "Corporate services"
), y = 2.55, h = 0.85,
fill = nexer_colours[["purple_light"]], ink = "white")

systems <- row_of(c(
  "Demand, pricing, accounts\nCRM and campaign tools\nmarket data",
  "Planning, stock, transport\nERP and warehouse systems\ncarrier feeds",
  "Yield, quality, energy\nplant historian and CMMS\nline and lab data",
  "Finance, HR, procurement\noffice suite and service desk\npolicy library"
), y = 1.05, h = 1.3, fill = nexer_colours[["blue_pale"]])

# Arrow x positions are derived from the boxes, so adding a fifth team moves
# the arrows with it.
arrows <- data.frame(
  x = teams$x + teams$w / 2, xend = teams$x + teams$w / 2,
  y = 4.5, yend = 3.5
)

bands <- data.frame(
  x = 1.95,
  y = c(5.35, 2.97, 1.7),
  label = c("Sets the rules", "Owns the outcome", "Works on these\nsystems and data")
)

ggplot() +
  nexer_arrows(arrows) +
  nexer_boxes(coe_header, size = 5, bold = TRUE) +
  nexer_boxes(coe_roles, size = 3.9) +
  nexer_boxes(teams, size = 4.5, bold = TRUE) +
  nexer_boxes(systems, size = 3.6) +
  nexer_band_labels(bands) +
  # A label, not text: the arrows pass behind it and would otherwise strike
  # through the sentence.
  annotate("label", x = 6.78, y = 4.03,
           label = "Sets standards, platform, reusable patterns and evaluation. Builds few solutions itself.",
           family = nexer_font_body(), size = 3.9, colour = "#6b6b6b",
           fill = "white", linewidth = 0, label.padding = unit(0.2, "lines")) +
  coord_cartesian(xlim = c(0.55, 11.6), ylim = c(0.9, 6.6)) +
  theme_nexer_diagram()
```

**Why it is built this way**

- `nexer_arrows()` is added *first* so the four rectangles cover the arrow tails.
- The grey sentence sits between two bands that arrows cross. `annotate("label")`
  with `fill = "white"` and `linewidth = 0` gives it an invisible backing plate;
  `annotate("text")` in the same position is struck through. Use `linewidth`, not
  the older `label.size` — the latter is ignored from ggplot2 4.0.0 and leaves a
  rounded border around the sentence.
- The band label column is why `row_of()` starts at `x0 = 2.05`, and why
  `xlim` starts at 0.55 rather than at the first box.

## 2. A gate chain — a delivery lifecycle

Left to right, with exit criteria under each gate and a rework loop returning
over the top. The shape to reach for when the question is *how work moves*.

```r
#| fig-width: 12
#| fig-height: 4.3

gates <- row_of(c(
  "1\nIntake",
  "2\nValue and\nrisk triage",
  "3\nBuild on\nthe platform",
  "4\nEvaluate\nagainst baseline",
  "5\nCharter\nand owner",
  "6\nScale and\nmonitor"
), y = 2.2, h = 1.15, x0 = 0.15, x1 = 11.5, gap = 0.2,
fill = nexer_colours[["purple"]], ink = "white")

# x0 = 0.15 because this diagram carries no band labels, so the left gutter
# would only be dead space.
flow <- data.frame(
  x = gates$x[1:5] + gates$w[1:5], xend = gates$x[2:6] - 0.03,
  y = 2.78, yend = 2.78
)

criteria <- data.frame(
  x = gates$x + gates$w / 2,
  y = 2.02,
  label = c(
    "A named business owner\nand a measurable problem",
    "Value, risk class, and\nthe data it would need",
    "Platform patterns,\nnot a new stack",
    "Beats today's number\non data it has not seen",
    "Scope of authority\nwritten down",
    "Cost, quality and usage\non one dashboard"
  )
)

# The rework loop runs above the boxes, because the exit criteria sit below
# them: routed the other way it draws a line through six labels.
loop_from <- gates$x[4] + gates$w[4] / 2
loop_to <- gates$x[2] + gates$w[2] / 2
reject <- data.frame(
  x =    c(loop_from, loop_from, loop_to),
  xend = c(loop_from, loop_to,   loop_to),
  y =    c(3.35, 3.92, 3.92),
  yend = c(3.92, 3.92, 3.40)
)

ggplot() +
  # Rows 1-2 are plain segments and row 3 carries the only arrowhead, so the
  # elbow reads as one line rather than three arrows.
  geom_segment(data = reject[1:2, ], aes(x = x, xend = xend, y = y, yend = yend),
               colour = nexer_colours[["orange"]], linewidth = 0.6, linetype = "22") +
  nexer_arrows(reject[3, ], colour = nexer_colours[["orange"]], linewidth = 0.6) +
  nexer_arrows(flow) +
  nexer_boxes(gates, size = 4.3) +
  geom_text(data = criteria, aes(x = x, y = y, label = label),
            vjust = 1, family = nexer_font_body(), size = 3.8,
            colour = "#6b6b6b", lineheight = 0.95) +
  annotate("text", x = (loop_from + loop_to) / 2, y = 4.02, vjust = 0,
           label = "Does not beat the baseline: rescope, or stop and say so",
           family = nexer_font_body(), size = 3.8,
           colour = nexer_colours[["orange"]]) +
  coord_cartesian(xlim = c(0, 11.65), ylim = c(1.3, 4.45)) +
  theme_nexer_diagram()
```

**Why it is built this way**

- **The one-arrowhead idiom.** An elbow is a three-row data frame. Draw rows 1–2
  with a plain `geom_segment()` and only the final row through `nexer_arrows()`,
  or you get an arrowhead at every corner.
- `vjust = 1` hangs the criteria text *below* its anchor, so the gap between box
  and caption stays constant however many lines a caption runs to.
- `x0 = 0.15` overrides the band-label gutter. Six gates need the width.

## 3. Layers, solid and ghost — a target architecture

Five bands, where the point is not the inventory but which pieces are **absent**.
The shape to reach for when the question is *what is missing*.

```r
#| fig-width: 12
#| fig-height: 5.0

X0 <- 2.15

experience <- row_of(c(
  "Desktop assistant", "Customer portal",
  "Service desk", "Business apps\nand dashboards"
), y = 5.55, h = 0.8, x0 = X0)

agent_row <- row_of(c(
  "Model platform\nmodels, tools, memory", "Low-code studio\ndepartmental agents",
  "Customer-facing\nagents", "Service identity\nper-agent credentials",
  "Evaluation and\nobservability"
), y = 4.3, h = 1.0, x0 = X0)
# Pick out the box that anchors the layer by overriding one cell in place.
agent_row$fill[1] <- nexer_colours[["purple"]]
agent_row$ink[1] <- "white"

know_row <- row_of(c(
  "Lakehouse\nstorage", "Data products and\nsemantic models",
  "Business glossary\nand ownership", "Catalogue and lineage",
  "API layer over\nthe ERP", "Plant data\ninto the lakehouse"
), y = 3.0, h = 1.05, x0 = X0)
know_row$fill[1] <- nexer_colours[["purple"]]
know_row$ink[1] <- "white"

systems <- row_of(c(
  "ERP", "CRM", "Service desk",
  "Maintenance\nmanagement", "Warehouse\nmanagement", "Plant historian"
), y = 1.95, h = 0.8, x0 = X0)

signals <- row_of(c(
  "Retailer sell-out", "Market panel", "Weather", "Tender outcomes"
), y = 1.15, h = 0.62, x0 = X0, fill = nexer_colours[["blue_pale"]])

platform <- row_of(
  "Cloud landing zone, identity, networking\nManaged file transfer  ·  Product data syndication  ·  Engineering tooling",
  y = 0.2, h = 0.75, x0 = X0)

bands <- data.frame(
  x = X0 - 0.12,
  y = c(5.95, 4.8, 3.52, 1.95, 0.57),
  label = c("Experience", "Agents and\norchestration", "Knowledge layer",
            "Systems and\noutside signals", "Platform")
)

ggplot() +
  nexer_boxes(experience, size = 3.7) +
  # One row_of(), sliced: solid and dashed boxes stay on the same grid.
  nexer_boxes(agent_row[1:3, ], size = 3.7) +
  nexer_ghost_boxes(agent_row[4:5, ], size = 3.5) +
  nexer_boxes(know_row[1:3, ], size = 3.7) +
  nexer_ghost_boxes(know_row[4:6, ], size = 3.5) +
  nexer_boxes(systems, size = 3.6) +
  nexer_boxes(signals, size = 3.6) +
  nexer_boxes(platform, size = 3.6) +
  nexer_band_labels(bands, size = 3.9) +
  coord_cartesian(xlim = c(0.62, 11.6), ylim = c(0.1, 6.45)) +
  # The subtitle is the legend, so no legend box is needed.
  labs(subtitle = paste0(
    nexer_span("Solid: platforms you already own", nexer_colours[["purple"]]),
    " &nbsp; · &nbsp; ",
    nexer_span("Dashed: the pieces that are missing", nexer_colours[["orange"]])
  )) +
  theme_nexer_diagram()
```

**Why it is built this way**

- **Slice, do not rebuild.** `agent_row[1:3, ]` solid and `agent_row[4:5, ]`
  ghost come from one `row_of()`, so every box in the band shares a width and a
  baseline. Two separate calls drift apart the moment a label changes.
- **Ghost boxes are the argument.** A diagram that only shows what exists is an
  inventory. The dashed boxes are what makes this an exhibit worth a slide.
- `nexer_span()` in the subtitle decodes solid against dashed in the same pass as
  reading the diagram. `theme_nexer_diagram()` renders the subtitle as markdown,
  which is what makes the colour work.
- Ghost text is set one step smaller than solid text (3.5 against 3.7), because
  orange on white at the same size reads louder than the boxes that matter.

## Sizes used here

| Diagram | `fig-width` | `fig-height` | Boxes |
|---|---|---|---|
| Operating model | 12 | 4.9 | 14 across 4 bands |
| Delivery lifecycle | 12 | 4.3 | 6 in one row |
| Target architecture | 12 | 5.0 | 26 across 6 bands |

All three are full-width, alone on their slide, and followed by a
`::: {.source}` rail. None shares a slide with `.columns` or `.stats`.
