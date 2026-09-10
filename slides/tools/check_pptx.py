"""Report, or assert, which layout each slide of a rendered .pptx landed on.

    python tools/check_pptx.py my-deck.pptx                    # report
    python tools/check_pptx.py tests/reference-smoke.pptx --smoke   # assert

A render can succeed while silently falling back to pandoc's default layouts,
which surfaces as a styling mystery days later. The --smoke form turns that into
a failure; the bare form is a quick look at what pandoc chose for a real deck.
"""
import argparse
import re
import sys
import zipfile
from pathlib import Path

# What tests/reference-smoke.qmd must produce, in order.
SMOKE = [
    "Title Slide",           # title metadata
    "Section Header",        # # A section divider
    "Title and Content",     # bullets
    "Two Content",           # two text columns
    "Comparison",            # two columns, each heading + image
    "Content with Caption",  # framing text then an image
    "Content with Caption",  # framing text then a table
    "Blank",                 # empty ##
]


def layout_of_each_slide(path: Path) -> list[str]:
    z = zipfile.ZipFile(path)
    names = {
        p: re.search(r'<p:cSld[^>]*name="([^"]*)"', z.read(p).decode("utf8")).group(1)
        for p in z.namelist()
        if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", p)
    }
    out = []
    i = 1
    while f"ppt/slides/slide{i}.xml" in z.namelist():
        rels = z.read(f"ppt/slides/_rels/slide{i}.xml.rels").decode("utf8")
        target = re.search(r"slideLayouts/(slideLayout\d+\.xml)", rels).group(1)
        out.append(names[f"ppt/slideLayouts/{target}"])
        i += 1
    z.close()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("deck", type=Path)
    ap.add_argument("--smoke", action="store_true",
                    help="assert the reference-smoke.qmd layout sequence")
    ap.add_argument("--expect", help="comma-separated layout names to assert")
    args = ap.parse_args()

    got = layout_of_each_slide(args.deck)
    expected = SMOKE if args.smoke else (
        [x.strip() for x in args.expect.split(",")] if args.expect else None
    )

    width = max((len(x) for x in got), default=10)
    for i, g in enumerate(got):
        if expected is None:
            print(f"  slide {i + 1:>2}: {g}")
        else:
            e = expected[i] if i < len(expected) else "(unexpected slide)"
            print(f"  slide {i + 1:>2}: {g:<{width}} {'OK' if g == e else '!= ' + e}")

    if expected is None:
        seen = {g: got.count(g) for g in dict.fromkeys(got)}
        print(f"\n{len(got)} slides across {len(seen)} layouts: "
              + ", ".join(f"{k} x{v}" for k, v in seen.items()))
        # A deck that never leaves "Title and Content" usually means the
        # reference doc was not applied at all.
        if len(seen) == 1 and got:
            print("warning: every slide used one layout -- is reference-doc set?",
                  file=sys.stderr)
        return 0

    if got != expected:
        print(f"\nFAIL: got {len(got)} slides, expected {len(expected)}", file=sys.stderr)
        return 1
    print(f"\nall {len(got)} slides bound to the intended layout")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
