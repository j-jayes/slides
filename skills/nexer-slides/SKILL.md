---
name: nexer-slides
description: >-
  Start, style and export a Nexer Insight branded presentation using the Quarto
  Reveal.js slide kit — correct colours, logo, typography, and PowerPoint
  export via the Nexer reference template. Use when a deck is for Nexer, a Nexer
  client, or when asked to "brand this deck" or "export to PowerPoint".
---

# Nexer-branded slides

The kit is the `slides/` directory: the Quarto project holding
`_extensions/nexer/`. **Every path below is relative to it**, so `cd slides`
first. If the repo has no kit yet, create one from its root:

```bash
quarto use template j-jayes/slides    # answer NO to "create a subdirectory"
```

It already contains the `slides/` folder, so saying yes gives you
`slides/slides/`.

One source `.qmd` renders to Reveal.js HTML and to editable PowerPoint, both on
brand. A render fills two directories: `../docs/` gets the website (a listing
page plus the decks, committed, served by GitHub Pages) and `../reports/` gets
the `.pptx` and any `.pdf` — the files you send people.

Every colour and font role here is lifted from the real corporate deck
(`slides/temp/Sales presentation 2026.pptx` → `ppt/theme/theme1.xml`, colour scheme
"Nexer colors", font scheme "Nexer fonts"). Nothing is invented.

That deck and the co-branding PDF are **not kept in this repo** (~90 MB, and
nothing at render time needs them). Everything extracted from them -- palette,
logo, swirl artwork, `nexer-reference.pptx` -- is committed. You only need the
originals to re-run the build scripts; put them back under `slides/temp/` if
so.

## Starting a deck

Copy the template, or work inside it:

```bash
cd slides
cp template.qmd my-deck.qmd
quarto render my-deck.qmd     # or bare `quarto render` for every deck
```

Give the deck a `description:` in its front matter: that is the text on its card
on the listing page. An `image:` is optional -- without one the card falls back
to the swirl artwork.

Front matter is two lines, because the extension carries the rest:

```yaml
format:
  nexer-revealjs: default
  nexer-pptx: default
```

### Rendering a deck from a subfolder

Decks normally sit flat in `slides/`. You can keep one in its own folder
(`<client>/deck.qmd`) instead; the project renders every `.qmd` under `slides/`.
Two things change:

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
else. The stylesheet link is in `_extensions/nexer/_extension.yml` (pptx uses
the real faces from the reference doc's theme, so it needs no such link) —
Quarto's `_brand.yml` sets font *names* but does not fetch `source: google`
files for revealjs, so the link is explicit.

For charts, `R/nexer-ggplot.R` provides `theme_nexer()`, the palette, and
`nexer_span()` for colouring a subtitle so it acts as the legend. Call
`nexer_use_fonts()` in the setup chunk — R cannot draw with a font it has not
registered, and without it you get one warning per label.

## Logo rules

From the co-branding guidelines (`slides/temp/Co-Branding Nexer.pdf`):

- Clear space around the logotype equals **1× the logotype's height**, all sides.
- A partner logo **must not be taller than Nexer's** when horizontal.
- **Nexer's logotype goes in the right corner.** The template already places it
  bottom-right; do not move it.

`assets/nexer-logo.png` is black (light slides), `assets/nexer-logo-white.png`
is white (dark slides).

## Exporting to PowerPoint

`_brand.yml` does **not** apply to pptx — Quarto supports it for html, revealjs,
dashboard and typst only. PowerPoint gets its type and palette from a reference
doc built from the real Nexer deck, and its components from `pptx-nexer.lua`.
Both are wired into the extension, so declare both formats and render:

```yaml
format:
  nexer-revealjs: default
  nexer-pptx: default
```

```bash
quarto render my-deck.qmd                                            # both
python tools/check_pptx.py ../reports/my-deck.pptx                   # what layouts were used
powershell -File tools/shoot_pptx.ps1 -Deck ../reports/my-deck.pptx  # export PNGs and look
```

The HTML lands in `../docs/`, the PowerPoint in `../reports/`. **Look at the
pptx before you send it.** The `shoot_pptx.ps1` COM open doubles as the
corruption test, and it attaches to a running PowerPoint rather than quitting
one, so it is safe to run with decks open.

### What PowerPoint builds natively

These are real shapes, not a picture of the HTML, so a colleague can retype a
figure or drag a box:

| Source | PowerPoint |
|---|---|
| `## Kicker` + `### Action title` | Purple locator over a hairline rule; action title in the title placeholder |
| `::: {.stats}` | One text box per figure, spread across the slide |
| `::: {.takeaway}` | Grey panel with an orange bar |
| `::: {.source}` and `::: {.units}` | One 9pt rail bottom-left, units first |
| `[text]{.chip}` | Highlighted small-caps run; orange for `.chip .accent` |
| `#### Subhead` | Purple small-caps |
| `{background-color="#5A1F9F"}` | A real coloured slide background |

PowerPoint has one title placeholder, so the filter promotes the `###` into it
and demotes the `##` to the locator shape. That is not cosmetic: leaving the
`###` in the body makes pandoc read the slide as "text then content" and **split
any following columns block onto a second, untitled slide**.

### Placement rules the filter cannot bend

Every shape above is absolutely positioned, because pandoc gives raw OpenXML no
layout. Nothing reflows, so composition is on you:

- **A `.stats` row goes at the top of the slide**, with nothing after it but a
  `.takeaway`. Any other body text is drawn underneath it.
- **A `.takeaway` sits in a fixed band at the bottom** of the slide or of its
  column. Keep the text above it to about ten lines full width, or five
  two-line bullets in a column, or they collide.
- **A `.stats` row cannot share a slide with `.columns`** — pandoc splits the
  slide at the columns block.
- **Only palette colours have a background tile.** `background-color` works by
  swapping in a PNG from `_extensions/nexer/bg/`; an off-palette hex warns and
  is dropped. Add one with `python tools/build_bg_pngs.py` after editing
  `_brand.yml`.

### What still does not survive

Say this up front rather than letting it be discovered in a meeting:

- `.fragment` / `.incremental` reveals — everything appears at once.
- Raw ```` ```{=html} ```` blocks — dropped entirely.
- A **dark `background-color` slide keeps the master's black logo.** The layout
  carrying the white one cannot be selected from markdown, at any pandoc
  version. Use dark statement slides sparingly in a deck destined for
  PowerPoint, or accept it.
- Image `width`/`height` — pandoc scales every image to fit its placeholder and
  ignores the attributes. Control the aspect ratio instead.
- Only the **first two** `.column` divs are used; a third is dropped.
- A **table inside a `.column` overflows the slide**. The placeholder is half the
  width, every cell wraps, and the rows run off the bottom with no warning. Use a
  numbered or bulleted list for step-by-step content and keep tables full width,
  at six rows or fewer. Screenshot the pptx; this failure is invisible in HTML.

### Rebuilding the reference template

Only needed if the corporate deck changes:

```bash
python tools/build_reference_pptx.py --verify
```

`--verify` checks pandoc's layout contract, placeholder geometry and idx
hygiene, that the theme's hyperlink colour is visible on the light master, that
every relationship target resolves, and the part counts pandoc's own globbing
depends on. If it passes but PowerPoint still complains, run the regressions:

```bash
python -m unittest discover -s tests
```

`tests/reference-smoke.qmd` exercises all seven pandoc layouts;
`tests/pptx-components.qmd` exercises every component above, and
`test_pptx_components.py` asserts the slide count, the layout of each slide, the
shapes present by name, and that the raw XML parses.

## Related skills

`jonathan-slides` is the structure — two-tier titles, evidence over prose, notes
as narration. `mckinsey-slides` is the rigour — action-title grammar, sourcing,
chart conventions. This skill is the skin.
