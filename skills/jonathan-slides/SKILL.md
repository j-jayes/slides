---
name: jonathan-slides
description: >-
  Build Quarto Reveal.js slides the way Jonathan builds them: a short locator
  heading, a takeaway sentence, evidence rather than prose, and full narration
  in speaker notes. Use when asked to "make slides", "build a deck", "turn this
  into a presentation", or when editing an existing .qmd presentation.
---

# How Jonathan builds slides

A slide is not a document page. Its job is to hold **one claim** and the evidence
for that claim, while the speaker does the talking. Prose on a slide competes with
the speaker and loses — so the words go in the speaker notes, and the slide gets
a picture, a table, or a number.

Everything below is read off a real deck: the thesis defence, rendered at
<https://j-jayes.github.io/kappa/> and sourced at
<https://github.com/j-jayes/kappa>. When in doubt, open it and copy the
pattern.

## 1. The two-tier title — the rule that matters most

Every content slide has a **locator** and a **takeaway**:

```markdown
## ⚡ Context

### Electrification and the grid rollout reached the Western Line first
```

- `##` is the **locator**: 1–3 words. Which section, paper, or workstream am I in?
  It repeats across consecutive slides on purpose — that repetition is what makes
  a long deck navigable.
- `###` is the **takeaway**: a full sentence stating what the audience should
  conclude *from this slide*. Not a topic label.

The Nexer template styles `##` as a small purple kicker and `###` as the large
action title, so following this habit produces the right hierarchy automatically.

> Anti-pattern: `## Results` with a chart and no `###`. The reader has to derive
> the point themselves, and they will derive a different one.

## 2. Evidence right, words left

The default shape is two columns, with the argument on the left and the proof on
the right:

```markdown
::::: {.columns}

:::: {.column width="55%"}
[chart or table]
::::

:::: {.column width="45%"}
#### Key drivers

- Short, parallel bullets
::::

:::::
```

**Nested fenced divs need more colons on the outer div.** A `::: {.takeaway}`
inside a `::: {.column}` inside a `::: {.columns}` silently breaks the layout —
Quarto prints "This usually indicates a problem with a fenced div" and the
columns stack vertically. Use 5 colons for `.columns`, 4 for `.column`, 3 for
anything nested inside. This is the single most common way a deck goes wrong.

## 3. Few words, many images and tables

Count the words on a slide. Over about 40 and it is an essay — move it into the
notes and replace it with the thing it describes.

Every figure carries a caption that says where it came from:

```markdown
![Income shares from @bengtsson2021WhatHappenedIncomes](assets/inequality.png){width=600}
```

## 4. Speaker notes are the actual script

Notes are written as **spoken prose**, in full sentences, the way it will be said
out loud — not as bullet reminders. They routinely run longer than the slide.

```markdown
::: {.notes}
So why do we care about Sweden as a case study? There are at least two reasons.
First, Sweden was a fast adopter — after Jonas Wenström discovered three-phase
current, rural electrification advanced rapidly between 1900 and 1921...
:::
```

This is what makes a deck rehearsable and reusable months later.

## 5. One colour per thread

When a deck has parallel workstreams (papers, workstreams, options), give each a
colour and carry it in the locator and on its appendix divider, so the audience
always knows which thread they are on:

```markdown
## [Paper II]{style="color:#d95f02;"}

### Income gains were largest at the bottom of the distribution
```

## 6. Progressive reveal, sparingly

`::: {.fragment}` for a point that lands better after the previous one, and
`::: {.incremental}` for a list that should build. Use it when sequence carries
meaning — not to drip-feed a list the audience could read at once.

## 7. Appendices, reached by button

Anything you might be asked about but will not present goes into an appendix
section, linked from the slide that provokes the question:

```markdown
[[More on Paper II]{.button}](#sec-appendix-p2)

# Paper II appendix {#sec-appendix-p2 background-color="#d95f02" visibility="uncounted"}
```

`visibility="uncounted"` keeps appendix slides out of the slide count;
`visibility="hidden"` parks a slide you are not using but do not want to delete.

## 8. Escape hatches

- `{.smaller}` on a dense slide, `{.scrollable}` when content genuinely overflows.
- ```` ```{=html} ```` raw blocks for a bespoke visual (the thesis deck builds its
  timeline strips this way). Note these do **not** survive export to PowerPoint.

## Working method

1. **Write the titles first, and read them in order.** The `###` sentences alone
   should tell the whole story. If they do not, the argument is wrong — fix that
   before making a single chart.
2. Build the evidence for each title. If you cannot find evidence, the title is a
   claim you cannot support: cut it or soften it.
3. Write the notes as narration.
4. Render and *look at it* — `quarto render deck.qmd` from `slides/`, then page
   through `_site/deck.html`. Use the kit's `tools/shoot_slides.py` to
   screenshot slides if you cannot open a browser.

## Branding

For Nexer work, use the `nexer-slides` skill — it supplies the template, brand
and PowerPoint export. For argument structure and chart rigour on a client deck,
`mckinsey-slides` covers the standards. This skill is about the shape of the
deck; those two are about its skin and its rigour.
