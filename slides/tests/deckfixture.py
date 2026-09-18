"""Build a small but structurally honest .pptx in memory, for the deck tools.

    make_deck(path)                      # PowerPoint's XML dialect
    make_deck(path, dialect="pandoc")    # what Quarto writes

A colleague's deck cannot be committed, and the Quarto fixtures take minutes
to render, so the zip-surgery tools are pinned against a package written here.
What it reproduces is everything those tools index on and could get wrong:

  * relationship ids out of order and not matching slide numbers,
  * slide ids neither contiguous nor in file order,
  * notes slides with a relationship back to their own slide,
  * both XML dialects -- PowerPoint writes `standalone="yes"` and `<x/>`,
    pandoc writes neither and `<x />`, and a regex that only knows one of
    them passes the tests and breaks on a real deck.

It is valid as a package but not openable in PowerPoint: the theme and master
are stubs. Anything that needs a deck PowerPoint will open uses the rendered
Quarto fixtures instead.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
P = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFDOC = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
PML = "application/vnd.openxmlformats-officedocument.presentationml"
DML = "application/vnd.openxmlformats-officedocument"

# A 1x1 transparent GIF, small enough to inline and a real image to any reader.
GIF = bytes.fromhex("47494638396101000100800000000000ffffff21f90401000000002c000000000"
                    "10001000002024401003b")

# Slide ids, deliberately neither contiguous nor in file-name order: a deck
# hand-edited in PowerPoint looks like this, and "next id = count + 256" is
# the bug it catches.
SLD_IDS = [256, 271, 258]


class Dialect:
    """The two ways the same OOXML gets written."""

    def __init__(self, name: str):
        self.name = name
        self.pandoc = name == "pandoc"
        self.decl = ('<?xml version="1.0" encoding="UTF-8"?>' if self.pandoc
                     else '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n')
        self.close = " />" if self.pandoc else "/>"

    def part(self, xml: str) -> bytes:
        return (self.decl + xml.replace("/>", self.close)).encode("utf8")


def rels(d: Dialect, *pairs: tuple[str, str, str]) -> bytes:
    """(rId, type, target) triples, written in the order given."""
    body = "".join(
        f'<Relationship Id="{i}" Type="{OFFDOC}/{t}" Target="{target}"/>'
        for i, t, target in pairs)
    return d.part(f'<Relationships xmlns="{RELS}">{body}</Relationships>')


def sp(shape_id: int, name: str, paras: str, *, ph: str = "",
       xywh: tuple[int, int, int, int] = (838200, 365125, 10515600, 1325563),
       fill: str = "") -> str:
    """One text shape. `ph` makes it a placeholder, `fill` a solid srgbClr."""
    x, y, cx, cy = xywh
    nv_pr = f'<p:ph type="{ph}"/>' if ph else ""
    solid = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else ""
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/><p:cNvSpPr/>'
            f"<p:nvPr>{nv_pr}</p:nvPr></p:nvSpPr>"
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{solid}</p:spPr>'
            f"<p:txBody><a:bodyPr/><a:lstStyle/>{paras}</p:txBody></p:sp>")


def para(*runs: tuple[str, str], lvl: int = 0, bullet: bool = False) -> str:
    """(text, rPr-attributes) runs in one paragraph."""
    ppr = ""
    if bullet or lvl:
        ppr = f'<a:pPr lvl="{lvl}"><a:buChar char="-"/></a:pPr>'
    body = "".join(
        f'<a:r><a:rPr lang="sv-SE" {attrs}><a:latin typeface="Calibri"/></a:rPr>'
        f"<a:t>{text}</a:t></a:r>"
        for text, attrs in runs)
    return f"<a:p>{ppr}{body}</a:p>"


def pic(shape_id: int, name: str, rid: str) -> str:
    return (f'<p:pic><p:nvPicPr><p:cNvPr id="{shape_id}" name="{name}"/><p:cNvPicPr/>'
            f"<p:nvPr/></p:nvPicPr>"
            f'<p:blipFill><a:blip r:embed="{rid}"/></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="1000" y="2000"/><a:ext cx="3000" cy="4000"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')


def slide_xml(d: Dialect, *shapes: str) -> bytes:
    return d.part(f"<p:sld {A} {P} {R}><p:cSld><p:spTree>"
                  f'<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
                  f"<p:grpSpPr/>{''.join(shapes)}</p:spTree></p:cSld></p:sld>")


def _slides(d: Dialect, media: bool, placeholders: bool) -> list[list[str]]:
    """The three slides' shapes. Slide 2 carries the picture when asked."""
    title = "title" if placeholders else ""
    body = "body" if placeholders else ""
    one = [sp(2, "Title 1", para(("Opening", 'sz="4000" b="1"')), ph=title),
           sp(3, "Rectangle 3", para(("Stamped on", "")), fill="0F172A",
              xywh=(548640, 457200, 2000000, 500000))]
    two = [sp(2, "Title 2", para(("Second slide", 'sz="4000"')), ph=title),
           sp(4, "Content 4",
              para(("Lead-in: ", 'b="1"'), ("then the rest", ""), lvl=0, bullet=True)
              + para(("Nested", ""), lvl=1)
              + para(("Split", ""), ("", "")).replace("</a:r><a:r>", "</a:r><a:br/><a:r>"),
              ph=body)]
    if media:
        two.append(pic(5, "Picture 5", "rId3"))
    three = [sp(2, "Title 3", para(("Third slide", "")), ph=title)]
    return [one, two, three]


def make_deck(path: Path, *, dialect: str = "powerpoint", notes: bool = True,
              media: bool = False, placeholders: bool = True) -> Path:
    """Write a three-slide deck to `path` and return it."""
    d = Dialect(dialect)
    shapes = _slides(d, media, placeholders)
    # slideN.xml numbering runs opposite to presentation order, as a deck does
    # once slides have been reordered in PowerPoint.
    files = ["slide3.xml", "slide1.xml", "slide2.xml"]

    overrides = [
        ("/ppt/presentation.xml", f"{PML}.presentation.main+xml"),
        ("/ppt/slideMasters/slideMaster1.xml", f"{PML}.slideMaster+xml"),
        ("/ppt/slideLayouts/slideLayout1.xml", f"{PML}.slideLayout+xml"),
        ("/ppt/theme/theme1.xml", f"{DML}.theme+xml"),
    ]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        # Presentation. rIds are unordered and the master sits between slides,
        # so "the next id is the count plus one" is not a safe rule.
        pres_rels = [("rId7", "slideMaster", "slideMasters/slideMaster1.xml")]
        sld_lst = ""
        for i, (name, sid) in enumerate(zip(files, SLD_IDS)):
            rid = f"rId{[4, 2, 9][i]}"
            pres_rels.append((rid, "slide", f"slides/{name}"))
            sld_lst += f'<p:sldId id="{sid}" r:id="{rid}"/>'
        pres_rels.append(("rId8", "theme", "theme/theme1.xml"))
        z.writestr("ppt/_rels/presentation.xml.rels", rels(d, *pres_rels))
        z.writestr("ppt/presentation.xml", d.part(
            f"<p:presentation {A} {P} {R}>"
            f'<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId7"/></p:sldMasterIdLst>'
            f"<p:sldIdLst>{sld_lst}</p:sldIdLst>"
            f'<p:sldSz cx="12192000" cy="6858000"/><p:notesSz cx="6858000" cy="9144000"/>'
            f"</p:presentation>"))

        for i, name in enumerate(files, start=1):
            z.writestr(f"ppt/slides/{name}", slide_xml(d, *shapes[i - 1]))
            overrides.append((f"/ppt/slides/{name}", f"{PML}.slide+xml"))
            slide_rels = [("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml")]
            if notes:
                slide_rels.append(("rId2", "notesSlide", f"../notesSlides/notesSlide{i}.xml"))
            if media and name == files[1]:
                slide_rels.append(("rId3", "image", "../media/image1.gif"))
            z.writestr(f"ppt/slides/_rels/{name}.rels", rels(d, *slide_rels))

            if notes:
                z.writestr(f"ppt/notesSlides/notesSlide{i}.xml", d.part(
                    f"<p:notes {A} {P}><p:cSld><p:spTree>"
                    + sp(2, f"Notes {i}", para((f"Narration for {name}", "")))
                    + "</p:spTree></p:cSld></p:notes>"))
                # The notes slide points back at its own slide. Deleting one
                # without the other leaves a dangling target.
                z.writestr(f"ppt/notesSlides/_rels/notesSlide{i}.xml.rels",
                           rels(d, ("rId1", "slide", f"../slides/{name}")))
                overrides.append((f"/ppt/notesSlides/notesSlide{i}.xml", f"{PML}.notesSlide+xml"))

        if media:
            z.writestr("ppt/media/image1.gif", GIF)

        ph_xml = ""
        if placeholders:
            ph_xml = (sp(2, "Title Placeholder 1", para(("", "")), ph="title")
                      + sp(3, "Text Placeholder 2", para(("", "")), ph="body"))
        z.writestr("ppt/slideLayouts/slideLayout1.xml", d.part(
            f'<p:sldLayout {A} {P} {R} type="titleOnly"><p:cSld name="Title and Content">'
            f"<p:spTree>{ph_xml}</p:spTree></p:cSld></p:sldLayout>"))
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels",
                   rels(d, ("rId1", "slideMaster", "../slideMasters/slideMaster1.xml")))
        z.writestr("ppt/slideMasters/slideMaster1.xml", d.part(
            f"<p:sldMaster {A} {P} {R}><p:cSld><p:spTree/></p:cSld>"
            f'<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
            f"</p:sldMaster>"))
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", rels(
            d, ("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml"),
            ("rId2", "theme", "../theme/theme1.xml")))
        z.writestr("ppt/theme/theme1.xml", d.part(
            f'<a:theme {A} name="Fixture Theme"><a:themeElements>'
            f'<a:clrScheme name="Fixture"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>'
            f'<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>'
            f'<a:dk2><a:srgbClr val="44546A"/></a:dk2><a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>'
            + "".join(f'<a:accent{i}><a:srgbClr val="{h}"/></a:accent{i}>' for i, h in
                      enumerate(["4472C4", "ED7D31", "A5A5A5", "FFC000", "5B9BD5", "70AD47"], 1))
            + f'<a:hlink><a:srgbClr val="0563C1"/></a:hlink>'
            f'<a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme>'
            f'<a:fontScheme name="Fixture"><a:majorFont><a:latin typeface="Cambria"/></a:majorFont>'
            f'<a:minorFont><a:latin typeface="Calibri"/></a:minorFont></a:fontScheme>'
            f"<a:fmtScheme/></a:themeElements></a:theme>"))

        defaults = [("rels", f"application/vnd.openxmlformats-package.relationships+xml"),
                    ("xml", "application/xml")]
        if media:
            defaults.append(("gif", "image/gif"))
        z.writestr("[Content_Types].xml", d.part(
            f'<Types xmlns="{CT}">'
            + "".join(f'<Default Extension="{e}" ContentType="{c}"/>' for e, c in defaults)
            + "".join(f'<Override PartName="{p}" ContentType="{c}"/>' for p, c in overrides)
            + "</Types>"))
        z.writestr("_rels/.rels", rels(
            d, ("rId1", "officeDocument", "ppt/presentation.xml")))
    return path
