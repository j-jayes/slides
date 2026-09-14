# Choosing the style for the AI education deck

14 September 2026. Six images, $0.40, about four minutes. One subject, three
candidate styles, two replicates each, then look at all six together.

The subject was deliberately dull and domestic, because a style has to survive
an ordinary scene: *a person at an open fridge late in the day, deciding what to
cook from the odds and ends on the shelves.*

All three candidates carried the same palette constraint, since this deck is
branded:

> Palette strictly limited to deep violet `#5A1F9F`, light violet `#AA4BF4`,
> pale blue `#D9E6F0` and a warm cream ground, with a single accent of orange
> `#FF5028` used sparingly on one element only.

## The three

| Candidate | Style prompt | Verdict |
|---|---|---|
| **A, risograph** | Flat vector editorial illustration, lineless, forms built from blocks of flat colour with soft textured shading, and a prominent grainy risograph texture over the entire image. | **Chosen.** Both replicates held the style, the palette and the single accent. Reads at column size. |
| B, papercut | Layered papercut collage built from cut construction paper shapes with visible cut edges and soft drop shadows between the layers. | Charming and much too simple. Faces came back blank, and one replicate invented a second person. |
| C, gouache | Chunky gouache illustration with opaque matte colour, visible brushwork and bold simplified shapes, in the manner of a mid-century picture book. | Handsome at full size, muddy at column size. The brushwork fights the texture of a projected slide, and one replicate spent the orange twice. |

The deciding test was not which looked best on screen at full size. It was which
still read as a picture of something when shrunk into 45% of a slide. A won
that easily; C lost it.

## The chosen style, verbatim

```yaml
defaults:
  aspect-ratio: "4:3"
  style: >
    Flat vector editorial illustration, lineless, forms built from blocks of
    flat colour with soft textured shading, and a prominent grainy risograph
    texture over the entire image. Palette strictly limited to deep violet
    #5A1F9F, light violet #AA4BF4, pale blue #D9E6F0 and a warm cream ground,
    with a single accent of orange #FF5028 used sparingly on one element only.
    Calm, modern and approachable. One clear subject, uncluttered composition,
    generous empty space. No text, no letters and no numbers anywhere in the
    image.
```

Three clauses in there are doing work beyond the look:

- **"One clear subject, uncluttered composition, generous empty space"** keeps
  the scene legible once it is a third of a slide wide.
- **"single accent ... on one element only"** is the chart rule applied to
  artwork. Without it the model paints three orange things and the eye has
  nowhere to land.
- **"No text, no letters and no numbers"** in the style rather than in each
  description. Said once, obeyed everywhere.

## What it cost, end to end

| Step | Images | Cost |
|---|---|---|
| Smoke test | 1 | $0.07 |
| Style experiment | 6 | $0.40 |
| Character sheet, `n: 3` | 3 | $0.20 |
| Six scenes, `n: 3` | 18 | $1.21 |
| | **28** | **$1.88** |

Eighteen scene images for six slides is the right ratio. Roughly one in three
was usable, and picking from three is faster and cheaper than re-prompting
until one attempt is perfect.

## The character

Two photographs went in as references, `jonathan-photo.jpg` (a company headshot)
and `jonathan-run.jpg` (full length, at the end of a race). The sheet asked for
three views at `n: 3`. Of the three sheets, one came back with blue-grey skin
and one with an oversized close-up; the third was right and became
`jonathan.png`.

Every scene then referenced `[jonathan]` and nothing else. The violet jumper in
the character sheet is what actually carries continuity across the six slides —
more than the face does, at that size.
