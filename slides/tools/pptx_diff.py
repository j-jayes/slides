"""Check a .pptx, and prove what changed in it.

    python tools/pptx_diff.py check deck.pptx                  # before sending
    python tools/pptx_diff.py diff original.pptx deck.pptx     # what we touched

Two jobs, both about the claim made back to the colleague.

`check` is the pre-flight. Every defect that makes PowerPoint offer to repair
a file is cheap to find in the package, and finding one here is worth a great
deal more than finding it in front of them. It is not a schema validator:
PowerPoint accepts plenty that the schema rejects and rejects a little that it
accepts, so this looks only for the faults that are known to break a deck.

`diff` is the evidence. Slides are matched by their sldId rather than their
position, because inserting one shifts every later number and a positional
comparison would report the whole deck as changed. A slide reported identical
is byte-for-byte what arrived -- not "looks the same", the same bytes.

Both read the package with zipfile and never write.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from pptx_edit import ID_ATTR, SLD_ID, SLD_ID_MIN
from pptx_to_md import NS, rels_of

P = f"{{{NS['p']}}}"
R = f"{{{NS['r']}}}"

# Parts nothing here should ever rewrite. A moved master, theme or layout can
# change how a slide nobody edited renders, which is exactly the failure this
# whole approach exists to rule out.
SACRED = re.compile(r"ppt/(slideMasters|slideLayouts|theme|notesMasters)/")

# Parts a deleted slide may legitimately take with it. A master, layout or
# theme is never among them, whatever was deleted.
REMOVABLE = re.compile(r"ppt/(slides|notesSlides|media|charts|embeddings|drawings)/")

# Parts that need their own Override and are not covered by the <Default> for
# "xml". Every deck declares that Default, so extension alone proves nothing:
# a slide missing its Override is a repair prompt even though the Default is
# right there.
NEEDS_OVERRIDE = re.compile(
    r"ppt/(slides|slideLayouts|slideMasters|notesSlides|notesMasters)/\w+\d+\.xml"
    r"|ppt/presentation\.xml")


def digests(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as z:
        return {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}


def _slide_ids(z: zipfile.ZipFile) -> dict[int, str]:
    """sldId -> slide part, in presentation order."""
    rels = rels_of(z, "ppt/presentation.xml")
    return {int(s.get("id")): rels[s.get(f"{R}id")]
            for s in ET.fromstring(z.read("ppt/presentation.xml")).iter(f"{P}sldId")}


def validate(path: Path) -> list[str]:
    """Everything wrong with this package that PowerPoint is known to mind."""
    problems = []
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        ct = z.read("[Content_Types].xml").decode("utf8")
        defaults = {e.lower() for e in re.findall(r'<Default Extension="([^"]+)"', ct)}
        overrides = set(re.findall(r'<Override PartName="/([^"]+)"', ct))

        for part in sorted(names):
            if part.endswith("/") or "/_rels/" in part or part == "[Content_Types].xml":
                continue
            if part in overrides:
                continue
            if NEEDS_OVERRIDE.fullmatch(part):
                problems.append(f"{part} has no Override in [Content_Types].xml; "
                                f"the Default for xml does not cover a slide part")
            elif part.rsplit(".", 1)[-1].lower() not in defaults:
                problems.append(f"{part} has no content type; PowerPoint will repair the deck")

        for part in sorted(n for n in names if n.endswith(".rels")):
            seen = set()
            for rel in ET.fromstring(z.read(part)):
                rid, target = rel.get("Id"), rel.get("Target")
                if rid in seen:
                    problems.append(f"{part} uses {rid} twice")
                seen.add(rid)
                if rel.get("TargetMode") == "External":
                    continue
                owner = part.replace("/_rels/", "/").removesuffix(".rels")
                resolved = _join(str(Path(owner).parent).replace("\\", "/"), target)
                if resolved not in names:
                    problems.append(f"{part}: {rid} points at {target}, which is not in the deck")

        ids, seen_ids = [], set()
        pres = z.read("ppt/presentation.xml").decode("utf8")
        for entry in SLD_ID.findall(pres):
            sld_id = int(ID_ATTR.search(entry).group(1))
            ids.append(sld_id)
            if sld_id in seen_ids:
                problems.append(f"slide id {sld_id} is used twice")
            if sld_id < SLD_ID_MIN:
                problems.append(f"slide id {sld_id} is below the {SLD_ID_MIN} floor")
            seen_ids.add(sld_id)

        notes_owner: dict[str, str] = {}
        for part in _slide_ids(z).values():
            try:
                ET.fromstring(z.read(part))
            except ET.ParseError as exc:
                problems.append(f"{part} is not well-formed XML ({exc}); "
                                f"a stray tag reaches PowerPoint as a repair prompt")
            targets = rels_of(z, part)
            layouts = [t for t in targets.values() if "slideLayouts/" in t]
            if len(layouts) != 1:
                problems.append(f"{part} is bound to {len(layouts)} layouts, not 1")
            declared = set(targets)
            used = set(re.findall(r'r:(?:id|embed|link)="([^"]+)"', z.read(part).decode("utf8")))
            for missing in sorted(used - declared):
                problems.append(f"{part} references {missing}, which its .rels does not declare")
            for notes in (t for t in targets.values() if "notesSlides/" in t):
                if notes in notes_owner:
                    problems.append(f"{notes} is the notes page of both "
                                    f"{notes_owner[notes]} and {part}")
                notes_owner[notes] = part

        stale = _stale_page_numbers(z)
        if stale:
            problems.append(
                f"note: this deck types its page numbers as text rather than using a "
                f"slide-number field, and {', '.join(stale)} disagree with their "
                f"position. Inserting or moving a slide cannot fix them.")

        if "sectionLst" in pres:
            problems.append("note: this deck has sections, and nothing here updates them; "
                            "check the section pane after adding or moving a slide")
    return problems


def _stale_page_numbers(z: zipfile.ZipFile) -> list[str]:
    """Slides whose typed-in page number disagrees with where they sit.

    A deck using <a:fld type="slidenum"> renumbers itself and never appears
    here. One that types the number goes stale the moment anyone inserts a
    slide -- which is worth saying before handing the deck back, especially
    when it arrived that way.
    """
    stale = []
    for n, part in enumerate(_slide_ids(z).values(), start=1):
        try:
            root = ET.fromstring(z.read(part))
        except ET.ParseError:
            continue  # already reported, and a worse problem than numbering

        for sp in root.iter(f"{P}sp"):
            off = sp.find("p:spPr/a:xfrm/a:off", NS)
            # Only the bottom-right corner: any other number on the slide is
            # content, not pagination.
            if off is None or int(off.get("y")) < 6000000 or int(off.get("x")) < 9000000:
                continue
            text = "".join(t.text or "" for t in sp.iter(f"{{{NS['a']}}}t")).strip()
            if text.isdigit() and int(text) != n:
                stale.append(f"slide {n} prints {text}")
    return stale


def _join(base: str, target: str) -> str:
    parts = [] if base in ("", ".") else base.split("/")
    for seg in target.split("/"):
        if seg == "..":
            parts.pop()
        elif seg and seg != ".":
            parts.append(seg)
    return "/".join(parts)


def diff(before: Path, after: Path) -> dict:
    """What changed between the deck that arrived and the deck going back."""
    b_parts, a_parts = digests(before), digests(after)
    with zipfile.ZipFile(before) as z:
        b_slides = _slide_ids(z)
    with zipfile.ZipFile(after) as z:
        a_slides = _slide_ids(z)

    identical, changed = [], []
    for sld_id, part in a_slides.items():
        if sld_id not in b_slides:
            continue
        old = b_parts.get(b_slides[sld_id])
        (identical if old == a_parts.get(part) else changed).append(sld_id)

    parts = {
        "changed": sorted(n for n in b_parts.keys() & a_parts.keys()
                          if b_parts[n] != a_parts[n]),
        "added": sorted(a_parts.keys() - b_parts.keys()),
        "removed": sorted(b_parts.keys() - a_parts.keys()),
    }
    slides_removed = [i for i in b_slides if i not in a_slides]
    # Deleting a slide is done on purpose and legitimately takes the slide, its
    # rels, its notes page and any media only it used. Anything else that
    # disappears was an accident, and so is anything at all when no slide went.
    expected = REMOVABLE if slides_removed else re.compile(r"(?!)")
    unexplained = [n for n in parts["removed"] if not expected.match(n)]
    disturbed = [n for n in parts["changed"] + parts["removed"] if SACRED.match(n)]
    return {
        "slides": {
            "identical": identical,
            "changed": changed,
            "added": [i for i in a_slides if i not in b_slides],
            "removed": slides_removed,
        },
        "parts": parts,
        "disturbed": disturbed,
        "unexplained": unexplained,
        "ok": not unexplained and not disturbed,
    }


def report(before: Path, after: Path, result: dict) -> str:
    """The diff as a paragraph for changes.md, which goes back with the deck."""
    s = result["slides"]
    lines = [f"{len(s['identical'])} of {len(s['identical']) + len(s['changed'])} "
             f"slides from {before.name} are byte-for-byte unchanged."]
    if s["added"]:
        lines.append(f"Added: {len(s['added'])} slide(s).")
    if s["changed"]:
        lines.append(f"Edited: slide id(s) {', '.join(str(i) for i in s['changed'])}.")
    if s["removed"]:
        lines.append(f"Removed: slide id(s) {', '.join(str(i) for i in s['removed'])}.")
    if result["disturbed"]:
        lines.append(f"WARNING: {', '.join(result['disturbed'])} changed. "
                     f"Slides nobody edited may now render differently.")
    if result["unexplained"]:
        lines.append(f"WARNING: parts lost that no deleted slide accounts for: "
                     f"{', '.join(result['unexplained'])}.")
    return " ".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    one = sub.add_parser("check", help="look for what PowerPoint would refuse")
    one.add_argument("deck", type=Path)
    two = sub.add_parser("diff", help="compare the deck going back with the one that arrived")
    two.add_argument("before", type=Path)
    two.add_argument("after", type=Path)
    args = ap.parse_args()

    if args.cmd == "check":
        problems = validate(args.deck)
        for problem in problems:
            print(f"  {problem}")
        hard = [p for p in problems if not p.startswith("note:")]
        print(f"{args.deck.name}: {len(hard) or 'no'} problem(s)")
        return 1 if hard else 0

    result = diff(args.before, args.after)
    print(report(args.before, args.after, result))
    for kind in ("changed", "added", "removed"):
        for part in result["parts"][kind]:
            print(f"  {kind:8} {part}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
