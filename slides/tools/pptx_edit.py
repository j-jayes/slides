"""Change a .pptx without disturbing the slides you did not change.

    python tools/pptx_edit.py xml  deck.pptx 8              # read slide 8's XML

Everything here is a zip rewritten to a zip. Parts this was not asked to
touch are copied across as bytes, never re-serialised, so a slide nobody
edited comes out byte-for-byte what the colleague sent -- which
tools/pptx_diff.py then proves rather than assumes.

XML is read with ElementTree and written with targeted string edits. That is
not squeamishness: round-tripping a pptx through ElementTree rewrites the
namespace prefixes, and PowerPoint will not open the result.

The two rules a new slide has to satisfy, both learned the hard way by
everyone who has done this:

  * register it in all four places -- the part itself, its .rels, an
    Override in [Content_Types].xml, a Relationship in
    ppt/_rels/presentation.xml.rels, and a <p:sldId> in the sldIdLst.
    Miss one and PowerPoint offers to repair the file.
  * never reorder the children of <p:presentation>. A deck written by
    PptxGenJS puts <p:notesMasterIdLst> where the schema does not expect
    it; PowerPoint reads that happily, and tidying it kills the deck.
"""
from __future__ import annotations

import argparse
import os
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from pptx_to_md import NS, rels_of

P = f"{{{NS['p']}}}"
R = f"{{{NS['r']}}}"
OFFDOC = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
SLIDE_CT = "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"

# ST_SlideId in pml.xsd: 256 <= id <= 2147483647. Below the floor PowerPoint
# repairs the file; the ceiling is where the master and layout id space starts.
SLD_ID_MIN, SLD_ID_MAX = 256, 2147483647

# `id="12"` but not `r:id="rId12"`. The lookbehind is the whole point.
ID_ATTR = re.compile(r'(?<![:\w])id="(\d+)"')
# A <p:sldId/> entry, in either dialect: PowerPoint writes `/>`, pandoc ` />`.
# \b keeps this off <p:sldIdLst and off p14:sldId inside a section list.
SLD_ID = re.compile(r"<p:sldId\b[^>]*?/>")


def rewrite(src: Path, dst: Path, replace: dict[str, bytes] | None = None,
            add: dict[str, bytes] | None = None, drop: set[str] | None = None) -> None:
    """Copy `src` to `dst`, applying the three changes and nothing else.

    Entry order and compression are preserved, and every part not named is
    written back byte-for-byte.
    """
    replace, add, drop = replace or {}, add or {}, drop or set()
    with zipfile.ZipFile(src) as zin:
        names = zin.namelist()
        known = set(names)
        for name in list(replace) + list(drop):
            if name not in known:
                # Silence here would write a deck that just lacks the edit.
                raise SystemExit(f"{src.name} has no part {name}")
        for name in add:
            if name in known:
                raise SystemExit(f"{src.name} already has part {name}; "
                                 f"use replace= to change it")

        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                if info.filename in drop:
                    continue
                data = replace.get(info.filename)
                if data is None:
                    data = zin.read(info.filename)
                # A fresh ZipInfo. Passing `info` through would mutate it and
                # every later read from `src` would fail on a bad CRC.
                out = zipfile.ZipInfo(info.filename, info.date_time)
                out.compress_type = info.compress_type
                out.external_attr = info.external_attr
                zout.writestr(out, data)
            for name, data in add.items():
                zout.writestr(zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)), data,
                              zipfile.ZIP_DEFLATED)


def edit(deck: Path, **changes) -> None:
    """Apply `changes` to `deck` in place, or leave it exactly as it was."""
    tmp = deck.with_suffix(".pptx.tmp")
    try:
        rewrite(deck, tmp, **changes)
        try:
            os.replace(tmp, deck)
        except PermissionError as exc:
            raise SystemExit(
                f"cannot write {deck.name}: {exc.strerror}. "
                f"Close it in PowerPoint and run this again.") from exc
    finally:
        tmp.unlink(missing_ok=True)


def read(deck: Path, part: str) -> str:
    with zipfile.ZipFile(deck) as z:
        return z.read(part).decode("utf8")


def slide_parts(deck: Path) -> list[str]:
    """Slide parts in presentation order."""
    with zipfile.ZipFile(deck) as z:
        return [rels_of(z, "ppt/presentation.xml")[s.get(f"{R}id")]
                for s in ET.fromstring(z.read("ppt/presentation.xml")).iter(f"{P}sldId")]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    dump = sub.add_parser("xml", help="print one slide's XML, to read or edit")
    dump.add_argument("deck", type=Path)
    dump.add_argument("slide", type=int)
    args = ap.parse_args()
    order = slide_parts(args.deck)
    if not 1 <= args.slide <= len(order):
        raise SystemExit(f"slide {args.slide} is outside 1..{len(order)}")
    print(read(args.deck, order[args.slide - 1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
