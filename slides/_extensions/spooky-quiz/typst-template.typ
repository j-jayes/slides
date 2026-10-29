// Spooky Quiz answer sheet: white page for the printer, pumpkin band on top.
#let ink = rgb("#363039")
#let pumpkin = rgb("#FF6F08")
#let purple = rgb("#872FE0")
#let slime = rgb("#89E031")
#let emoji-font = ("Segoe UI Emoji",)

#let spooky(title: none, subtitle: none, doc) = {
  set page(
    margin: (x: 1.6cm, top: 2.7cm, bottom: 1.3cm),
    background: {
      place(top, rect(width: 100%, height: 2.1cm, fill: pumpkin))
      place(top + left, dx: 1.6cm, dy: 0.45cm,
        text(font: "Creepster", size: 26pt, fill: white, stroke: 0.4pt + ink)[#title])
      place(top + right, dx: -1.6cm, dy: 0.6cm,
        text(font: emoji-font, size: 22pt)[🦇 🎃 👻])
      place(bottom + left, dx: 0.6cm, dy: -0.5cm, text(font: emoji-font, size: 14pt)[🕸️])
      place(bottom + right, dx: -0.6cm, dy: -0.5cm, text(font: emoji-font, size: 14pt)[🕷️])
    },
    footer: context align(center, text(size: 8pt, fill: ink.lighten(40%))[
      #subtitle · page #counter(page).display()
    ]),
  )
  set text(font: ("Special Elite",) + emoji-font, size: 10.5pt, fill: ink)
  show heading: set text(font: "Creepster", weight: "regular", fill: pumpkin)
  show heading.where(level: 1): it => block(above: 1.1em, below: 0.6em,
    text(size: 20pt, stroke: 0.3pt + purple, it.body))
  doc
}

// Building blocks the answer sheet is generated from (R/quiz.R).
#let blank(w) = box(width: w, height: 1.3em, stroke: (bottom: 0.6pt + ink))
#let qn(n) = box(width: 2.4em, text(font: "Creepster", size: 13pt, fill: pumpkin)[#n])
#let letter(l) = box(width: 1.7em, height: 1.7em, radius: 50%, stroke: 0.8pt + ink,
  align(center + horizon, l))
#let qrow(n, body) = block(below: 0.6em, grid(columns: (2.4em, 1fr), align: horizon + left, qn(n), body))

#let mc(n, k: 4) = qrow(n, stack(dir: ltr, spacing: 1.4em, ..("A", "B", "C", "D").slice(0, k).map(letter)))
#let order(n) = qrow(n, stack(dir: ltr, spacing: 0.4em,
  blank(2.6em), [→], blank(2.6em), [→], blank(2.6em), [→], blank(2.6em),
  h(1.2em), text(size: 8pt, fill: ink.lighten(40%))[first → last]))
// Taller than the other rows: rebus answers are whole phrases.
#let open(n) = qrow(n, box(height: 2.2em, align(bottom, blank(100%))))
#let song(n) = qrow(n, grid(columns: (auto, 1fr, auto, 1fr), gutter: 0.5em, align: bottom,
  [Song], blank(100%), [Artist], blank(100%)))
#let score(max) = align(right, text(size: 10pt)[Round score: #box(width: 3em, stroke: (bottom: 0.6pt + ink)) / #max])
#let team-box() = block(width: 100%, inset: 10pt, radius: 8pt, stroke: 1.2pt + pumpkin,
  [Team name: #blank(70%)])
