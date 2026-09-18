"""Dump a .pptx to Markdown: every slide's text, tables, pictures and notes.

    python tools/pptx_to_md.py deck.pptx out.md            # pictures go to <out dir>/assets/
    python tools/pptx_to_md.py deck.pptx out.md --assets pics

Reads the package directly with zipfile, so it needs no python-pptx. Slides
come out in presentation order (from presentation.xml, not file names), each
as a `##` heading carrying its number and layout name, then one block per
text shape in z-order, tables as Markdown tables, and the notes page under a
**Notes** label. Bullet levels are kept as nested list indentation.
"""
from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def rels_of(z: zipfile.ZipFile, part: str) -> dict[str, str]:
    """rId -> target path (package-absolute) for one part."""
    p = Path(part)
    rels_part = f"{p.parent.as_posix()}/_rels/{p.name}.rels"
    if rels_part not in z.namelist():
        return {}
    out = {}
    for rel in ET.fromstring(z.read(rels_part)).iter(f"{REL_NS}Relationship"):
        target = rel.get("Target")
        if rel.get("TargetMode") == "External":
            out[rel.get("Id")] = target
            continue
        out[rel.get("Id")] = _join(p.parent.as_posix(), target)
    return out


def _join(base: str, target: str) -> str:
    parts = base.split("/") if base else []
    for seg in target.split("/"):
        if seg == "..":
            parts.pop()
        elif seg and seg != ".":
            parts.append(seg)
    return "/".join(parts)


def slides_in_order(z: zipfile.ZipFile) -> list[str]:
    pres = ET.fromstring(z.read("ppt/presentation.xml"))
    rels = rels_of(z, "ppt/presentation.xml")
    return [rels[s.get(f"{{{NS['r']}}}id")] for s in pres.iter(f"{{{NS['p']}}}sldId")]


def layout_name(z: zipfile.ZipFile, slide: str) -> str:
    for target in rels_of(z, slide).values():
        if "slideLayouts/" in target:
            m = re.search(r'<p:cSld[^>]*name="([^"]*)"', z.read(target).decode("utf8", "ignore"))
            return m.group(1) if m else ""
    return ""


def segments(para) -> list[str]:
    """The paragraph's text, split at every <a:br/>.

    A break is how one paragraph carries a second line -- a subtitle under a
    title, an author under that. iter() walks in document order, so runs and
    breaks interleave the way they are written.
    """
    segs = [""]
    for el in para.iter():
        tag = el.tag.split("}")[1]
        if tag == "br":
            segs.append("")
        elif tag == "t":
            segs[-1] += el.text or ""
    return [s for s in (seg.strip() for seg in segs) if s]


def paragraphs(el) -> list[str]:
    """Text of every non-empty paragraph under `el`, as Markdown lines."""
    lines = []
    for para in el.iter(f"{{{NS['a']}}}p"):
        segs = segments(para)
        if not segs:
            continue
        ppr = para.find("a:pPr", NS)
        lvl = int(ppr.get("lvl", "0")) if ppr is not None else 0
        bulleted = ppr is not None and ppr.find("a:buNone", NS) is None and (
            lvl > 0 or ppr.find("a:buChar", NS) is not None or ppr.find("a:buAutoNum", NS) is not None
        )
        first = ("  " * lvl + "- ") if bulleted else ""
        lines.append(first + segs[0])
        # Continuation lines sit under the bullet text, which is what keeps
        # them part of the same list item in Markdown.
        lines.extend(" " * len(first) + seg for seg in segs[1:])
    return lines


def shape_blocks(z: zipfile.ZipFile, slide: str, assets: Path, md_dir: Path) -> list[str]:
    root = ET.fromstring(z.read(slide))
    rels = rels_of(z, slide)
    blocks = []
    tree = root.find("p:cSld/p:spTree", NS)
    for child in tree:
        tag = child.tag.split("}")[1]
        if tag == "sp":
            name = child.find("p:nvSpPr/p:cNvPr", NS).get("name", "")
            lines = paragraphs(child)
            if lines:
                blocks.append(f"<!-- {name} -->\n" + "\n".join(lines))
        elif tag == "graphicFrame":
            tbl = child.find(".//a:tbl", NS)
            if tbl is None:
                continue
            rows = []
            for tr in tbl.iter(f"{{{NS['a']}}}tr"):
                cells = [" ".join(paragraphs(tc)).replace("|", "\\|") for tc in tr.findall("a:tc", NS)]
                rows.append("| " + " | ".join(cells) + " |")
            if rows:
                header, *body = rows
                sep = "|" + "---|" * (header.count("|") - 1)
                blocks.append("\n".join([header, sep, *body]))
        elif tag == "pic":
            name = child.find("p:nvPicPr/p:cNvPr", NS).get("name", "")
            blip = child.find(".//a:blip", NS)
            rid = blip.get(f"{{{NS['r']}}}embed") if blip is not None else None
            target = rels.get(rid)
            if not target:
                continue
            slide_no = re.search(r"slide(\d+)", slide).group(1)
            dest = assets / f"slide{slide_no}-{Path(target).name}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(target))
            rel = dest.relative_to(md_dir).as_posix()
            blocks.append(f"![{name}]({rel})")
    return blocks


def notes_lines(z: zipfile.ZipFile, slide: str) -> list[str]:
    for target in rels_of(z, slide).values():
        if "notesSlides/" in target:
            root = ET.fromstring(z.read(target))
            out = []
            for sp in root.iter(f"{{{NS['p']}}}sp"):
                ph = sp.find(".//p:nvPr/p:ph", NS)
                if ph is not None and ph.get("type") in {"sldNum", "hdr", "ftr", "dt", "sldImg"}:
                    continue
                out.extend(paragraphs(sp))
            return out
    return []


def convert(pptx: Path, out: Path, assets: Path) -> tuple[int, int]:
    z = zipfile.ZipFile(pptx)
    slides = slides_in_order(z)
    md = [f"# {pptx.name}", "", f"Extracted with `tools/pptx_to_md.py` from `{pptx.name}` "
          f"({len(slides)} slides). Text is verbatim; `<!-- -->` comments name the source shape.", ""]
    with_notes = 0
    for i, slide in enumerate(slides, 1):
        md.append(f"## Slide {i} — layout: {layout_name(z, slide)}")
        md.append("")
        blocks = shape_blocks(z, slide, assets, out.parent)
        md.append("\n\n".join(blocks) if blocks else "_(no text on slide)_")
        md.append("")
        notes = notes_lines(z, slide)
        if notes:
            with_notes += 1
            md.append("**Notes:**")
            md.append("")
            md.extend(notes)
            md.append("")
    out.write_text("\n".join(md), encoding="utf8")
    return len(slides), with_notes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pptx", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--assets", type=Path, help="directory for extracted pictures (default: <out dir>/assets)")
    args = ap.parse_args()
    assets = args.assets or args.out.parent / "assets"
    n, with_notes = convert(args.pptx, args.out, assets)
    print(f"wrote {args.out}: {n} slides, {with_notes} with notes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
