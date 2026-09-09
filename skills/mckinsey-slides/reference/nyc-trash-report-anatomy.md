# The Future of Trash — report anatomy

Source: `temp-mckinsey/future-of-trash-april-2023.pdf`, April 2023, 94 pages.

**Framing correction worth keeping straight**: this is *not* a McKinsey-branded
"Exhibit N" report. It is a client-branded (NYC Department of Sanitation)
document built with McKinsey support — the acknowledgements say *"This report
relied on significant support from the New York City Department of
Transportation and McKinsey & Company."* So it shows the **McKinsey-built
government report deck** archetype: one exhibit per page, no exhibit numbering,
and the action title split into a noun-phrase page title plus a bold takeaway
lead-in.

## 1. The two-tier title system

Every content page has:

- **Tier 1 — page title**: 2–9 words, noun phrase, no verb in ~85%, no number in
  ~95%. This is the *locator*, the functional equivalent of "Exhibit 3".
- **Tier 2 — the takeaway**: a bold lead-in sentence below the title, in the body
  area. This is where the "so what" lives.

Continuation pages append a literal `, cont.` to the identical title — used 26
times. This replaces renumbering.

### Productive title families — what makes a 94-page deck navigable

```
Complicating Factor – Population Density
Complicating Factor – Built Environment
Complicating Factor – Weather
Complicating Factor – Curb Space
Complicating Factor – Collection Frequency
Complicating Factor – Container Model and Fleet

Viability – Overview
Viability – Street Sections That Require No Changes To Collection Frequency
Viability – Street Sections That Require Doubled Collection Frequency
Viability – Commercial Corridors

Case Study: Amsterdam    Case Study: Barcelona    Case Study: Paris
```

Question titles are used sparingly, for framing pages only: `What is
Containerization?`, `Why Containerization Matters`, `Is Containerization Viable
in New York City?`

## 2. Takeaway sentences, verbatim

> "Containerization is not a one-size-fits-all solution to New York City's current trash problem."

> "DSNY determined through careful analysis that containerization is viable citywide for 89% of New York City streets with residential properties, comprising 77% of the City's total residential waste output."

> "All 89% of residential street sections can be containerized by eliminating up to 10% of current parking spaces citywide."

> "Wheeled shared containers are not a reliable, scalable solution for New York City. However, they are compatible with current fleet and present an opportunity to meaningfully pilot shared containerization."

> "A scalable, viable truck for shared container collection in New York City does not currently exist in the United States."

> "Accordingly, DSNY must work with industry to develop a first-of-its-kind ASL collection truck for stationary shared containers in the United States. This would take at least three years and significant capital investment."

> "The optimal containerization model doesn't just vary neighborhood-to-neighborhood, but street section to street section."

> "No major city assessed in this study uses wheeled shared containers as their primary, or even secondary, containerization model."

> "Trash must go somewhere."

> "Snow adds operational complexity to trash collection."

### Grammar

- **Simple present** dominates. Past tense only for the study's own actions
  (`DSNY determined…`). Future via modals — `would` (52), `must` (26), `may`
  (25), `could` (8) — rarely bare `will`.
- **8–30 words, median ~19.** Two-sentence takeaways are common: verdict then
  qualifier, or verdict then cost.
- **Always a finite verb** — these are sentences, unlike the page titles.
- **Numbers in ~half**, and always **with the base named**: `89% of New York City
  streets with residential properties`, never a bare `89%`.

### The four "so what" moves

1. **Verdict with a threshold** — "viable for 89% … comprising 77% …"
2. **Negation + escape hatch** — "not a reliable, scalable solution … However, they are compatible with current fleet…"
3. **Absence claim** — "does not currently exist in the United States"
4. **Obligation** — "DSNY must work with industry to develop…"

Short sentences are deliberate rhythm breaks: `"Trash must go somewhere."` (4
words), `"Snow compatible."` (2 words, a table cell).

## 3. Standard page furniture

```
[Page title, top-left]                          [corner badge A / B / C, top-right]
[Bold takeaway sentence or short paragraph]
[Chart title]
[units line, lowercase]
    ── the graphic ──
                                    [boxed callout: "Containerization takeaways:"]
[Note: …] or [* …] or [a … b …]
                                                          [page number, bottom-right]
```

Chart title + units, stacked, verbatim:

```
Average daily waste weight by stream1     pounds, thousands
Average daily waste volume by stream2     cubic yards
Annual Snowfall (in)
Population density, New York City (2010)5
```

Pattern: `<Metric> by <cut>, <geography> (<year>)` on line 1; bare lowercase unit
on line 2.

**Scoping line then a single quantified consequence** — a recurring rhythm:

> "Example of shared containers on a mid-density street section in The Bronx"
> "25 shared containers would occupy 11.5 parking spaces (24% of total spaces currently available)"

**The takeaway box**, same header string every time, **1–2 bullets, never 3**:

```
Containerization takeaways:
 • The solution for New York City is not "one size fits all" and would require
   different containerization solutions based on density.
 • Containerizing New York City's high-density neighborhoods presents a unique challenge.
```

**Threshold definitions are printed under the chart**, so the claim is auditable:

> "Viable" defined as containers would take up <25% of available street length.

**Legends restate the encoded rule**, not just the colour, with traffic-light
names in quotes so the encoding survives a black-and-white print:

```
75+% street sections are "green", requiring <25% of street length
```

Sourcing: superscript numerals resolved in a rear `Works Cited` appendix keyed by
page number, plus a parallel `Image Credits` appendix. `Note:` lines and
lettered footnotes carry method caveats.

## 4. Chart types actually used

Big-number KPI row (3 across) · big-number grid (5 stats) · stacked column ·
paired % bars · two-segment donut · ranked benchmark table · time-series column ·
100% stacked bar by segment · schedule/calendar matrix · tick/Harvey-ball matrix
(27 city rows) · qualitative preference matrix · Marimekko-style share-of-market
bar · choropleth maps three-up · world map with pinned annotations · counted
pictogram · segmented 100% archetype bar · feature-comparison table with bolded
lead-in labels · two-column pro/con · head-to-head spec table · 2×3 roadmap grid ·
isometric streetscape renders · scale-analogy pictogram · captioned photo strips.

**Absent**: waterfall charts, 2×2 BCG bubble matrices, scatter plots, S-curves,
and any "Exhibit N of M" numbering.

## 5. Rhetorical devices worth stealing

**Enumeration announced in advance** — and then delivered exactly:

> "DSNY's assessment is that the hoist truck is not viable for scaled deployment in New York City for three reasons: 1. … 2. … 3. …"

**Archetype framing as the structural spine** — eight residential street
archetypes, compressed to a four-band scale used as chart axes (`Single family /
Low density / Mid density / High density`), then to a three-tier verdict:

```
A Currently viable with no required change to collection frequency
B Viability requires doubled collection frequency
C Viability not possible even with doubled collection frequency
```

**The scale analogy — the report's most memorable device:**

> "New Yorkers leave out 44 MILLION pounds of waste every day of service… Equal to the weight of 140 Statues of Liberty!"

> "If the daily volume of waste was set out in a straight line one foot wide by one foot high, it would extend 37 miles: five miles longer than the entire perimeter of Manhattan."

> "the City allocates 80% of all available curb space to on-street parking, and a combined area equivalent to 12 Central Parks."

**The crux sentence** — one per section, naming the single binding constraint:

> "The crux of the issue is that the City produces a high volume of waste in a small area, with little-to-no flexibility to build outside of pedestrian and street lanes…"

**Concession then pivot**: "Despite all of these challenges, options for
containerization in New York City … do exist."

**Rule-of-three closers**: "The goal is clear: cleaner streets, fewer rats, and a
more livable City."

**Assumptions stated as a checklist**, so the model is auditable:

> "Viability is determined on a block-to-block basis, and assumes the following:
> Maximum of 25% of available curb space … Containers must be able to hold 150% of
> current waste output … 4 cubic yard shared containers … Sufficient street width…"

## 6. Register

- Body sentences 20–40 words; takeaways 8–30.
- Heavy, systematic hedging: `~` (51×), `would` (52), `must` (26), `may` (25),
  `up to` (20), `at scale` (10), `approximately` (9), `per expert interviews` (5).
- Third-person institutional; the actor is always named (`DSNY`, `the City`).
  `we` appears only in the Commissioner's letter.
- Methodological humility stated, not hidden: *"a conservative assumption of
  'maximum distribution' was applied"*, *"the precise volume conversion is not
  known"*.
- The unit of analysis is defined once and never varies — `street section` occurs
  **97 times**.
- One deliberate register break, worth copying: *"In Europe, collection frequency
  is typically six to 14 times per week (yes, up to twice a day!)"*

## 7. How it closes

Not a call to action and **no "questions to consider" page**. It ends
analytically: a 2×3 `Pathway to Containerization` grid (`Immediate next steps` |
`Future vision` × `Residential / Institutional / Commercial`), then named,
bounded, dated pilots, then a substantial methodologically-defensive appendix
listing every assumption and subtraction.
