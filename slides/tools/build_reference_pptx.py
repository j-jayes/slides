"""Build _extensions/nexer/nexer-reference.pptx -- the reference-doc Quarto uses for pptx.

_brand.yml does not reach PowerPoint; pandoc styles pptx from a reference doc
whose layouts it matches BY NAME. So this takes the real Nexer corporate deck,
keeps its theme, master, logo and artwork, throws away everything else, and
renames/retypes seven layouts into the names pandoc looks for.

The one thing that cannot be reused as-is: no Nexer layout has a
`<p:ph type="title"/>`. What looks like a title is a `type="body"` placeholder.
Without a real title placeholder pandoc emits an empty `<p:sp/>` per slide,
which corrupts the file. Retyping that placeholder is the core of this script.

    python tools/build_reference_pptx.py            # build
    python tools/build_reference_pptx.py --verify   # build + assert

Deliberately stdlib zipfile + targeted string edits on the decoded XML, so every
byte we do not touch is preserved exactly as PowerPoint wrote it.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "temp" / "Sales presentation 2026.pptx"
OUT = ROOT / "_extensions" / "nexer" / "nexer-reference.pptx"
SWIRL = ROOT / "assets" / "swirl-dark.jpg"
BLACK_LOGO = ROOT / "assets" / "nexer-logo.png"
# Full-bleed swirl artwork on the two dark layouts: 1.3 MB and 0.9 MB of PNG
# for what the Reveal deck already carries as a 62 KB JPEG.
SWIRL_PNGS = {"image12.png", "image15.png"}

# The corporate deck is not tracked in this repo, so this script only runs when
# a copy has been placed under temp/.
MISSING_DECK = """source deck not found: {deck}

The corporate deck is not kept in this repo -- it is ~90 MB and only needed to
rebuild the reference template. Put a copy at

  temp/Sales presentation 2026.pptx

and re-run. nexer-reference.pptx is committed, so you only need this when the
corporate deck itself changes."""

# Nexer's master2 ("Dark background" in docProps/app.xml) owns layouts 20-39 and
# theme2, and is the only master with a full one/two/three-column family.
SRC_MASTER = 2
SRC_THEME = 2
MASTER_LOGO_RID = "rId22"   # -> ../media/image1.emf, the white wordmark

# Nexer's theme is built for white-on-black, so its <a:hlink> is #FFFFFF. On
# the light master built below that makes every link in a deck white on white:
# the text is in the file and invisible on the slide. _brand.yml sets the link
# colour to the Nexer purple, so match it, with the lighter purple for
# followed links.
LINK, FOLLOWED_LINK = "5A1F9F", "AA4BF4"

# (output index, <p:cSld name>, source layout, tone)
#
# The first seven names are what pandoc looks up. The last four are not
# pandoc-addressable but keep the deck pleasant to extend by hand -- and pad the
# count to 11 so none of pandoc's own default layouts leak into the output.
LAYOUTS = [
    (1, "Title Slide", 21, "dark"),
    (2, "Title and Content", 28, "light"),
    (3, "Section Header", 23, "dark"),
    (4, "Two Content", 34, "light"),
    (5, "Comparison", 34, "light"),
    (6, "Content with Caption", 28, "light"),
    (7, "Blank", 27, "light"),
    (8, "Statement", 26, "dark"),
    (9, "Title, Three column", 35, "light"),
    (10, "Title, One column, image right", 32, "light"),
    (11, "Title, One column, image left", 33, "light"),
]

# Slide canvas is 12192000 x 6858000 EMU. Nexer's own content margin is 838200.
MARGIN = 838200
FULL_W = 10515600
TITLE_Y, TITLE_H = 655469, 906293
BODY_Y = 1822267
BODY_H = 4352400
COL_W = 5040000
COL_R_X = 6313800

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\
<Default Extension="xml" ContentType="application/xml"/>\
<Default Extension="png" ContentType="image/png"/>\
<Default Extension="jpeg" ContentType="image/jpeg"/>\
<Default Extension="jpg" ContentType="image/jpeg"/>\
<Default Extension="emf" ContentType="image/x-emf"/>\
<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>\
<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>\
{layout_overrides}\
<Override PartName="/ppt/notesMasters/notesMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"/>\
<Override PartName="/ppt/presProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presProps+xml"/>\
<Override PartName="/ppt/viewProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml"/>\
<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>\
<Override PartName="/ppt/theme/theme2.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>\
<Override PartName="/ppt/tableStyles.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml"/>\
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>\
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>\
</Types>"""

PRESENTATION_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>\
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster" Target="notesMasters/notesMaster1.xml"/>\
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps" Target="presProps.xml"/>\
<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/viewProps" Target="viewProps.xml"/>\
<Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>\
<Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/tableStyles" Target="tableStyles.xml"/>\
</Relationships>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>"""

APP_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" \
xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">\
<Application>Microsoft Office PowerPoint</Application><PresentationFormat>Widescreen</PresentationFormat>\
<Slides>0</Slides><Company>Nexer</Company><AppVersion>16.0000</AppVersion></Properties>"""


# --------------------------------------------------------------------------- #
# XML helpers -- targeted string edits, so untouched bytes stay byte-identical
# --------------------------------------------------------------------------- #

def set_layout_name(xml: str, name: str) -> str:
    return re.sub(r'(<p:cSld[^>]*?)name="[^"]*"', rf'\1name="{name}"', xml, count=1)


def ensure_layout_name(xml: str, name: str) -> str:
    """Layouts without a name attribute need one adding."""
    if re.search(r"<p:cSld[^>]*name=", xml):
        return set_layout_name(xml, name)
    return xml.replace("<p:cSld>", f'<p:cSld name="{name}">', 1)


def retype_ph(xml: str, idx: int, new_ph: str) -> str:
    """Replace the <p:ph .../> carrying this idx with new_ph."""
    pattern = re.compile(r'<p:ph\b[^>]*\bidx="%d"[^>]*/>' % idx)
    out, n = pattern.subn(new_ph, xml, count=1)
    if n != 1:
        raise ValueError(f"no placeholder idx={idx} to retype")
    return out


def drop_ph_shapes(xml: str) -> str:
    """Remove every <p:sp> that holds a placeholder, keeping decorations."""
    def keep(m: re.Match) -> str:
        return "" if "<p:ph" in m.group(0) else m.group(0)

    return re.sub(r"<p:sp>.*?</p:sp>", keep, xml, flags=re.S)


def append_shapes(xml: str, shapes: str) -> str:
    return xml.replace("</p:spTree>", shapes + "</p:spTree>", 1)


def make_ph_shape(shape_id: int, name: str, ph: str, x: int, y: int,
                  cx: int, cy: int, lst: str = "", prompt: str = "") -> str:
    """A placeholder <p:sp> with explicit geometry.

    Geometry is not optional: pandoc gives the generated slide shape an empty
    <p:spPr>, so it inherits size from the layout. Without <a:xfrm> here,
    getContentShapeSize throws and images fall back to full-page.
    """
    body = (
        f'<a:p><a:r><a:rPr lang="en-US" dirty="0"/><a:t>{prompt}</a:t></a:r></a:p>'
        if prompt else "<a:p><a:endParaRPr lang=\"en-US\"/></a:p>"
    )
    return (
        f"<p:sp><p:nvSpPr><p:cNvPr id=\"{shape_id}\" name=\"{name}\"/>"
        f'<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr>{ph}</p:nvPr></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm></p:spPr>'
        f'<p:txBody><a:bodyPr><a:normAutofit/></a:bodyPr><a:lstStyle>{lst}</a:lstStyle>{body}</p:txBody></p:sp>'
    )


# Action-title styling for light layouts: Nexer's own title is 44pt ALL CAPS,
# which is a section-divider look. A content slide's title is the takeaway
# sentence, so it wants sentence case at a size that fits ~20 words.
TITLE_LST_LIGHT = (
    '<a:lvl1pPr algn="l"><a:defRPr sz="2600" b="0" cap="none" spc="-30">'
    '<a:solidFill><a:schemeClr val="tx1"/></a:solidFill>'
    '<a:latin typeface="+mj-lt"/></a:defRPr></a:lvl1pPr>'
)
BODY_LST_LIGHT = (
    '<a:lvl1pPr algn="l"><a:defRPr sz="1800" b="1">'
    '<a:solidFill><a:schemeClr val="tx1"/></a:solidFill>'
    '<a:latin typeface="+mn-lt"/></a:defRPr></a:lvl1pPr>'
)


def to_light(xml: str) -> str:
    """Flip a layout from Nexer's white-on-black to black-on-white.

    Order matters: recolour the text first, then the background. Doing it the
    other way round makes the background bg1 and the very next substitution
    turns that same fill back to tx1.
    """
    head, sep, rest = xml.partition("</p:bg>")
    if not sep:                       # layout inherits the master background
        head, sep, rest = "", "", xml
    # Placeholder text in these layouts is explicitly white; make it ink.
    rest = rest.replace(
        '<a:solidFill><a:schemeClr val="bg1"/></a:solidFill>',
        '<a:solidFill><a:schemeClr val="tx1"/></a:solidFill>',
    )
    head = head.replace(
        '<p:bg><p:bgPr><a:solidFill><a:schemeClr val="tx1"/>',
        '<p:bg><p:bgPr><a:solidFill><a:schemeClr val="bg1"/>',
    )
    return head + sep + rest


def restyle_title(xml: str) -> str:
    """Give the retyped title the action-title treatment on light layouts."""
    return re.sub(
        r'(<p:ph type="title"/></p:nvPr></p:nvSpPr>.*?<a:lstStyle>)(.*?)(</a:lstStyle>)',
        lambda m: m.group(1) + TITLE_LST_LIGHT + m.group(3),
        xml,
        count=1,
        flags=re.S,
    )


# --------------------------------------------------------------------------- #
# Per-layout transforms
# --------------------------------------------------------------------------- #

def build_layout(xml: str, name: str, tone: str) -> str:
    """Turn one Nexer layout into a pandoc-addressable one."""
    if tone == "light":
        xml = to_light(xml)

    if name == "Title Slide":
        # ctrTitle, subTitle, and a dt placeholder. The dt is not optional:
        # the master sets <p:hf dt="0"/>, so pandoc's fiDate is Nothing, and
        # any `date:` in YAML makes it emit an empty <p:sp/> unless dt exists.
        xml = retype_ph(xml, 10, '<p:ph type="ctrTitle"/>')
        xml = retype_ph(xml, 12, '<p:ph type="subTitle" idx="1"/>')
        # Nexer's own title is 60pt ALL CAPS with <a:noAutofit/>, sized for the
        # two-word headings in their deck. A real deck title is longer and runs
        # off the canvas, so shrink the base size and let it autofit.
        xml = xml.replace("<a:noAutofit/>", "<a:normAutofit/>")
        xml = re.sub(r'(<p:ph type="ctrTitle"/>.*?<a:defRPr[^>]*?)sz="\d+"',
                     r'\g<1>sz="4000"', xml, count=1, flags=re.S)
        xml = append_shapes(xml, make_ph_shape(
            90, "Date Placeholder 90", '<p:ph type="dt" sz="half" idx="10"/>',
            MARGIN, 6250000, 6552414, 330000,
            '<a:lvl1pPr algn="l"><a:defRPr sz="1200">'
            '<a:solidFill><a:schemeClr val="bg1"/></a:solidFill></a:defRPr></a:lvl1pPr>',
        ))

    elif name == "Section Header":
        # Pandoc only fills the title here; idx 12 stays a body for hand use.
        xml = retype_ph(xml, 10, '<p:ph type="title"/>')

    elif name == "Title and Content":
        # idx 11 is already untyped, which is exactly pandoc's ObjType[0].
        xml = retype_ph(xml, 10, '<p:ph type="title"/>')
        xml = restyle_title(xml)

    elif name == "Two Content":
        xml = retype_ph(xml, 11, '<p:ph type="title"/>')
        xml = restyle_title(xml)

    elif name == "Comparison":
        # pandoc wants title, body[0], ObjType[0], body[1], ObjType[1] in
        # spTree document order -- it counts position, not idx. Rebuild the
        # placeholders wholesale so the order is unambiguous.
        xml = drop_ph_shapes(xml)
        head_h = 500000
        content_y = BODY_Y + head_h + 80000
        content_h = BODY_Y + BODY_H - content_y
        shapes = (
            make_ph_shape(10, "Title 1", '<p:ph type="title"/>',
                          MARGIN, TITLE_Y, FULL_W, TITLE_H, TITLE_LST_LIGHT)
            + make_ph_shape(11, "Text Placeholder 2", '<p:ph type="body" idx="12"/>',
                            MARGIN, BODY_Y, COL_W, head_h, BODY_LST_LIGHT)
            + make_ph_shape(12, "Content Placeholder 3", '<p:ph sz="quarter" idx="13"/>',
                            MARGIN, content_y, COL_W, content_h)
            + make_ph_shape(13, "Text Placeholder 4", '<p:ph type="body" idx="14"/>',
                            COL_R_X, BODY_Y, COL_W, head_h, BODY_LST_LIGHT)
            + make_ph_shape(14, "Content Placeholder 5", '<p:ph sz="quarter" idx="15"/>',
                            COL_R_X, content_y, COL_W, content_h)
        )
        xml = append_shapes(xml, shapes)

    elif name == "Content with Caption":
        # Fires on any slide that is text then a table/figure -- the common
        # case in a data deck. Stacked, not image-right: a side split cannot
        # hold a wide table.
        xml = drop_ph_shapes(xml)
        cap_h = 800000
        content_y = BODY_Y + cap_h + 80000
        content_h = BODY_Y + BODY_H - content_y
        shapes = (
            make_ph_shape(10, "Title 1", '<p:ph type="title"/>',
                          MARGIN, TITLE_Y, FULL_W, TITLE_H, TITLE_LST_LIGHT)
            + make_ph_shape(11, "Text Placeholder 2", '<p:ph type="body" idx="14"/>',
                            MARGIN, BODY_Y, FULL_W, cap_h,
                            '<a:lvl1pPr algn="l"><a:defRPr sz="1600">'
                            '<a:solidFill><a:schemeClr val="tx1"/></a:solidFill>'
                            '</a:defRPr></a:lvl1pPr>')
            + make_ph_shape(12, "Content Placeholder 3", '<p:ph sz="quarter" idx="11"/>',
                            MARGIN, content_y, FULL_W, content_h)
        )
        xml = append_shapes(xml, shapes)

    elif name == "Title, Three column":
        xml = retype_ph(xml, 12, '<p:ph type="title"/>')
        xml = restyle_title(xml)

    elif name in ("Title, One column, image right", "Title, One column, image left"):
        title_idx = 10 if "right" in name else 12
        xml = retype_ph(xml, title_idx, '<p:ph type="title"/>')
        xml = restyle_title(xml)

    if tone == "dark":
        # These carry their own white logo; suppress the master's black one.
        xml = re.sub(r"<p:sldLayout(?![^>]*showMasterSp)",
                     '<p:sldLayout showMasterSp="0"', xml, count=1)

    # "Blank" and "Statement" need no placeholder surgery.
    return ensure_layout_name(xml, name)


def build_master(xml: str, layout_rids: list[str]) -> str:
    """Flip the master to light and point it at exactly our 11 layouts."""
    xml = xml.replace(
        '<p:bg><p:bgPr><a:solidFill><a:schemeClr val="tx1"/>',
        '<p:bg><p:bgPr><a:solidFill><a:schemeClr val="bg1"/>',
    )
    # txStyles: white text -> ink; invisible grey bullets -> Nexer purple.
    head, sep, styles = xml.partition("<p:txStyles>")
    styles = styles.replace(
        '<a:solidFill><a:schemeClr val="bg1"/></a:solidFill>',
        '<a:solidFill><a:schemeClr val="tx1"/></a:solidFill>',
    )
    styles = styles.replace('<a:buClr><a:schemeClr val="bg2"/></a:buClr>',
                            '<a:buClr><a:schemeClr val="tx2"/></a:buClr>')
    styles = styles.replace('<a:buClr><a:schemeClr val="accent4"/></a:buClr>',
                            '<a:buClr><a:schemeClr val="tx2"/></a:buClr>')
    xml = head + sep + styles

    # The master's logo is the white wordmark, invisible now the master is
    # light. Repoint it at the black one; the dark layouts carry their own
    # white logo and suppress master shapes.
    xml = xml.replace(f'r:embed="{MASTER_LOGO_RID}"', 'r:embed="rIdLogo"')

    entries = "".join(
        f'<p:sldLayoutId id="{2147484000 + i}" r:id="{rid}"/>'
        for i, rid in enumerate(layout_rids, start=1)
    )
    return re.sub(
        r"<p:sldLayoutIdLst>.*?</p:sldLayoutIdLst>",
        f"<p:sldLayoutIdLst>{entries}</p:sldLayoutIdLst>",
        xml,
        flags=re.S,
    )


def build_presentation(xml: str) -> str:
    xml = re.sub(r"<p:sldMasterIdLst>.*?</p:sldMasterIdLst>",
                 '<p:sldMasterIdLst><p:sldMasterId id="2147484125" r:id="rId1"/></p:sldMasterIdLst>',
                 xml, flags=re.S)
    xml = re.sub(r"<p:notesMasterIdLst>.*?</p:notesMasterIdLst>",
                 '<p:notesMasterIdLst><p:notesMasterId r:id="rId2"/></p:notesMasterIdLst>',
                 xml, flags=re.S)
    xml = re.sub(r"<p:handoutMasterIdLst>.*?</p:handoutMasterIdLst>", "", xml, flags=re.S)
    xml = re.sub(r"<p:sldIdLst>.*?</p:sldIdLst>", "<p:sldIdLst/>", xml, flags=re.S)
    # Embedded fonts must go: pandoc copies ppt/fonts/* into every output but
    # cannot emit a content type for .fntdata, leaving an undeclared OPC part
    # and a repair prompt. Bw Gradual / FK Grotesk are installed on Nexer
    # machines, so the theme resolves them natively anyway.
    xml = re.sub(r"<p:embeddedFontLst>.*?</p:embeddedFontLst>", "", xml, flags=re.S)
    return xml


def fix_theme_links(xml: str) -> str:
    """Recolour the theme's hyperlink pair for a light master. See LINK."""
    return re.sub(
        r"<a:hlink><a:srgbClr val=\"[0-9A-Fa-f]{6}\"/></a:hlink>"
        r"<a:folHlink><a:srgbClr val=\"[0-9A-Fa-f]{6}\"/></a:folHlink>",
        f'<a:hlink><a:srgbClr val="{LINK}"/></a:hlink>'
        f'<a:folHlink><a:srgbClr val="{FOLLOWED_LINK}"/></a:folHlink>',
        xml, count=1)


def rels_for_layout(src_rels: str) -> str:
    """Repoint a layout's rels at slideMaster1 and drop dangling targets."""
    return re.sub(r'Target="\.\./slideMasters/slideMaster\d+\.xml"',
                  'Target="../slideMasters/slideMaster1.xml"', src_rels)


def build() -> None:
    if not SRC.exists():
        sys.exit(MISSING_DECK.format(deck=SRC))

    zin = zipfile.ZipFile(SRC)
    parts: dict[str, bytes] = {}
    media: set[str] = set()

    # --- layouts -----------------------------------------------------------
    layout_rids = []
    for out_i, name, src_i, tone in LAYOUTS:
        xml = zin.read(f"ppt/slideLayouts/slideLayout{src_i}.xml").decode("utf8")
        xml = build_layout(xml, name, tone)
        parts[f"ppt/slideLayouts/slideLayout{out_i}.xml"] = xml.encode("utf8")

        rels = zin.read(f"ppt/slideLayouts/_rels/slideLayout{src_i}.xml.rels").decode("utf8")
        rels = rels_for_layout(rels)
        for png in SWIRL_PNGS:
            rels = rels.replace(f"../media/{png}", f"../media/{Path(png).stem}.jpg")
        # Keep only media still referenced by the (possibly rebuilt) layout.
        for m in re.finditer(r'Id="([^"]+)"[^>]*Target="\.\./media/([^"]+)"', rels):
            if m.group(1) in xml:
                media.add(m.group(2))
            else:
                rels = re.sub(r'<Relationship Id="%s".*?/>' % m.group(1), "", rels)
        parts[f"ppt/slideLayouts/_rels/slideLayout{out_i}.xml.rels"] = rels.encode("utf8")
        layout_rids.append(f"rId{out_i}")

    # --- master ------------------------------------------------------------
    master = zin.read(f"ppt/slideMasters/slideMaster{SRC_MASTER}.xml").decode("utf8")
    parts["ppt/slideMasters/slideMaster1.xml"] = build_master(master, layout_rids).encode("utf8")
    master_rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    for out_i, *_ in LAYOUTS:
        master_rels.append(
            f'<Relationship Id="rId{out_i}" Type="http://schemas.openxmlformats.org/'
            f'officeDocument/2006/relationships/slideLayout" '
            f'Target="../slideLayouts/slideLayout{out_i}.xml"/>')
    master_rels.append(
        f'<Relationship Id="rId{len(LAYOUTS) + 1}" Type="http://schemas.openxmlformats.org/'
        f'officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>')
    master_rels.append(
        '<Relationship Id="rIdLogo" Type="http://schemas.openxmlformats.org/'
        'officeDocument/2006/relationships/image" Target="../media/image200.png"/>')
    master_rels.append("</Relationships>")
    parts["ppt/slideMasters/_rels/slideMaster1.xml.rels"] = "".join(master_rels).encode("utf8")

    # --- themes ------------------------------------------------------------
    parts["ppt/theme/theme1.xml"] = fix_theme_links(
        zin.read(f"ppt/theme/theme{SRC_THEME}.xml").decode("utf8")).encode("utf8")
    notes_rels = zin.read("ppt/notesMasters/_rels/notesMaster1.xml.rels").decode("utf8")
    notes_theme = re.search(r"theme/(theme\d+\.xml)", notes_rels).group(1)
    parts["ppt/theme/theme2.xml"] = zin.read(f"ppt/theme/{notes_theme}")
    parts["ppt/notesMasters/notesMaster1.xml"] = zin.read("ppt/notesMasters/notesMaster1.xml")
    parts["ppt/notesMasters/_rels/notesMaster1.xml.rels"] = re.sub(
        r"theme/theme\d+\.xml", "theme/theme2.xml", notes_rels).encode("utf8")

    # --- presentation and package indexes ----------------------------------
    parts["ppt/presentation.xml"] = build_presentation(
        zin.read("ppt/presentation.xml").decode("utf8")).encode("utf8")
    parts["ppt/_rels/presentation.xml.rels"] = PRESENTATION_RELS.encode("utf8")
    for keep in ("ppt/presProps.xml", "ppt/viewProps.xml", "ppt/tableStyles.xml",
                 "docProps/core.xml"):
        parts[keep] = zin.read(keep)
    # Must be named image* -- pandoc only copies ppt/media/image* into output.
    parts["ppt/media/image200.png"] = BLACK_LOGO.read_bytes()
    parts["docProps/app.xml"] = APP_XML.encode("utf8")
    parts["_rels/.rels"] = ROOT_RELS.encode("utf8")

    # --- media -------------------------------------------------------------
    for name in sorted(media):
        # Swap the heavy swirl PNG for the same downsampled JPEG the Reveal
        # deck uses, so both formats show identical artwork.
        if f"{Path(name).stem}.png" in SWIRL_PNGS:
            parts[f"ppt/media/{name}"] = SWIRL.read_bytes()
        else:
            parts[f"ppt/media/{name}"] = zin.read(f"ppt/media/{name}")

    overrides = "".join(
        f'<Override PartName="/ppt/slideLayouts/slideLayout{i}.xml" '
        f'ContentType="application/vnd.openxmlformats-officedocument.'
        f'presentationml.slideLayout+xml"/>' for i, *_ in LAYOUTS)
    parts["[Content_Types].xml"] = CONTENT_TYPES.format(
        layout_overrides=overrides).encode("utf8")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in sorted(parts):
            # Fixed timestamp and mode: this artefact is committed, and a zip
            # whose bytes change on every rebuild shows up as a spurious diff.
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zout.writestr(info, parts[name])
    zin.close()
    print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size:,} bytes, {len(parts)} parts)")


# --------------------------------------------------------------------------- #
# Verification
# --------------------------------------------------------------------------- #

# What pandoc looks up per layout, in spTree document order. "obj" means a
# <p:ph> with NO type attribute -- pandoc's ObjType.
CONTRACT = {
    "Title Slide": ["ctrTitle", "subTitle"],
    "Title and Content": ["title", "obj"],
    "Section Header": ["title"],
    "Two Content": ["title", "obj", "obj"],
    "Comparison": ["title", "body", "obj", "body", "obj"],
    "Content with Caption": ["title", "body", "obj"],
    "Blank": [],
}


def ph_sequence(xml: str) -> list[str]:
    """Placeholder types in spTree document order; untyped becomes 'obj'."""
    seq = []
    for m in re.finditer(r"<p:ph\b[^>]*/>", xml):
        t = re.search(r'type="([^"]+)"', m.group(0))
        seq.append(t.group(1) if t else "obj")
    return seq


def verify(path: Path) -> list[str]:
    """Return a list of problems; empty means the package is sound."""
    problems = []
    z = zipfile.ZipFile(path)
    names = set(z.namelist())

    layouts = {}
    for n in sorted(names):
        if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", n):
            xml = z.read(n).decode("utf8")
            m = re.search(r'<p:cSld[^>]*name="([^"]*)"', xml)
            layouts[n] = (m.group(1) if m else None, xml)

    # 1. pandoc's layout contract
    by_name = {}
    for n, (nm, xml) in layouts.items():
        if nm in by_name:
            problems.append(f"duplicate layout name {nm!r} ({n} and {by_name[nm]})")
        by_name[nm] = n
    for name, expected in CONTRACT.items():
        if name not in by_name:
            problems.append(f"missing layout {name!r}")
            continue
        got = ph_sequence(layouts[by_name[name]][1])
        # dt/ftr/sldNum are chrome, not content; ignore them in the contract.
        got = [t for t in got if t not in ("dt", "ftr", "sldNum")]
        if got[:len(expected)] != expected:
            problems.append(f"{name!r}: placeholder order {got} does not start with {expected}")

    # 2. idx hygiene -- unique per layout, never 1 (pandoc hardcodes idx=1
    #    on table graphicFrames and would collide)
    for n, (nm, xml) in layouts.items():
        idxs = re.findall(r'<p:ph\b[^>]*\bidx="(\d+)"', xml)
        if len(idxs) != len(set(idxs)):
            problems.append(f"{nm!r}: duplicate idx values {idxs}")
        if "1" in idxs and nm != "Title Slide":
            problems.append(f"{nm!r}: idx=1 collides with pandoc's table frames")
        for m in re.finditer(r"<p:sp>.*?</p:sp>", xml, re.S):
            if "<p:ph" in m.group(0) and "<a:off " not in m.group(0):
                problems.append(f"{nm!r}: a placeholder has no <a:xfrm> geometry")

    # 3. OPC soundness -- every rel target exists, every part has a content type
    ct = z.read("[Content_Types].xml").decode("utf8")
    defaults = set(re.findall(r'<Default Extension="([^"]+)"', ct))
    overrides = set(re.findall(r'<Override PartName="/([^"]+)"', ct))
    for n in names:
        if n.endswith(".rels") or n == "[Content_Types].xml":
            continue
        if n not in overrides and n.rsplit(".", 1)[-1].lower() not in defaults:
            problems.append(f"part with no content type: {n}")
    for n in names:
        if not n.endswith(".rels"):
            continue
        base = n.rsplit("_rels/", 1)[0].rstrip("/")
        for m in re.finditer(r'Target="([^"]+)"([^>]*)', z.read(n).decode("utf8")):
            if 'TargetMode="External"' in m.group(2):
                continue
            target = m.group(1)
            resolved = str(Path(base or ".", target).as_posix()).lstrip("./")
            resolved = re.sub(r"[^/]+/\.\./", "", resolved)
            if resolved not in names:
                problems.append(f"{n}: dangling target {target} -> {resolved}")

    # 4. links must be visible on the light master
    theme = z.read("ppt/theme/theme1.xml").decode("utf8")
    if f'<a:hlink><a:srgbClr val="{LINK}"/>' not in theme:
        problems.append(f"theme hyperlink colour is not #{LINK}; links will be "
                        "invisible on the light master")

    # 5. counts pandoc's dist-archive glob depends on
    n_layouts = len(layouts)
    n_themes = len([n for n in names if re.fullmatch(r"ppt/theme/theme\d+\.xml", n)])
    n_masters = len([n for n in names if re.fullmatch(r"ppt/slideMasters/slideMaster\d+\.xml", n)])
    if n_masters != 1:
        problems.append(f"expected exactly 1 slide master, found {n_masters}")
    if n_layouts != 11:
        problems.append(f"expected 11 layouts (pandoc's dist has 11), found {n_layouts}")
    if n_themes != 2:
        problems.append(f"expected 2 themes (pandoc's dist has 2), found {n_themes}")

    z.close()
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="assert the package is sound")
    args = ap.parse_args()

    build()

    if args.verify:
        problems = verify(OUT)
        if problems:
            print(f"\n{len(problems)} problem(s):", file=sys.stderr)
            for p in problems:
                print(f"  - {p}", file=sys.stderr)
            return 1
        print("verify: layout contract, idx hygiene, OPC refs and part counts all OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
