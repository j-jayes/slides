---
name: viz-tables
description: >-
  Lay out a summary table by Wilke's six rules using gt — no vertical lines,
  no rules between data rows, text left, numbers right with the same
  decimals, headers aligned with their data. Use when asked for a "summary
  table", "format this table", "table for the report", or when the reader
  needs to read exact values rather than compare shapes.
---

# Tables: when the number is the point

A chart is for comparing; a table is for looking up. Reach for a table when
the reader needs the exact value, when there are only a handful of rows, or
when the columns are not commensurable. Wilke gives six formatting rules and
they are the whole of the craft.

Setup as in `viz-index` plus `library(gt)`, which is installed. The template
writes HTML, because gt renders to PNG only with webshot2 and a headless
browser.

## Wilke's six rules

1. **No vertical lines.** Ever.
2. **No horizontal lines between data rows.** A rule under the header and
   one above the footer is all a table needs.
3. **Text columns are left aligned.**
4. **Number columns are right aligned, with the same number of decimals
   down the whole column.**
5. **Columns of single characters are centred.**
6. **Header fields align with their data** — a header over a number column
   is right aligned too.

Instead of rules between rows, alternate row shading if the table is wide
enough to lose your place in. And unlike a figure, **a table's caption goes
above it**, because a table is read from the top like text.

## The template

[gt-six-rules.R](reference/gt-six-rules.R) turns those into `tab_options()`:

```r
summary |>
  gt(rowname_col = "class") |>
  tab_header(title = paste0(best, "s go furthest on a gallon"),
             subtitle = "Mean fuel economy and engine size by vehicle class, 234 models") |>
  tab_spanner(label = "Miles per gallon", columns = c(city, highway)) |>
  fmt_number(columns = c(city, highway, displacement), decimals = 1) |>
  fmt_integer(columns = models) |>
  cols_align(align = "left", columns = class) |>
  cols_align(align = "right", columns = c(models, city, highway, displacement)) |>
  tab_options(
    table.font.names = "Inter",
    table.border.top.style = "none", table.border.bottom.style = "none",
    column_labels.border.top.style = "none",
    column_labels.border.bottom.width = px(1.5),
    table_body.hlines.style = "none",          # rule 2
    stub.border.style = "none",                # rule 1
    heading.align = "left"
  )
```

## Rules that matter

**Sort the rows so the order is the finding.** `arrange(desc(highway))`
makes the table a ranking, and the title can then name the top row —
computed from the data, as in every other viz template.

**Same decimals down a column.** `fmt_number(decimals = 1)` for the
measured columns, `fmt_integer()` for counts. `20.1` above `20.4` above
`18.8` lines up on the decimal point; `20.1` above `20` does not.

**Group columns with a spanner, not a merged header.**
`tab_spanner(label = "Miles per gallon", columns = c(city, highway))` says
that City and Highway share their units, which is where the units belong
in a table.

**Name the rows properly.** `tools::toTitleCase()` gives "Suv" and
"2seater". Recode by hand: "SUV", "Two-seater". A table is read closely, so
sloppy labels show.

**Seven rows is comfortable; fifteen is the limit.** Past that, the reader
is scanning, which is what a chart is for. On a slide, six rows.

**Keep the source note.** Same rule as a chart: `tab_source_note("Source:
…")` in small grey text.

## On a Nexer slide

Do not export a gt table into a deck. The kit's PowerPoint filter builds
native tables from **markdown** tables, so a colleague can edit the cells;
a gt table would arrive as a picture. Write the six rules into a markdown
table instead — the `nexer-slides` skill has the styling — and keep it full
width at six rows or fewer, since a table inside a `.column` overflows the
slide with no warning. gt is for HTML reports and blog posts.

## What does not work

- **Vertical rules and boxed cells.** Wilke's rule 1, and the fastest way
  to make a table look like a spreadsheet.
- **Zebra striping on a five-row table.** It is for long tables only.
- **`gtsave()` to PNG** without webshot2 and chromote installed. The
  template writes HTML for that reason.
- **A table of twenty rows and eight columns** in a report body. Put it in
  an appendix and chart the finding.
- **Centre-aligned numbers.** The digits stop lining up.
- **A table when the claim is a comparison.** If the reader is asked which
  is bigger, draw bars.

## Before you ship

Open the HTML and check: no vertical lines, no rules between rows, numbers
right aligned with equal decimals, headers aligned with their data, the
row order meaningful, the title naming what the order shows, the source
note present.

## Related skills

`viz-index` for the conventions, `viz-amounts` for the bar chart a table
often should be, `nexer-slides` for markdown tables that survive the
PowerPoint export, `mckinsey-slides` for the benchmark-table convention in
a client deck.
