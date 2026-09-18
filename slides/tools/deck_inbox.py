"""Take in a colleague's deck and set up somewhere to work on it.

    python tools/deck_inbox.py intake "../inbox/Deras förslag.pptx"

Drop what arrives in inbox/. This copies it to work/<slug>/ and lays out
everything an agent needs to read it, see it and change it:

    original.pptx    the file exactly as it arrived, never written to again
    deck.pptx        the working copy -- what tools/pptx_edit.py edits
    deck.md          the words, from tools/pptx_to_md.py
    assets/          pictures pulled out of the deck
    inventory.json   the handles, from tools/pptx_inventory.py
    before/*.png     one per slide, as PowerPoint draws them
    before.pdf       the whole deck, for reading at length
    changes.md       what we did, which goes back with the deck

The original is the baseline the return step diffs against, which is what
makes "we changed nothing else" a claim rather than a hope. Nothing here
writes to inbox/.

The work directory is named in ASCII however the sender named the file: COM
resolves paths through the process locale and PowerShell is shelled out to,
and neither is worth debugging over an umlaut.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import unicodedata
from datetime import date
from pathlib import Path

import pptx_inventory
import pptx_to_md

ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent


def slug(name: str) -> str:
    """An ASCII directory name. 'Västerhuset 2.0_förslag' -> 'vasterhuset-2-0-forslag'."""
    flat = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", flat.lower())).strip("-")


def shoot(deck: Path, png_dir: Path, pdf: Path) -> None:
    """One PNG per slide plus a PDF, via PowerPoint.

    Also the corruption test: a malformed package fails to open here rather
    than in front of the colleague.
    """
    result = subprocess.run(
        ["powershell", "-NoProfile", "-File", str(TOOLS / "shoot_pptx.ps1"),
         "-Deck", str(deck), "-OutDir", str(png_dir), "-Pdf", str(pdf)],
        capture_output=True, text=True)
    if result.returncode != 0 or not pdf.exists():
        raise SystemExit(f"PowerPoint could not export {deck.name}. "
                         f"A package it refuses to open is the first thing to suspect.\n"
                         f"{result.stdout}\n{result.stderr}")
    # PowerPoint writes Slide1.PNG ... Slide10.PNG, which sort lexically into
    # the wrong order. Renumber so the files read in slide order.
    for png in png_dir.glob("*.PNG"):
        n = int(re.search(r"(\d+)", png.stem).group(1))
        png.rename(png_dir / f"slide-{n:03d}.png")


def intake(src: Path, root: Path = ROOT, render: bool = True) -> Path:
    """Copy `src` into work/<slug>/ and lay out everything we read it with."""
    src = Path(src)
    if not src.is_file():
        raise SystemExit(f"no such deck: {src}")
    work = root / "work" / slug(src.stem)
    if work.exists():
        raise SystemExit(f"{work} already exists. Delete it to start over, or "
                         f"keep working in it -- re-running would overwrite deck.pptx "
                         f"and lose any edits already made.")
    (work / "assets").mkdir(parents=True)

    shutil.copy2(src, work / "original.pptx")
    shutil.copy2(src, work / "deck.pptx")
    deck = work / "deck.pptx"

    slides, with_notes = pptx_to_md.convert(deck, work / "deck.md", work / "assets")
    inv = pptx_inventory.inventory(deck)
    (work / "inventory.json").write_text(
        json.dumps(inv, indent=2, ensure_ascii=False), encoding="utf8")
    (work / "changes.md").write_text(
        f"# Changes to {src.name}\n\n"
        f"Taken in on {date.today():%Y-%m-%d}: {slides} slides, {with_notes} with notes, "
        f"{inv['kind']}, {len(inv['layouts'])} layout(s).\n\n"
        f"Every slide not listed below is byte-identical to the file as it arrived.\n\n",
        encoding="utf8")

    if render:
        shoot(deck, work / "before", work / "before.pdf")
    print(f"{work}: {slides} slides, {with_notes} with notes, {inv['kind']}, "
          f"{sum(len(s['shapes']) for s in inv['slides'])} shapes")
    return work


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    take = sub.add_parser("intake", help="copy a deck out of inbox/ and read it")
    take.add_argument("deck", type=Path)
    take.add_argument("--no-render", action="store_true",
                      help="skip the PowerPoint export (no PNGs, no PDF)")
    args = ap.parse_args()
    intake(args.deck, render=not args.no_render)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
