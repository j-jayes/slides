---
name: mckinsey-slides
description: >-
  Apply McKinsey slide standards — action-title grammar, the ghost deck,
  sourcing and chart conventions — to a Quarto Reveal.js deck. Use when asked
  for "McKinsey-style" or "consulting-style" slides, for an executive or client
  deck, or when reviewing whether a deck's argument actually holds together.
---

# McKinsey-style slides

Everything here is read off two real documents, both in `temp-mckinsey/`:

- **`McKinsey-USPS-Future-Business-Model-.pdf`** (2010, 39 slides) — a genuine
  McKinsey client deck. The primary source for slide grammar.
- **`future-of-trash-april-2023.pdf`** (2023, 94 pages) — a client-branded
  report built with McKinsey support. The source for report-shaped work.

The PDFs themselves are **not kept in this repo**. You should not normally need
them — the corpora below carry the evidence, quoted verbatim.

Detailed corpora, with verbatim titles, source lines, callouts and chart
conventions, are in [reference/usps-deck-anatomy.md](reference/usps-deck-anatomy.md)
and [reference/nyc-trash-report-anatomy.md](reference/nyc-trash-report-anatomy.md).
**Read the relevant one before drafting** — quoting the real corpus beats
paraphrasing house style from memory.

## 1. The action title

One sentence stating the conclusion. **14–20 words** in the USPS deck, median 17.
No terminal punctuation. Sentence case — only proper nouns and defined case names
capitalise. It wraps to exactly two lines, broken at a clause boundary.

> **Anti-pattern**: `Revenue Growth 2023`
>
> **Real**: `Retiree Health Benefit funding requirements are a significant burden, equal to 12% of total revenue in 2010`

**Tense is keyed to the section**, and this is worth being deliberate about:

| Section | Tense | Example |
|---|---|---|
| Diagnosis | present perfect | `Losses have been driven by volume declines, RHB pre-funding requirements and limitations on cost savings` |
| Forecast | `will` | `Volume will decline significantly over the next decade driven by a steady decline in First-Class Mail` |
| Recommendation | `can` / `will need to` | `USPS will need to pursue multiple "Fundamental Change" options to close the remaining gap` |

About 35% of titles carry a number, and the number is always the payload.

**Two constructions to reach for:**

- **Concession, then punch** — `Recent reductions in workforce usage have been significant, **but** pieces per FTE still declined in 2009`
- **Front-loaded conditioner** — `**Without aggressive management cost-cutting,** work hours will remain flat…`

Topic-label titles (`Pricing opportunities for USPS`) appear **only in the
reference annex**, never in the argument.

## 2. The ghost deck — write titles first

Read the titles alone, in order. They must tell the whole argument with no
slides attached. This is the test that catches a broken deck before any chart
gets built.

The USPS deck's spine: slide 2 asserts, slide 3 decomposes it into exactly three
drivers, slides 4–8 prove each in turn. The numbers carry across titles —
`-$33B / $238B` → `-$15B / $115B` → `remaining gap`.

Two rules that follow:

- **Announce, then deliver.** A title saying `Four trends will affect postal
  economics going forward` is followed by exactly four slides. If you promise a
  number, honour it.
- **Repeat the frame, change the delta.** Build slides reuse the identical layout
  with new data so the reader compares instead of re-learning. The USPS deck
  re-words a callout by a single word to mark the change: `…will be reached in
  Oct 2010` becomes `…**still** reached in Oct 2010`.

## 3. Slide anatomy

- **Kicker**, top-left: `Section` or `Section: Sub-scope` — `Base Case: Volume
  Declines`, `Fundamental Change: Pricing`. In the Nexer template this is the
  `##` heading; the action title is the `###`.
- **Chip**, top-right: a repeated taxonomy or a chart legend.
- **Body**: chart-left / narrative-right at ~60:40, each column with its own
  noun-phrase header — `Net profit/loss` … `Key drivers`.
- **Bottom rail**, fixed order: `Note:` → numbered footnotes → `SOURCE:`.

Source lines are the literal uppercase token, semicolon-separated, no period:

```
SOURCE: USPS 2009 10-K; USPS 2010 Budget
SOURCE: BCG; Global Insights; USPS Financial Forecast Model
```

## 4. Chart conventions

**Chart title on line 1, a bare lowercase units line on line 2.** Always.

```
Net profit/loss              →  $ billions
Pieces per FTE               →  Pieces per year, thousands
Average daily waste weight   →  pounds, thousands
```

The index base lives in the unit line, not the title: `Cumulative increase from
1973, percent`.

- `~` is the hedge — `~$10 billion`, `~150 million delivery points`.
- **Ranges, not points**, for uncertain forecasts.
- Split projections with a divider labelled `Actual | Forecast`.
- CAGR annotated on the line: `+2.2% p.a.¹`.
- **Footnotes disclose method**, they are not asides: `Revenue declines
  calculating by applying 2009 prices against 2006-09 volume declines`.
- **Always print the base with a percentage**: `89% of New York City streets with
  residential properties`, never a bare `89%`.
- **Print the threshold definition** so the claim is auditable: `"Viable" defined
  as containers would take up <25% of available street length.`

**Minimalism**: no 3D, no heavy gridlines, no redundant legend. Colour the
subtitle instead of drawing a legend, so the reader decodes the colour and reads
the insight in one pass — the Nexer kit's `R/nexer-ggplot.R` provides
`nexer_span()` and `theme_nexer()` for exactly this.

## 5. Callouts

**Every callout carries a number or a named threshold.** Never a generic label.

```
55% of reductions have come from non-career and overtime
Statutory debt ceiling of $15 B will be reached in Oct 2010
Even if volumes remained flat instead of declining by 1.5% annually,
the loss in 2020 would still be $21 billion
```

That last one is a **stress-test callout** — the pre-emptive answer to the
obvious objection. Worth building one into any deck that forecasts.

## 6. Chart archetypes — what the evidence actually supports

Present in the sources, with what each is for:

| Archetype | Job |
|---|---|
| Waterfall / bridge | Where a number comes from. Label start, end and every step. |
| Sizing build-up | Stack the levers, total them, then drill into each and restate its subtotal. |
| Options taxonomy | Columns of coded options (`R1 R2 P1 P2 S1…`). Screen them; you need not score them. |
| Screening funnel | Inputs → longlist → rejects, with the reject criteria printed. |
| Upside / downside pair | Two columns, risks nested as sub-bullets. |
| Conceptual 2×2 with a centre insight box | Every quadrant header carries a parenthetical scale figure. |
| Big-number KPI row | 3–5 figures, each with its base named. |
| Benchmark table | Sorted so the subject's position is the point. |
| 2×N roadmap grid | `Immediate next steps` \| `Future vision` × audience segment. |

**Not in either source** — do not present these as McKinsey house style:
Marimekko, scored impact/feasibility 2×2 bubble matrices, Gantt charts, scatter
plots, S-curves. (An earlier version of this skill recommended Marimekko and
Gantt from memory; the documents do not support it.)

## 7. Report-shaped work

When the deliverable is a document rather than a presentation, the NYC report
shows the variant: a **noun-phrase page title** (the locator) plus a **bold
takeaway lead-in** (the message), with `, cont.` for continuation pages instead
of renumbering. Title families create navigability — `Complicating Factor – X`,
`Viability – X`, `Case Study: X`.

Its most memorable device is the **scale analogy**: `44 MILLION pounds of waste
every day … Equal to the weight of 140 Statues of Liberty!` One of these per
deck earns its place.

Define the unit of analysis once and never vary it — `street section` appears 97
times in that report.

## 8. Execution

Use the Nexer Quarto kit — see the `nexer-slides` skill
for branding and the `jonathan-slides` skill for deck structure. The template's
`##` / `###` split already implements the kicker + action-title convention, and
`.takeaway`, `.units` and `.source` implement the lead-in, unit line and bottom
rail.

## A note on the video

`temp-mckinsey/youtube.txt` points at *Build your own "McKinsey Style"
Presentation (Full Tutorial)* (Analyst Academy, 5 Jan 2024, 10:53). **Its
transcript could not be retrieved** — YouTube blocks caption fetching. What is
recoverable is the creator's own written prompt, which states the horizontal-logic
rule directly and is worth keeping:

> "make sure each is a complete sentence that reads like a normal sentence such
> that if you read them altogether it would sound like a cohesive story."

Its taught workflow is Plan → Create → Research → Design → Finalize. The design
and colour guidance in the video is unrecovered; if someone pastes the transcript
into `temp-mckinsey/youtube.txt`, fold it in. Do not attribute anything else to
that video.
