"""Change a .pptx without disturbing the slides you did not change.

    python tools/pptx_edit.py xml  deck.pptx 8              # read slide 8's XML
    python tools/pptx_edit.py add  deck.pptx --clone 8 --after 8
    python tools/pptx_edit.py add  deck.pptx slide.xml --after 8

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
PKG_RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
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


def _free_rid(deck: Path) -> str:
    """An rId used neither in presentation.xml.rels nor in presentation.xml.

    The second half matters: an id can be referenced by the presentation and
    reusing it silently repoints an existing reference.
    """
    used = set(re.findall(r'Id="rId(\d+)"', read(deck, "ppt/_rels/presentation.xml.rels")))
    used |= set(re.findall(r'r:id="rId(\d+)"', read(deck, "ppt/presentation.xml")))
    return f"rId{max((int(i) for i in used), default=0) + 1}"


def _free_slide_id(pres: str) -> int:
    ids = [int(ID_ATTR.search(m).group(1)) for m in SLD_ID.findall(pres)]
    new = max(ids, default=SLD_ID_MIN - 1) + 1
    if not SLD_ID_MIN <= new <= SLD_ID_MAX:
        raise SystemExit(f"no slide id free below {SLD_ID_MAX}")
    return new


def _free_slide_part(deck: Path) -> str:
    """The next slideN.xml. Existing files are never renumbered."""
    with zipfile.ZipFile(deck) as z:
        used = [int(m.group(1)) for n in z.namelist()
                if (m := re.fullmatch(r"ppt/slides/slide(\d+)\.xml", n))]
    return f"ppt/slides/slide{max(used, default=0) + 1}.xml"


def add_slide(deck: Path, *, xml: bytes | None = None, clone: int | None = None,
              after: int | None = None, layout: str | None = None) -> dict:
    """Put a slide into `deck` after slide number `after` (0 = first).

    `clone` copies slide number N, which is the way to author one that has to
    look native: a deck with no placeholders offers nothing to build on, and
    an existing slide is a working example of its own design.
    """
    order = slide_parts(deck)
    if (xml is None) == (clone is None):
        raise SystemExit("give either a slide XML file or --clone N, not both")
    if after is None:
        after = len(order)
    if not 0 <= after <= len(order):
        raise SystemExit(f"--after {after} is outside 0..{len(order)}")

    with zipfile.ZipFile(deck) as z:
        if clone is not None:
            if not 1 <= clone <= len(order):
                raise SystemExit(f"--clone {clone} is outside 1..{len(order)}")
            source = order[clone - 1]
            xml = z.read(source)
            source_rels = z.read(f"ppt/slides/_rels/{Path(source).name}.rels").decode("utf8")
        else:
            source, source_rels = None, None
        layout_part = layout or _layout_of(z, order[max(after - 1, 0)] if order else None)

    try:
        ET.fromstring(xml)
    except ET.ParseError as exc:
        raise SystemExit(f"that is not well-formed XML, so PowerPoint would "
                         f"refuse the deck: {exc}") from exc

    part = _free_slide_part(deck)
    name = Path(part).name
    rels = _slide_rels(source_rels, layout_part)
    _check_references(xml, rels)

    pres = read(deck, "ppt/presentation.xml")
    pres_rels = read(deck, "ppt/_rels/presentation.xml.rels")
    ct = read(deck, "[Content_Types].xml")
    rid, sld_id = _free_rid(deck), _free_slide_id(pres)

    edit(deck,
         add={part: xml, f"ppt/slides/_rels/{name}.rels": rels.encode("utf8")},
         replace={
             "ppt/presentation.xml": _insert_sld_id(pres, sld_id, rid, after).encode("utf8"),
             "ppt/_rels/presentation.xml.rels": _insert_before(
                 pres_rels, "</Relationships>",
                 f'<Relationship Id="{rid}" Type="{OFFDOC}/slide" '
                 f'Target="slides/{name}"/>').encode("utf8"),
             "[Content_Types].xml": _insert_before(
                 ct, "</Types>",
                 f'<Override PartName="/{part}" ContentType="{SLIDE_CT}"/>').encode("utf8"),
         })
    return {"part": part, "sldId": sld_id, "rId": rid, "position": after + 1,
            "cloned_from": source}


# A <p:sp> never contains another, so a non-greedy match is exact.
SHAPE = re.compile(r"<p:sp>.*?</p:sp>", re.S)
PARA = re.compile(r"<a:p\s*/>|<a:p>.*?</a:p>", re.S)
RUN = re.compile(r"<a:r>.*?</a:r>", re.S)
# An <a:rPr> usually has children -- <a:latin/> among them -- so the first
# "/>" inside it is not its own end. Match the empty and full forms apart.
RPR = re.compile(r"<a:rPr\b[^>]*/>|<a:rPr\b[^>]*>.*?</a:rPr>", re.S)


def set_text(deck: Path, *, slide: int, shape: int, para: int,
             text: str, flatten: bool = False) -> dict:
    """Rewrite one paragraph, keeping the formatting it already carries.

    The paragraph becomes a single run wearing the first run's properties.
    That is what keeps the colleague's type size, weight and typeface --
    assigning to the text frame wholesale is what loses them.
    """
    order = slide_parts(deck)
    if not 1 <= slide <= len(order):
        raise SystemExit(f"slide {slide} is outside 1..{len(order)}")
    part = order[slide - 1]
    xml = read(deck, part)

    found = next((m for m in SHAPE.finditer(xml)
                  if re.search(r'<p:cNvPr id="(\d+)"', m.group(0))
                  and int(re.search(r'<p:cNvPr id="(\d+)"', m.group(0)).group(1)) == shape), None)
    if found is None:
        raise SystemExit(f"slide {slide} has no shape with id {shape}; "
                         f"inventory.json lists the ids")
    paras = list(PARA.finditer(found.group(0)))
    if not 0 <= para < len(paras):
        raise SystemExit(f"shape {shape} has {len(paras)} paragraph(s), so "
                         f"--para {para} is outside 0..{len(paras) - 1}")
    old = paras[para].group(0)

    if "<a:fld" in old:
        raise SystemExit("that paragraph holds a field, whose text PowerPoint "
                         "generates. Editing it here would be overwritten.")
    runs = RUN.findall(old)
    if len(runs) > 1 and not flatten and not _uniform(runs):
        raise SystemExit(
            f"the runs in that paragraph are formatted differently, so rewriting it "
            f"as one run would lose the distinction. Pass --flatten to accept that.")

    new = _one_run(old, runs, text)
    body = found.group(0)[:paras[para].start()] + new + found.group(0)[paras[para].end():]
    edit(deck, replace={part: (xml[:found.start()] + body + xml[found.end():]).encode("utf8")})
    return {"part": part, "shape": shape, "para": para, "text": text}


def _uniform(runs: list[str]) -> bool:
    """Do these runs differ by anything but proofing noise?

    Spell-checking splits a paragraph on err= and dirty= and lang=, which say
    nothing about how it looks. The client deck has paragraphs in 73 pieces
    that are all one format underneath.
    """
    def strip(run: str) -> str:
        rPr = RPR.search(run)
        return re.sub(r'\s(?:err|dirty|lang|smtClean)="[^"]*"', "", rPr.group(0)) if rPr else ""
    return len(set(strip(r) for r in runs)) == 1


def _one_run(old: str, runs: list[str], text: str) -> str:
    """The paragraph with every run replaced by one carrying `text`."""
    rPr = ""
    if runs:
        match = RPR.search(runs[0])
        # err= marks a spell-check squiggle on words that are gone now.
        rPr = re.sub(r'\s(?:err|dirty|smtClean)="[^"]*"', "", match.group(0)) if match else ""
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # PowerPoint drops a leading or trailing space without this.
    space = ' xml:space="preserve"' if text != text.strip() else ""
    run = f"<a:r>{rPr}<a:t{space}>{escaped}</a:t></a:r>"

    if not runs:  # an empty paragraph: put the run before endParaRPr
        return re.sub(r"(<a:endParaRPr\b|</a:p>)", run + r"\1", old, count=1)
    # Keep pPr and endParaRPr; the first run becomes the new one, the rest go.
    out = old.replace(runs[0], run, 1)
    for extra in runs[1:]:
        out = out.replace(extra, "", 1)
    return re.sub(r"<a:br\s*/>", "", out)


def delete_slide(deck: Path, slide: int) -> dict:
    """Take slide number `slide` out, with everything only it was using."""
    order = slide_parts(deck)
    if not 1 <= slide <= len(order):
        raise SystemExit(f"slide {slide} is outside 1..{len(order)}")
    if len(order) == 1:
        raise SystemExit("a presentation needs one slide; this is the last one")
    part = order[slide - 1]
    name = Path(part).name
    rels_part = f"ppt/slides/_rels/{name}.rels"

    with zipfile.ZipFile(deck) as z:
        mine = set(rels_of(z, part).values())
        drop = {part, rels_part} | _orphans(z, mine, keep_out=part)

    pres = read(deck, "ppt/presentation.xml")
    rid = re.search(rf'<Relationship[^>]*Target="slides/{re.escape(name)}"[^>]*/>',
                    read(deck, "ppt/_rels/presentation.xml.rels"))
    if rid is None:
        raise SystemExit(f"{name} has no relationship from the presentation")
    entry = _sld_id_entry(pres, re.search(r'Id="([^"]+)"', rid.group(0)).group(1))

    edit(deck, drop=drop, replace={
        "ppt/presentation.xml": pres.replace(entry, "", 1).encode("utf8"),
        "ppt/_rels/presentation.xml.rels": read(
            deck, "ppt/_rels/presentation.xml.rels").replace(rid.group(0), "", 1).encode("utf8"),
        "[Content_Types].xml": _drop_overrides(
            read(deck, "[Content_Types].xml"), drop).encode("utf8"),
    })
    return {"part": part, "also_removed": sorted(drop - {part, rels_part})}


def _orphans(z: zipfile.ZipFile, mine: set[str], keep_out: str) -> set[str]:
    """Parts this slide uses that nothing else will still be using.

    A notes page belongs to one slide and always goes. Media, charts and the
    rest are shared as often as not, so they go only when no other part still
    points at them -- dropping one that is still referenced is the commonest
    cause of the repair dialog there is.
    """
    others = set()
    for rels in (n for n in z.namelist() if n.endswith(".rels")):
        owner = rels.replace("/_rels/", "/").removesuffix(".rels")
        if owner == keep_out:
            continue
        others |= set(rels_of(z, owner).values())

    gone = set()
    for target in mine:
        if "slideLayouts/" in target or target in others:
            continue
        gone.add(target)
        nested = f"{Path(target).parent.as_posix()}/_rels/{Path(target).name}.rels"
        if nested in z.namelist():
            gone.add(nested)
    return gone


def _drop_overrides(ct: str, parts: set[str]) -> str:
    for part in parts:
        ct = re.sub(rf'<Override[^>]*PartName="/{re.escape(part)}"[^>]*/>', "", ct)
    return ct


def _sld_id_entry(pres: str, rid: str) -> str:
    for entry in SLD_ID.findall(pres):
        if f'r:id="{rid}"' in entry:
            return entry
    raise SystemExit(f"no <p:sldId> uses {rid}")


def move_slide(deck: Path, slide: int, to: int) -> dict:
    """Put slide number `slide` at position `to`, changing nothing else.

    The running order lives entirely in <p:sldIdLst>, so this rewrites one
    part and no slide at all.
    """
    pres = read(deck, "ppt/presentation.xml")
    entries = SLD_ID.findall(pres)
    if not 1 <= slide <= len(entries):
        raise SystemExit(f"slide {slide} is outside 1..{len(entries)}")
    if not 1 <= to <= len(entries):
        raise SystemExit(f"--to {to} is outside 1..{len(entries)}")
    if slide == to:
        return {"moved": False, "from": slide, "to": to}

    reordered = list(entries)
    reordered.insert(to - 1, reordered.pop(slide - 1))
    out, rest = [], pres
    for old, new in zip(entries, reordered):
        head, _, rest = rest.partition(old)
        out.append(head + new)
    edit(deck, replace={"ppt/presentation.xml": ("".join(out) + rest).encode("utf8")})
    return {"moved": True, "from": slide, "to": to}


def _layout_of(z: zipfile.ZipFile, slide: str | None) -> str:
    """The layout a neighbouring slide uses, so a new slide inherits it."""
    if slide is not None:
        for target in rels_of(z, slide).values():
            if "slideLayouts/" in target:
                return target
    layouts = sorted(n for n in z.namelist()
                     if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", n))
    if not layouts:
        raise SystemExit("this deck has no slide layout to bind a new slide to")
    return layouts[0]


def _slide_rels(source_rels: str | None, layout_part: str) -> str:
    """The new slide's .rels: its layout, plus whatever a clone also needs.

    A clone's notesSlide relationship is dropped. Two slides pointing at one
    notes page is a defect PowerPoint repairs, and it would also mean editing
    one slide's notes changed the other's.
    """
    target = "../" + layout_part.split("ppt/", 1)[1]
    if source_rels is None:
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
                f'<Relationships xmlns="{PKG_RELS}">'
                f'<Relationship Id="rId1" Type="{OFFDOC}/slideLayout" Target="{target}"/>'
                f"</Relationships>")
    return re.sub(r"<Relationship\b[^>]*?relationships/notesSlide[^>]*?/>", "", source_rels)


def _check_references(xml: bytes, rels: str) -> None:
    """Every r:id and r:embed the slide uses must exist in its .rels."""
    declared = set(re.findall(r'Id="([^"]+)"', rels))
    used = set(re.findall(rb'r:(?:id|embed|link)="([^"]+)"', xml))
    missing = {u.decode() for u in used} - declared
    if missing:
        raise SystemExit(
            f"the slide references {', '.join(sorted(missing))} but its .rels does not "
            f"declare them. PowerPoint repairs a deck with a dangling reference.")


def _insert_before(xml: str, close: str, fragment: str) -> str:
    if close not in xml:
        raise SystemExit(f"expected {close} in that part")
    return xml.replace(close, fragment + close, 1)


def _insert_sld_id(pres: str, sld_id: int, rid: str, after: int) -> str:
    """Put a <p:sldId/> into the presentation's own list, at `after`.

    Only <p:sldIdLst> is touched. A section list holds <p14:sldId> entries of
    its own, and writing into one of those would move the slide in the
    section pane and nowhere else.
    """
    lst = re.search(r"<p:sldIdLst\s*/>|<p:sldIdLst\b[^>]*>.*?</p:sldIdLst>", pres, re.S)
    if lst is None:
        raise SystemExit("this deck has no <p:sldIdLst>; it is not a presentation")
    entries = list(SLD_ID.finditer(lst.group(0)))
    # Match the dialect of the entry we sit next to: pandoc writes ` />`.
    close = " />" if entries and entries[0].group(0).endswith(" />") else "/>"
    new = f'<p:sldId id="{sld_id}" r:id="{rid}"{close}'

    if not entries:
        body = f"<p:sldIdLst>{new}</p:sldIdLst>"
    elif after == 0:
        body = lst.group(0)[:entries[0].start()] + new + lst.group(0)[entries[0].start():]
    else:
        at = entries[after - 1].end()
        body = lst.group(0)[:at] + new + lst.group(0)[at:]
    return pres[:lst.start()] + body + pres[lst.end():]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    dump = sub.add_parser("xml", help="print one slide's XML, to read or edit")
    dump.add_argument("deck", type=Path)
    dump.add_argument("slide", type=int)

    new = sub.add_parser("add", help="add a slide")
    new.add_argument("deck", type=Path)
    new.add_argument("xml", type=Path, nargs="?", help="a slide XML file to insert")
    new.add_argument("--clone", type=int, metavar="N", help="copy slide N instead")
    new.add_argument("--after", type=int, metavar="N", help="0 puts it first")
    new.add_argument("--layout", help="layout part to bind (default: the neighbour's)")

    edit_text = sub.add_parser("text", help="rewrite one paragraph, keeping its formatting")
    edit_text.add_argument("deck", type=Path)
    edit_text.add_argument("--slide", type=int, required=True)
    edit_text.add_argument("--shape", type=int, required=True,
                           help="cNvPr id, as inventory.json lists it")
    edit_text.add_argument("--para", type=int, default=0)
    edit_text.add_argument("text")
    edit_text.add_argument("--flatten", action="store_true",
                           help="accept losing the run-by-run formatting")

    gone = sub.add_parser("delete", help="remove a slide and anything only it used")
    gone.add_argument("deck", type=Path)
    gone.add_argument("slide", type=int)

    moved = sub.add_parser("move", help="put a slide at another position")
    moved.add_argument("deck", type=Path)
    moved.add_argument("slide", type=int)
    moved.add_argument("--to", type=int, required=True)

    args = ap.parse_args()
    if args.cmd == "delete":
        done = delete_slide(args.deck, args.slide)
        extra = f", with {', '.join(done['also_removed'])}" if done["also_removed"] else ""
        print(f"removed {done['part']}{extra}")
        return 0
    if args.cmd == "move":
        done = move_slide(args.deck, args.slide, to=args.to)
        print(f"slide {done['from']} is now slide {done['to']}" if done["moved"]
              else f"slide {args.slide} is already at {args.to}")
        return 0
    if args.cmd == "xml":
        order = slide_parts(args.deck)
        if not 1 <= args.slide <= len(order):
            raise SystemExit(f"slide {args.slide} is outside 1..{len(order)}")
        print(read(args.deck, order[args.slide - 1]))
        return 0

    if args.cmd == "text":
        done = set_text(args.deck, slide=args.slide, shape=args.shape, para=args.para,
                        text=args.text, flatten=args.flatten)
        print(f"slide {args.slide}, shape {args.shape}, paragraph {args.para}: "
              f"{done['text']!r}\nre-shoot the deck and look at it -- nothing here "
              f"can tell whether the new text still fits its box")
        return 0

    made = add_slide(args.deck, xml=args.xml.read_bytes() if args.xml else None,
                     clone=args.clone, after=args.after, layout=args.layout)
    source = f" from {made['cloned_from']}" if made["cloned_from"] else ""
    print(f"added {made['part']}{source} as slide {made['position']} "
          f"(sldId {made['sldId']}, {made['rId']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
