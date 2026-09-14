---
name: illustrate-slides
description: >-
  Illustrate a deck with AI-generated images the reproducible way — prompts in a
  YAML file, bananarama calling Gemini, one shared style so every slide matches,
  and a reference image so the same character appears throughout. Use when a
  slide needs a picture rather than a chart, or when asked to "illustrate these
  slides", "add an image here", or "generate artwork for the deck".
---

# Illustrations belong in version control, not in a chat window

Adapted from Hadley Wickham,
[Illustrating my slides with AI](https://tidydesign.substack.com/p/illustrating-my-slides-with-ai)
(3 August 2026), and the R package it describes,
[bananarama](https://github.com/hadley/bananarama).

Generate **illustrations**, never photos and never diagrams. An AI photograph on
a work slide is misleading at best and uncanny at worst. An AI diagram looks
impressive and explains nothing, and you cannot nudge a box or reword a label,
so you end up prompt-tweaking towards something you could have drawn faster
yourself — that is what `ggplot-diagrams` is for. An illustration has a
different job: it evokes a feeling and then gets out of the way, so the audience
keeps watching you.

The workflow is a YAML file and one function call. The prompts are committed, so
a year later you can still see which prompt produced which picture.

## Setup, once per machine

```bash
# bananarama is pure R, but pkgbuild demands Rtools on Windows, so install the
# dependencies with pak and the package itself straight from source.
Rscript -e "install.packages('pak'); pak::pak(c('ellmer', 'magick', 'yaml12', 'openssl'))"
curl -sL https://github.com/hadley/bananarama/archive/refs/heads/main.zip -o b.zip
unzip -q b.zip && R CMD INSTALL --no-multiarch bananarama-main
```

On Windows R is usually not on PATH; call it as
`"C:\Program Files\R\R-4.5.1\bin\Rscript.exe"`.

The key is a Gemini API key in `.env` at the repo root. `.env` is gitignored,
and every run loads it first:

```r
readRenviron(".env")
bananarama::bananarama("slides/assets/illustrations/my-deck.yml")
```

Creating the key, the project it bills to, and how to rotate it are in
[reference/gcloud-setup.md](reference/gcloud-setup.md).

## The YAML contract

```yaml
defaults:
  aspect-ratio: "4:3"        # 16:9 for full-bleed, 4:3 or 1:1 for a column
  style: >                   # appended to every description below
    ...
output-dir: my-deck          # relative to the YAML; default is the YAML's name

images:
  - name: fridge             # becomes fridge.png
    description: >
      [jonathan] at an open fridge deciding what to cook.
```

| Key | What it does |
|---|---|
| `defaults.style` | Appended to every description. This is what makes the deck look like one deck. |
| `aspect-ratio` | `"16:9"`, `"4:3"`, `"1:1"`, `"3:2"`. Default `16:9`. |
| `n` | Replicates, written as `name-1.png`, `name-2.png`. Per image, or in `defaults`. |
| `seed` | Makes a run more, though not perfectly, repeatable. Gemini only. |
| `model` | Default `gemini-3.1-flash-image-preview`. `gemini-3-pro-image` costs twice as much. |
| `[name]` | A reference image: `name.png`, `.jpg`, `.jpeg`, `.webp` or `.gif` **beside the YAML**. |
| `force` | Regenerate images that already exist. |

**Existing files are skipped.** That is the whole convenience: commit the PNGs
next to the YAML and a re-run does nothing and costs nothing. To reroll one
image, delete that one PNG.

## Developing a style

Write the style once in `defaults.style`, never per image, or the deck stops
looking like a deck. In a presentation the changes between slides should be
meaningful, and a wandering style is a change that means nothing.

Do not copy someone else's, ours included. Photograph an illustration you like,
ask Gemini to describe its style, then try three candidates on one subject at
`n: 2` and look at the six side by side. That costs about $0.40 and settles an
argument you would otherwise be having six slides later.

Two things earn their place in any style for a branded deck:

- **Name the hex codes.** "Palette strictly limited to deep violet `#5A1F9F`,
  light violet `#AA4BF4`, pale blue `#D9E6F0` and a warm cream ground, with a
  single accent of orange `#FF5028` used sparingly on one element only." The
  model holds this well, and it is the same one-accent discipline as a chart.
- **"No text, no letters and no numbers anywhere in the image."** Put it in the
  style, not in each description. Models render text as convincing gibberish,
  and nobody in the room will read past it.

The style used for the AI education deck, and the two it beat, are in
[reference/style-experiment.md](reference/style-experiment.md).

## A recurring character

If a person appears on more than one slide, they have to be the same person.
Photographs go in as references; the stylised character comes out once, and is
then the only thing you reference.

1. Put two photographs beside the YAML — one face, one full length.
2. Generate a character sheet at `n: 3`: front view, three-quarter view and a
   head-and-shoulders close-up on a plain ground. Describe them in words as
   well (`early thirties, round dark-rimmed glasses, light stubble`), because
   the model uses the words and the pictures together.
3. Pick one, save it as `jonathan.png`, and reference **that** from every scene.
   Crop out any part you particularly like and keep it as its own reference.

Ask for "simple friendly cartoon features, not a portrait likeness". A style
this flat cannot carry a real likeness, and chasing one produces an uncanny
near-miss. Keep the clothing in the character sheet and the scenes will keep it
too, which does more for continuity than the face does.

## Putting one on a slide

Generated images live with the deck, not with this skill:

```
slides/assets/illustrations/my-deck.yml     # the prompts, committed
slides/assets/illustrations/my-deck/*.png   # the images, committed
slides/assets/illustrations/jonathan.png    # the character, committed
```

On a statement slide, put the text in one column and the picture in the other.
`.ask` styles `.lead` and `.question` wherever they sit, so they work inside a
column unchanged:

```markdown
## {.ask .center background-color="#5A1F9F"}

::::: {.columns}

:::: {.column width="55%"}

::: {.lead}
Räck upp handen om du har använt AI för att…
:::

::: {.question}
planera veckans middagar, eller laga något av det som fanns kvar i kylen
:::

::::

:::: {.column width="45%"}

![](../assets/illustrations/intro-1/middag.png)

::::

:::::
```

A cream-grounded illustration on a purple slide reads as a card, which is the
effect you want: plainly an illustration, not a window.

## Cost, and the artists

About **$0.07** an image at 1K on the default model, and there is no free tier
for any image model. A style experiment, a character sheet and six slides came
to about $1.90. Cheap per image, not cheap across forty rerolls, so generate
three replicates and choose rather than re-prompting.

These models were trained on images scraped from the internet without the
consent of the artists who made them. That is true whether or not it is
convenient. If you use this, buy art from people.

## What does not work

- **Editing.** bananarama generates, it does not edit. To change a finished
  image, take it to Gemini chat and be blunt: "move the text box to the left"
  works where "the robot should say the words" does nothing. Or crop it
  yourself, which is usually faster.
- **Text in images.** Every time. Put the words on the slide instead, where they
  are in the deck's own typeface and can be corrected.
- **The aspect ratio is a near miss.** Ask for 16:9 and Gemini returns 16.1:9;
  4:3 comes back as 1200 × 896. Anything that must line up exactly needs a crop.
- **Full-bleed backgrounds in PowerPoint.** `pptx-nexer.lua` treats any slide
  carrying `background-image` as dark and forces the title white, so a light
  illustration behind a title gives you white on cream. Use a column instead.
- **`width`/`height` in PowerPoint.** Ignored; pandoc scales every image to its
  placeholder. Only the aspect ratio survives, so choose it in the YAML.
- **A prompt for the scene you have already pictured exactly.** Describe the
  feeling and let the model surprise you, or you will spend $5 arriving at
  something worse than its second attempt.

## Verifying it

```bash
cd slides
quarto render intro/my-deck.qmd
python tools/shoot_slides.py _site/intro/my-deck.html --all
```

Then **look at them**, at slide size rather than full size. Check that the
character is recognisably the same person on every slide, that no image smuggled
in a word, that the accent colour appears once per image rather than five times,
and that the picture still reads at the size it is actually shown.

## Related skills

`nexer-slides` is the skin — palette, logo rules, and what PowerPoint does to
each component. `jonathan-slides` is the structure. `ggplot-diagrams` is what
you want when the picture has to explain something rather than evoke it.
