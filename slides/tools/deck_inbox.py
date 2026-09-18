"""Take in a colleague's deck and set up somewhere to work on it.

    python tools/deck_inbox.py intake "../inbox/Deras förslag.pptx"
    python tools/deck_inbox.py handback ../work/deras-forslag

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

`handback` checks the edited deck, diffs it against the original, renders it
again, and puts it in outbox/ under the colleague's own file name with a
change note beside it. A deck that has lost a part, or whose XML no longer
parses, does not get that far -- the last place to catch that is here rather
than in their PowerPoint.

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

import pptx_diff
import pptx_inventory
import pptx_to_md

ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent


def slug(name: str) -> str:
    """An ASCII directory name. 'Säljstöd 2.0_förslag' -> 'saljstod-2-0-forslag'."""
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


def handback(work: Path, render: bool = True) -> Path:
    """Check, diff, render and put the edited deck in outbox/."""
    work = Path(work)
    deck, original = work / "deck.pptx", work / "original.pptx"
    if not deck.is_file() or not original.is_file():
        raise SystemExit(f"{work} is not a work directory from `intake`")

    problems = pptx_diff.validate(deck)
    hard = [p for p in problems if not p.startswith("note:")]
    if hard:
        raise SystemExit("this deck would not open cleanly, so it is not going out:\n  "
                         + "\n  ".join(hard))
    result = pptx_diff.diff(original, deck)
    if not result["ok"]:
        raise SystemExit("this edit disturbed parts it should not have, so it is not "
                         "going out:\n  " + pptx_diff.report(original, deck, result))

    if render:
        shoot(deck, work / "after", work / "after.pdf")

    name = _original_name(work)
    out = work.parents[1] / "outbox" / f"{name.stem} (Nexer){name.suffix}"
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(deck, out)
    if render:
        shutil.copy2(work / "after.pdf", out.with_suffix(".pdf"))
    out.with_suffix(".changes.md").write_text(
        (work / "changes.md").read_text(encoding="utf8")
        + pptx_diff.report(original, deck, result) + "\n"
        + "".join(f"\n{p}" for p in problems if p.startswith("note:")) + "\n",
        encoding="utf8")
    print(f"{out}\n{pptx_diff.report(original, deck, result)}")
    return out


def _original_name(work: Path) -> Path:
    """The colleague's own file name, recovered from the change log's first line."""
    first = (work / "changes.md").read_text(encoding="utf8").splitlines()[0]
    return Path(first.removeprefix("# Changes to ").strip())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    take = sub.add_parser("intake", help="copy a deck out of inbox/ and read it")
    take.add_argument("deck", type=Path)
    take.add_argument("--no-render", action="store_true",
                      help="skip the PowerPoint export (no PNGs, no PDF)")
    back = sub.add_parser("handback", help="check, diff and send the edited deck out")
    back.add_argument("work", type=Path)
    back.add_argument("--no-render", action="store_true")
    args = ap.parse_args()
    if args.cmd == "intake":
        intake(args.deck, render=not args.no_render)
    else:
        handback(args.work, render=not args.no_render)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
