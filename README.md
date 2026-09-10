# Nexer slide kit

A Quarto Reveal.js template that renders one `.qmd` to branded HTML and to
editable PowerPoint, publishes the HTML as a GitHub Pages site with a listing
page, and the Claude Code skills for writing the deck that goes in it.

```bash
cd slides
cp template.qmd my-deck.qmd
quarto render                       # every deck, both formats
quarto render my-deck.qmd           # just this one
quarto preview                      # live reload while you write
```

Front matter is two lines:

```yaml
format:
  nexer-revealjs: default
  nexer-pptx: default
```

Add `export-pdf: true` alongside them and every render also prints a PDF.

`slides/template.qmd` is a working gallery of every slide archetype. Delete
what you do not need rather than starting from a blank file.

## Where things land

The Quarto project lives in `slides/`, so the kit drops into a
cookiecutter-data-science repo without taking over the root. One render fills
two directories:

| Path | What it is |
|---|---|
| `slides/` | The project. Decks, `_brand.yml`, `_extensions/`, `assets/`, `R/`, `tools/`, `tests/`. |
| `slides/index.qmd` | The listing page. Every deck gets a card; give each one a `description:` and, if you want a thumbnail, an `image:`. |
| `docs/` | The rendered site. **Committed** — point GitHub Pages at it. |
| `reports/` | The `.pptx` (and any `.pdf`). What you send people. Not committed. |
| `slides/_site/` | Quarto's own output, which the two above are copied out of. Ignored. |

To publish: **Settings → Pages → Deploy from a branch → `main` / `docs`**, then
commit `docs/` after a render. `tools/publish.py` writes the `.nojekyll` that
stops GitHub running Jekyll over the output.

Publishing never deletes, so a `docs/` holding a `CNAME` or hand-written pages
is safe. The cost is that renaming a deck leaves its old page behind: delete
`docs/` and re-render to clear it.

## What PowerPoint gets

The pptx is not a flattened copy of the HTML. `pptx-nexer.lua` rebuilds the
branded components as native shapes, so a colleague can retype a figure or drag
a box:

| In the source | In PowerPoint |
|---|---|
| `## Kicker` + `### Action title` | Small purple locator over a hairline rule, action title in the title placeholder |
| `::: {.stats}` | One text box per figure, spread across the slide |
| `::: {.takeaway}` | Grey panel with an orange bar |
| `::: {.source}` / `::: {.units}` | One 9pt rail bottom-left, units first |
| `[text]{.chip}` | Highlighted small-caps run, orange for `.accent` |
| `#### Subhead` | Purple small-caps |
| `{background-color="#5A1F9F"}` | A real coloured slide background |

Three placement rules follow from how pandoc lays out a pptx slide, and the
`nexer-slides` skill spells them out: a stat row goes at the top of the slide
with nothing but a takeaway after it; a takeaway sits in a fixed band at the
bottom of its column, so keep the text above it short; and a stat row cannot
share a slide with `.columns`.

## Getting the kit

Four ways in, because the deck kit and the skills install by different routes.
Pick by what you are doing.

| I want | Do this |
|---|---|
| A new repo for a deck | GitHub **Use this template**. You get everything, agent config included. |
| The kit inside an existing repo | `quarto use template j-jayes/slides` from the repo root, answering **no** to the subdirectory prompt |
| Only the two formats | `quarto add j-jayes/slides` |
| The skills, in every project | `claude plugin marketplace add j-jayes/slides` then `claude plugin install slides@j-jayes` |

Two things about the middle routes worth knowing before you are surprised by
them:

- `quarto use template` already puts the project in `slides/`, which is why you
  answer no when it offers to make a subdirectory — say yes and you get
  `slides/slides/`. It copies neither `docs/`, `reports/`, `slides/tests/` nor
  `skills/`, and never copies top-level dotfiles, so `.gitignore` and
  `.claude/` travel only via the GitHub template. `template.qmd` keeps its name
  (Quarto only auto-renames one at the repo root).
- `quarto add` installs `_extensions/nexer/` and nothing else — so you get the
  two formats but not `_brand.yml`, `assets/` or `R/`. The formats reference
  `brand`, so a deck built this way needs a `_brand.yml` of its own. Use
  `quarto use template` if you want the whole kit.

Once the plugin is installed the skills are available in every project, invoked
as `/slides:nexer-slides` or triggered automatically by what you ask for.
`claude plugin marketplace update j-jayes` pulls the latest.

## What is here

| Path | What it is |
|---|---|
| `slides/_brand.yml` | Nexer colours, logo and type roles. **The source of truth** — editing a palette entry recolours the deck. |
| `slides/_extensions/nexer/` | Both formats: `_extension.yml`, `nexer.scss`, `pptx-nexer.lua`, `bg/` and `nexer-reference.pptx`. |
| `slides/assets/` | Logo (black and white), favicon, swirl backgrounds. |
| `slides/R/nexer-ggplot.R` | `theme_nexer()`, the chart palette, and `nexer_span()` for coloured-subtitle legends. |
| `slides/tools/` | Build, publish and verification scripts (below). |
| `slides/tests/` | The layout and component regressions. |
| `skills/` | The Claude Code skills, shipped as the `slides` plugin. |
| `.claude-plugin/` | Plugin and marketplace manifests. This repo is its own single-plugin marketplace. |

## The one authoring rule

`##` is the **kicker** (where am I), `###` is the **action title** (what should
I conclude). Both formats size them accordingly.

```markdown
## Market context

### Adoption has grown for three years but the gap to peers is widening
```

Nested fenced divs need **more colons on the outer div** — 5 for `.columns`, 4
for `.column`, 3 for anything inside. Get this wrong and columns silently stack.

## Tools

All paths relative to `slides/`.

```bash
python -m unittest discover -s tests               # the whole suite
python tools/build_bg_pngs.py                      # rebuild the background tiles from _brand.yml
python tools/build_reference_pptx.py --verify      # rebuild + validate nexer-reference.pptx
python tools/extract_assets.py                     # re-extract logo/swirls from the corporate deck
python tools/check_pptx.py ../reports/my-deck.pptx # which layout each pptx slide landed on
python tools/shoot_slides.py _site/my-deck.html --all       # screenshot every HTML slide
powershell -File tools/shoot_pptx.ps1 -Deck ../reports/my-deck.pptx   # export pptx slides to PNG
python tools/export_pdf.py _site/my-deck.html      # print the deck to PDF via headless Chrome
```

`shoot_pptx.ps1` doubles as the corruption test: a malformed package makes
PowerPoint raise a repair prompt and the COM open fails. It attaches to a
running PowerPoint rather than starting and quitting one, so it will not close
the decks you have open.

`export_pdf.py` and `publish.py` both run as project post-render hooks, so a
deck carrying `export-pdf: true` gets a PDF on every render. Quarto has no PDF
output for revealjs — the documented route is opening the deck with `?print-pdf`
and working Chrome's print dialog by hand — so the script drives Chrome headless
instead and checks the page count against the deck, because the failure mode is
a silent one-page blank rather than an error.

## Skills

Ten skills ship in the plugin. Three are about decks:

| Skill | What it covers |
|---|---|
| `jonathan-slides` | Structure — two-tier titles, evidence over prose, notes as narration. |
| `nexer-slides` | Branding and export — palette, logo rules, what PowerPoint does with each component. |
| `mckinsey-slides` | Rigour — action-title grammar, the ghost deck, sourcing and chart conventions. |

The other seven are general engineering practice: `tdd`, `manual-testing`,
`first-run-the-tests`, `git-discipline`, `walkthrough`, `subagent-fanout` and
`data-dict`. `CLAUDE.md` carries the standing engineering standards; it is not
part of the plugin, so copy it or point at it from your own.

## Provenance

The source material below is **not kept in this repo** — the corporate deck
alone is ~90 MB and nothing at render time needs it. Everything derived from it
is committed. To re-run the build scripts, put the originals back under
`slides/temp/`.

Colours, fonts, logo and swirl artwork all come from
`slides/temp/Sales presentation 2026.pptx` (theme scheme "Nexer colors" / "Nexer
fonts"). Logo clear-space and co-branding rules come from
`slides/temp/Co-Branding Nexer.pdf`. Nothing is invented.

Bw Gradual and FK Grotesk are commercial and are not redistributed here — they
are named first in the font stack and resolve on machines that have them
installed; Outfit and Inter load from Google Fonts as the fallback.
