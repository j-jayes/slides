# A summary table by Wilke's six rules: no vertical lines, no lines between
# data rows, text left-aligned, numbers right-aligned with the same number
# of decimals, single characters centred, headers aligned with their data.
# Writes HTML; gt needs webshot2 for PNG, which is not assumed here.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())

library(dplyr)
library(gt)

summary <- ggplot2::mpg |>
  group_by(class) |>
  summarise(
    models = n(),
    city = mean(cty),
    highway = mean(hwy),
    displacement = mean(displ),
    .groups = "drop"
  ) |>
  arrange(desc(highway)) |>
  # toTitleCase() would give "Suv" and "2seater": name the rows by hand.
  mutate(class = recode(class,
    compact = "Compact", subcompact = "Subcompact", midsize = "Midsize",
    `2seater` = "Two-seater", minivan = "Minivan", suv = "SUV", pickup = "Pickup"
  ))

# The row order is the claim, so the title comes from the first row.
best <- summary$class[1]

table <- summary |>
  gt(rowname_col = "class") |>
  tab_header(
    title = paste0(best, "s go furthest on a gallon"),
    subtitle = "Mean fuel economy and engine size by vehicle class, 234 models"
  ) |>
  cols_label(
    models = "Models",
    city = "City",
    highway = "Highway",
    displacement = "Litres"
  ) |>
  tab_spanner(label = "Miles per gallon", columns = c(city, highway)) |>
  # Same decimals down every numeric column; integers stay integers.
  fmt_number(columns = c(city, highway, displacement), decimals = 1) |>
  fmt_integer(columns = models) |>
  # Text left, numbers right, headers with their data.
  cols_align(align = "left", columns = class) |>
  cols_align(align = "right", columns = c(models, city, highway, displacement)) |>
  tab_source_note("Source: ggplot2::mpg (US EPA)") |>
  # No vertical lines, no lines between data rows: a rule under the header
  # and one above the source note are all a table needs.
  tab_options(
    table.font.names = "Inter",
    table.border.top.style = "none",
    table.border.bottom.style = "none",
    column_labels.border.top.style = "none",
    column_labels.border.bottom.width = px(1.5),
    column_labels.border.bottom.color = "#4A4A4A",
    table_body.hlines.style = "none",
    table_body.border.bottom.width = px(1),
    table_body.border.bottom.color = "#4A4A4A",
    stub.border.style = "none",
    heading.align = "left",
    heading.title.font.weight = "bold",
    source_notes.font.size = px(12),
    data_row.padding = px(6)
  ) |>
  tab_style(style = cell_text(color = "#6B6B6B"), locations = cells_source_notes())

path <- file.path(out_dir, "gt-six-rules.html")
gtsave(table, path)
message("wrote ", path)
