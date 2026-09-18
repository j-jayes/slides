"""Dump a .pptx as JSON: the handles an agent needs to edit it.

    python tools/pptx_inventory.py deck.pptx inventory.json
    python tools/pptx_inventory.py deck.pptx -          # to stdout

tools/pptx_to_md.py reads a deck for its words. This reads it for its
structure: every shape's id and geometry, the colours and fonts it actually
uses, the layouts and their placeholders, and each paragraph numbered the way
tools/pptx_edit.py addresses it.

The field that decides how a new slide gets authored is `kind`:

  template     the layouts carry placeholders -- build on them, and let
               colours come from the theme.
  free-shape   no placeholder anywhere, so there is nothing to build on.
               Copy a neighbouring slide and reuse its hex values; a
               schemeClr would resolve to whatever stock theme it carries.

Reads the package with zipfile and ElementTree, so it needs no python-pptx,
and it only ever reads: ET rewrites namespace prefixes on write, which is
fatal to a pptx.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from pptx_to_md import NS, rels_of, segments

A = f"{{{NS['a']}}}"
P = f"{{{NS['p']}}}"
R = f"{{{NS['r']}}}"

# The shape tags worth an entry. Anything else under spTree (grpSpPr and the
# group's own nvGrpSpPr) is scaffolding, not a shape.
KINDS = {"sp": "sp", "pic": "pic", "graphicFrame": "graphicFrame",
         "grpSp": "grpSp", "cxnSp": "cxnSp"}


def _first(el, *paths: str):
    """The first of `paths` that matches. An empty element is falsy, so the
    obvious `a or b` would skip past a <p:spPr/> that is there but bare."""
    for path in paths:
        found = el.find(path, NS) if el is not None else None
        if found is not None:
            return found
    return None


def geometry(spPr) -> dict:
    """Position, size and preset shape, where the shape states them."""
    out = {}
    off, ext = _first(spPr, "a:xfrm/a:off"), _first(spPr, "a:xfrm/a:ext")
    if off is not None and ext is not None:
        out["xywh"] = [int(off.get("x")), int(off.get("y")),
                       int(ext.get("cx")), int(ext.get("cy"))]
    geom = _first(spPr, "a:prstGeom")
    if geom is not None:
        out["geom"] = geom.get("prst")
    fill = _first(spPr, "a:solidFill")
    if fill is not None:
        out.update(colour_of(fill, "fill"))
    line = _first(spPr, "a:ln/a:solidFill")
    if line is not None:
        out.update(colour_of(line, "line"))
    return out


def colour_of(el, key: str) -> dict:
    """One solid fill, as either a hex value or the theme slot it points at."""
    srgb, scheme = _first(el, "a:srgbClr"), _first(el, "a:schemeClr")
    if srgb is not None:
        return {key: srgb.get("val")}
    if scheme is not None:
        return {key: f"scheme:{scheme.get('val')}"}
    return {}


def run_format(rPr) -> dict:
    """The formatting worth reporting, with the proofing noise stripped.

    Spell-checking fragments a paragraph into runs that differ only by err=
    and dirty=. Reporting those as distinct formats would mark almost every
    paragraph mixed, which is the one thing this field is for.
    """
    if rPr is None:
        return {}
    out = {}
    latin = _first(rPr, "a:latin")
    if latin is not None:
        out["typeface"] = latin.get("typeface")
    if rPr.get("sz"):
        out["sz"] = int(rPr.get("sz"))
    for attr in ("b", "i", "u"):
        if rPr.get(attr) in ("1", "true"):
            out[attr] = True
    fill = _first(rPr, "a:solidFill")
    if fill is not None:
        out.update(colour_of(fill, "color"))
    return out


def paragraph(para, i: int) -> dict:
    """One paragraph, numbered as pptx_edit.py addresses it.

    Every <a:p> counts, including the empty ones used as spacers: an index
    that skipped them would point an edit at the wrong paragraph.
    """
    ppr = _first(para, "a:pPr")
    formats = []
    for rPr in (r.find("a:rPr", NS) for r in para.findall("a:r", NS)):
        fmt = run_format(rPr)
        if fmt not in formats:
            formats.append(fmt)
    out = {
        "i": i,
        "text": "\n".join(segments(para)),
        "formats": formats,
        # An edit rewrites a paragraph as one run. Where the runs genuinely
        # differ -- a bold lead-in, then normal text -- that would lose the
        # distinction, so the edit refuses unless told to flatten.
        "mixed": len(formats) > 1,
    }
    if ppr is not None and ppr.get("lvl"):
        out["lvl"] = int(ppr.get("lvl"))
    return out


def shape(el, rels: dict[str, str]) -> dict:
    """One shape: what to call it, where it sits, and what it says."""
    tag = el.tag.split("}")[1]
    nv = _first(el, f"p:nv{'Grp' if tag == 'grpSp' else ''}SpPr/p:cNvPr")
    if nv is None:  # pic and graphicFrame name their wrapper differently
        nv = next((c for c in el.iter(f"{P}cNvPr")), None)
    out = {"id": int(nv.get("id")), "name": nv.get("name", ""), "kind": KINDS[tag]}

    ph = next((p for p in el.iter(f"{P}ph")), None)
    if ph is not None:
        out["ph"] = ph.get("type", "body")
    out.update(geometry(_first(el, "p:spPr", "p:grpSpPr")))

    blip = _first(el, ".//a:blip")
    if blip is not None:
        out["embeds"] = rels.get(blip.get(f"{R}embed"))
    if tag == "graphicFrame" and _first(el, ".//a:tbl") is not None:
        out["table"] = True
    if tag == "grpSp":
        out["shapes"] = [shape(c, rels) for c in el
                         if c.tag.split("}")[1] in KINDS]

    body = _first(el, "p:txBody", ".//a:txBody")
    if body is not None:
        out["paragraphs"] = [paragraph(p, i)
                             for i, p in enumerate(body.findall("a:p", NS))]
    return out


def layouts(z: zipfile.ZipFile) -> list[dict]:
    """Every layout, with the placeholders a new slide could be built on."""
    out = []
    for part in sorted(p for p in z.namelist()
                       if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", p)):
        root = ET.fromstring(z.read(part))
        cSld = root.find("p:cSld", NS)
        out.append({
            "part": part,
            "name": cSld.get("name", "") if cSld is not None else "",
            "type": root.get("type", ""),
            "placeholders": [ph.get("type", "body") for ph in root.iter(f"{P}ph")],
        })
    return out


def theme(z: zipfile.ZipFile) -> dict:
    """The theme the master binds: its fonts, and its colour slots."""
    part = next((p for p in sorted(z.namelist())
                 if re.fullmatch(r"ppt/theme/theme\d+\.xml", p)), None)
    if part is None:
        return {}
    root = ET.fromstring(z.read(part))
    scheme = _first(root, "a:themeElements/a:clrScheme")
    colours = {}
    for slot in scheme if scheme is not None else []:
        name = slot.tag.split("}")[1]
        srgb, sys_clr = _first(slot, "a:srgbClr"), _first(slot, "a:sysClr")
        if srgb is not None:
            colours[name] = srgb.get("val")
        elif sys_clr is not None:
            colours[name] = sys_clr.get("lastClr", sys_clr.get("val"))
    fonts = _first(root, "a:themeElements/a:fontScheme")
    major = _first(fonts, "a:majorFont/a:latin")
    minor = _first(fonts, "a:minorFont/a:latin")
    return {
        "name": root.get("name", ""),
        "major": major.get("typeface") if major is not None else "",
        "minor": minor.get("typeface") if minor is not None else "",
        "colours": colours,
    }


def notes_text(z: zipfile.ZipFile, slide: str) -> str | None:
    """The narration on this slide's notes page, if it has any."""
    for target in rels_of(z, slide).values():
        if "notesSlides/" in target:
            root = ET.fromstring(z.read(target))
            lines = []
            for sp in root.iter(f"{P}sp"):
                ph = _first(sp, ".//p:nvPr/p:ph")
                if ph is not None and ph.get("type") in {"sldNum", "hdr", "ftr", "dt", "sldImg"}:
                    continue
                lines.extend(segments(p) for p in sp.iter(f"{A}p"))
            text = "\n".join(line for group in lines for line in group)
            return text or None
    return None


def inventory(pptx: Path) -> dict:
    """Everything an agent needs to address and match this deck."""
    with zipfile.ZipFile(pptx) as z:
        pres = ET.fromstring(z.read("ppt/presentation.xml"))
        sz = pres.find("p:sldSz", NS)
        pres_rels = rels_of(z, "ppt/presentation.xml")
        lays = layouts(z)

        slides = []
        for i, (sld_id, part) in enumerate(
                ((int(s.get("id")), pres_rels[s.get(f"{R}id")])
                 for s in pres.iter(f"{P}sldId")), start=1):
            root = ET.fromstring(z.read(part))
            rels = rels_of(z, part)
            layout = next((lay["name"] for lay in lays
                           if lay["part"] in rels.values()), "")
            tree = root.find("p:cSld/p:spTree", NS)
            slides.append({
                "n": i,
                "sldId": sld_id,
                "part": part,
                "layout": layout,
                "shapes": [shape(c, rels) for c in tree
                           if c.tag.split("}")[1] in KINDS],
                "notes": notes_text(z, part),
            })

        # Counted over the slides only. The master and layouts of a generated
        # deck are often stock Office even when no slide uses the theme.
        xml = b"".join(z.read(s["part"]) for s in slides)
        return {
            "deck": pptx.name,
            "slide_size": [int(sz.get("cx")), int(sz.get("cy"))] if sz is not None else [],
            "kind": "template" if any(lay["placeholders"] for lay in lays) else "free-shape",
            "theme": theme(z),
            "colour_use": {"srgbClr": xml.count(b"<a:srgbClr"),
                           "schemeClr": xml.count(b"<a:schemeClr")},
            "layouts": lays,
            "slides": slides,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pptx", type=Path)
    ap.add_argument("out", type=Path, help="JSON file, or - for stdout")
    args = ap.parse_args()
    inv = inventory(args.pptx)
    text = json.dumps(inv, indent=2, ensure_ascii=False)
    if str(args.out) == "-":
        print(text)
    else:
        args.out.write_text(text, encoding="utf8")
        shapes = sum(len(s["shapes"]) for s in inv["slides"])
        print(f"wrote {args.out}: {len(inv['slides'])} slides, {shapes} shapes, "
              f"{inv['kind']}, {len(inv['layouts'])} layouts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
