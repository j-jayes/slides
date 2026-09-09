# Nexer slide kit

A Quarto Reveal.js template that renders one `.qmd` to branded HTML and to
editable PowerPoint, and the Claude Code skills for writing the deck that goes
in it.

```bash
cp template.qmd my-deck.qmd
quarto render my-deck.qmd                     # both formats
quarto render my-deck.qmd --to nexer-revealjs # HTML only
quarto render my-deck.qmd --to nexer-pptx     # PowerPoint only
```

Front matter is two lines:

```yaml
format:
  nexer-revealjs: default
  nexer-pptx: default
```

Add `export-pdf: true` alongside them and every render also prints a PDF.

`template.qmd` is a working gallery of every slide archetype. Delete what you do
not need rather than starting from a blank file.

## Getting the kit

Four ways in, because the deck kit and the skills install by different routes.
Pick by what you are doing.

| I want | Do this |
|---|---|
| A new repo for a deck | GitHub **Use this template**. You get everything, skills and agent config included. |
| The kit inside an existing repo | `quarto use template j-jayes/slides` and name the directory `slides` |
| Only the two formats | `quarto add j-jayes/slides` |
| The skills, in every project | `claude plugin marketplace add j-jayes/slides` then `claude plugin install slides@j-jayes` |

Two things about the middle routes worth knowing before you are surprised by
them:

- `quarto use template` copies every non-hidden file except `README.md` and
  `LICENSE`, and installs `_extensions/` properly. `template.qmd` is renamed to
  match the directory you name. It does **not** copy `.gitignore`, `.claude/` or
  anything else beginning with a dot, and Quarto 1.9+ also skips `CLAUDE.md`.
  Those travel only via the GitHub template.
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
| `_brand.yml` | Nexer colours, logo and type roles. **The source of truth** — editing a palette entry recolours the deck. |
| `_extensions/nexer/` | Both formats: `_extension.yml`, `nexer.scss`, `pptx-titles.lua`, and `nexer-reference.pptx`. |
| `assets/` | Logo (black and white), favicon, swirl backgrounds. |
| `R/nexer-ggplot.R` | `theme_nexer()`, the chart palette, and `nexer_span()` for coloured-subtitle legends. |
| `tools/` | Build and verification scripts (below). |
| `tests/reference-smoke.qmd` | Exercises all seven pandoc layouts. |
| `skills/` | The Claude Code skills, shipped as the `slides` plugin. |
| `.claude-plugin/` | Plugin and marketplace manifests. This repo is its own single-plugin marketplace. |

## The one authoring rule

`##` is the **kicker** (where am I), `###` is the **action title** (what should I
conclude). The stylesheet sizes them accordingly.

```markdown
## Market context

### Adoption has grown for three years but the gap to peers is widening
```

Nested fenced divs need **more colons on the outer div** — 5 for `.columns`, 4
for `.column`, 3 for anything inside. Get this wrong and columns silently stack.

## Tools

```bash
python tools/extract_assets.py                    # re-extract logo/swirls from the corporate deck
python tools/build_reference_pptx.py --verify     # rebuild + validate nexer-reference.pptx
python tools/shoot_slides.py my-deck.html --all   # screenshot every HTML slide
python tools/check_pptx.py my-deck.pptx           # assert pptx slides bound to the right layouts
python tools/export_pdf.py my-deck.html           # print the deck to PDF via headless Chrome
powershell -File tools/shoot_pptx.ps1 -Deck my-deck.pptx   # export pptx slides to PNG
```

`shoot_pptx.ps1` doubles as the corruption test: a malformed package makes
PowerPoint raise a repair prompt and the COM open fails.

`export_pdf.py` also runs as a post-render hook, so a deck carrying
`export-pdf: true` gets a PDF beside its HTML on every render. Quarto has no PDF
output for revealjs -- the documented route is opening the deck with `?print-pdf`
and working Chrome's print dialog by hand -- so the script drives Chrome headless
instead and checks the page count against the deck, because the failure mode is a
silent one-page blank rather than an error.

## Skills

Ten skills ship in the plugin. Three are about decks:

| Skill | What it covers |
|---|---|
| `jonathan-slides` | Structure — two-tier titles, evidence over prose, notes as narration. |
| `nexer-slides` | Branding and export — palette, logo rules, what survives the trip to PowerPoint. |
| `mckinsey-slides` | Rigour — action-title grammar, the ghost deck, sourcing and chart conventions. |

The other seven are general engineering practice: `tdd`, `manual-testing`,
`first-run-the-tests`, `git-discipline`, `walkthrough`, `subagent-fanout` and
`data-dict`. `CLAUDE.md` carries the standing engineering standards; it is not
part of the plugin, so copy it or point at it from your own.

## Provenance

The source material below is **not kept in this repo** — the corporate deck
alone is ~90 MB and nothing at render time needs it. Everything derived from it
is committed. To re-run the build scripts, put the originals back under `temp/`.

Colours, fonts, logo and swirl artwork all come from
`temp/Sales presentation 2026.pptx` (theme scheme "Nexer colors" / "Nexer
fonts"). Logo clear-space and co-branding rules come from
`temp/Co-Branding Nexer.pdf`. Nothing is invented.

Bw Gradual and FK Grotesk are commercial and are not redistributed here — they
are named first in the font stack and resolve on machines that have them
installed; Outfit and Inter load from Google Fonts as the fallback.
