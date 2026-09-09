---
name: nexer-slides
description: >-
  Start, style and export a Nexer Insight branded presentation using the Quarto
  Reveal.js slide kit — correct colours, logo, typography, and PowerPoint
  export via the Nexer reference template. Use when a deck is for Nexer, a Nexer
  client, or when asked to "brand this deck" or "export to PowerPoint".
---

# Nexer-branded slides

The kit is the Quarto project containing `_extensions/nexer/` — usually
`slides/` in a client repo, the repo root in the kit's own. **Every path below is
relative to it**, so `cd` there first. If the project has no kit yet, create one:

```bash
quarto use template j-jayes/slides    # name the directory `slides`
```

It renders one source `.qmd` to Reveal.js HTML and to editable PowerPoint, both
on brand.

Every colour and font role here is lifted from the real corporate deck
(`temp/Sales presentation 2026.pptx` → `ppt/theme/theme1.xml`, colour scheme
"Nexer colors", font scheme "Nexer fonts"). Nothing is invented.

That deck and the co-branding PDF are **not kept in this repo** (~90 MB, and
nothing at render time needs them). Everything extracted from them -- palette,
logo, swirl artwork, `nexer-reference.pptx` -- is committed. You only need the
originals to re-run the build scripts; put them back under `temp/` if so.

## Starting a deck

Copy the kit, or work inside it:

```bash
cp template.qmd my-deck.qmd
quarto render my-deck.qmd
```

Front matter is two lines, because the extension carries the rest:

```yaml
format:
  nexer-revealjs: default
  nexer-pptx: default
```

### Rendering a deck from a subfolder

Keep a client deck in its own folder (`<client>/deck.qmd`); the project renders
every `.qmd` under it. Two things change:

- Paths in the source are **deck-relative**: `../assets/swirl-dark.jpg`,
  `source("../R/nexer-ggplot.R")`.
- Quarto roots the revealjs logo at the *project* directory for any document in a
  subfolder, so `_brand.yml`'s logo is emitted as `/assets/nexer-logo.png` and
  vanishes when the HTML is opened from disk. Repoint it in the deck's own front
  matter, which leaves the kit untouched:

```yaml
format:
  nexer-revealjs:
    include-in-header:
      - text: |
          <style>
          .reveal .slide-logo { content: url("../assets/nexer-logo.png"); }
          </style>
```

A document-level `include-in-header` adds to the extension's rather than
replacing it, so the Google Fonts link survives. A file whose name starts with
`_` is excluded from the Quarto project and will not find the extension at all.

`template.qmd` is a working gallery of every archetype — title slide,
section divider, statement, kicker + action title with a chart, stat row,
takeaway box, options table, bridge chart, appendix. Delete what you do not
need rather than writing from scratch.

## The palette, and when to reach for each

| Token | Hex | Use |
|---|---|---|
| `--brand-purple` | `#5A1F9F` | The Nexer colour. Kickers, links, primary chart series, section fills. |
| `--brand-purple-light` | `#AA4BF4` | Hover, secondary emphasis, accents on dark backgrounds. |
| `--brand-orange` | `#FF5028` | **Highlight only.** The one thing you want looked at. Never a second theme colour. |
| `--brand-orange-light` | `#FF875A` | A softer second highlight when orange is already spent. |
| `--brand-blue-pale` | `#D9E6F0` | Chips, quiet fills. |
| `--brand-grey` / `--brand-grey-pale` | `#C8C8C8` / `#F0F0F0` | Everything that is not the point: comparison series, table headers, rules. |

The discipline that makes charts read: **one series in purple, everything else
grey, orange reserved for the single fact the slide exists to deliver.**

`_brand.yml` is the source of truth. Editing a palette entry there
recolours the deck — the stylesheet consumes the values as CSS custom
properties, so no SCSS edit is needed.

## Light body, dark punctuation

Content slides are white with black text, because charts and tables are
unreadable on black. Reach for dark deliberately:

```markdown
# Section name {background-image="assets/swirl-dark.jpg" background-color="#000000"}

## Context {background-color="#5A1F9F"}
### One sentence, no evidence
```

The swirl artwork (`assets/swirl-dark.jpg`, `assets/swirl-light.jpg`) comes from
the corporate deck and keeps its left ~60% clear, which is where text goes.

## Components the stylesheet provides

```markdown
::: {.stats}
::: {.stat}
[2 450]{.figure} [Employees]{.label}
:::
:::

::: {.takeaway}
The bold lead-in that states the point.
:::

::: {.units}
€ millions, annualised
:::

::: {.source}
[Note:]{.label} Method caveat. &nbsp; [Source:]{.label} Where it came from
:::

[Non-legislative]{.chip}   [Highlight]{.chip .accent}
```

## Typography

Headings are **Bw Gradual**, body is **FK Grotesk** — the real Nexer faces. They
are commercial, so nothing is redistributed; they are named first in the font
stack and resolve natively on machines that have them installed (Nexer laptops
do). **Outfit** and **Inter** load from Google Fonts as the fallback everywhere
else. The stylesheet link is in `_extensions/nexer/_extension.yml` —
Quarto's `_brand.yml` sets font *names* but does not fetch `source: google`
files for revealjs, so the link is explicit.

For charts, `R/nexer-ggplot.R` provides `theme_nexer()`, the palette, and
`nexer_span()` for colouring a subtitle so it acts as the legend. Call
`nexer_use_fonts()` in the setup chunk — R cannot draw with a font it has not
registered, and without it you get one warning per label.

## Logo rules

From the co-branding guidelines (`temp/Co-Branding Nexer.pdf`):

- Clear space around the logotype equals **1× the logotype's height**, all sides.
- A partner logo **must not be taller than Nexer's** when horizontal.
- **Nexer's logotype goes in the right corner.** The template already places it
  bottom-right; do not move it.

`assets/nexer-logo.png` is black (light slides), `assets/nexer-logo-white.png`
is white (dark slides).

## Exporting to PowerPoint

`_brand.yml` does **not** apply to pptx — Quarto supports it for html, revealjs,
dashboard and typst only. PowerPoint is styled by a reference doc built from the
real Nexer deck. Both are wired into the extension, so declare both formats and
render:

```yaml
format:
  nexer-revealjs: default
  nexer-pptx: default
```

```bash
quarto render my-deck.qmd                                  # both
python tools/check_pptx.py my-deck.pptx                    # what layouts were used
powershell -File tools/shoot_pptx.ps1 -Deck my-deck.pptx   # export PNGs and look
```

### How the two-tier title maps to PowerPoint

PowerPoint has one title placeholder, so `pptx-titles.lua` promotes the `###`
action title into it and drops the `##` kicker. That is also better PowerPoint
design — the title should carry the takeaway, not the section label.

This is not cosmetic. Leaving the `###` in the body makes pandoc read the slide
as "text then content" and **split any following columns block onto a second,
untitled slide**. The filter is what keeps the pptx slide count equal to the
HTML deck's.

### What does not survive the trip to PowerPoint

Say this up front rather than letting it be discovered in a meeting:

- `.fragment` / `.incremental` reveals — everything appears at once.
- `background-color` / `background-image` on slides — layout backgrounds only.
- Raw ```` ```{=html} ```` blocks — dropped entirely.
- `.button` links, `.chip`, `.stats` and `.takeaway` styling — these are CSS,
  and pptx has no stylesheet. The text survives; the styling does not.
- `.units` and `.source` move to the **speaker notes**, prefixed `[units]` and
  `[source]`. Pandoc cannot place any block after a figure or table on the same
  slide, so leaving them on the face would spawn a stray slide.

- `.chip` rows collapse into a run-on line, because the pill borders were the
  separator. Join chips with ` · ` so the row still reads as a list in pptx.
- A **table inside a `.column` overflows the slide**. The placeholder is half the
  width, every cell wraps, and the rows run off the bottom with no warning. Use a
  numbered or bulleted list for step-by-step content and keep tables full width,
  at six rows or fewer. Screenshot the pptx; this failure is invisible in HTML.
- Any block **before** a `.columns` block (a `.stats` row, a `.takeaway`) makes
  pandoc split the slide in two, the second one untitled. Check the slide count
  with `tools/check_pptx.py` after adding one.

A further pandoc constraint worth knowing: **nothing can follow a figure or
table on a slide**. If you need a caption under an exhibit in PowerPoint, put it
in the column beside it.

### Rebuilding the reference template

Only needed if the corporate deck changes:

```bash
python tools/build_reference_pptx.py --verify
```

`--verify` checks pandoc's layout contract, placeholder geometry and idx
hygiene, that every relationship target resolves, and the part counts pandoc's
own globbing depends on. If it passes but PowerPoint still complains, render
`tests/reference-smoke.qmd` and open the result — that exercises all seven
layouts.

## Related skills

`jonathan-slides` is the structure — two-tier titles, evidence over prose, notes
as narration. `mckinsey-slides` is the rigour — action-title grammar, sourcing,
chart conventions. This skill is the skin.
