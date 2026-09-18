"""Red/green cover for tools/pptx_to_md.py -- reading a deck back as Markdown.

Two sources. A package built here in memory pins the rules that are easy to
get wrong without a renderer: slides come out in presentation order rather
than file-name order, and the notes page follows its slide. The rendered
pptx-components fixture then checks the tool against what pandoc and
pptx-nexer.lua actually write: named shapes, a real table, a picture.

    python -m unittest tests.test_pptx_to_md
"""
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import pptx_to_md  # noqa: E402
from check_pptx import layout_of_each_slide  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1]
DECK = PROJECT / "_site" / "tests" / "pptx-components.pptx"

A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
P = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
RELS = 'xmlns="http://schemas.openxmlformats.org/package/2006/relationships"'


def text_shape(name: str, text: str) -> str:
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="2" name="{name}"/></p:nvSpPr>'
            f"<p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>")


def broken_shape(name: str, *paras: str) -> str:
    """A shape whose paragraphs hold <a:br/> line breaks, as a title block does."""
    body = ""
    for para in paras:
        lvl, _, text = para.partition("|")
        ppr = f'<a:pPr lvl="{lvl}"><a:buChar char="-"/></a:pPr>' if lvl.isdigit() else ""
        runs = "<a:br/>".join(f"<a:r><a:t>{seg}</a:t></a:r>" for seg in text.split("//"))
        body += f"<a:p>{ppr}{runs}</a:p>"
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="3" name="{name}"/></p:nvSpPr>'
            f"<p:txBody>{body}</p:txBody></p:sp>")


def slide(*shapes: str) -> str:
    return f"<p:sld {A} {P} {R}><p:cSld><p:spTree>{''.join(shapes)}</p:spTree></p:cSld></p:sld>"


def rels(*targets: str) -> str:
    body = "".join(f'<Relationship Id="rId{i}" Target="{t}"/>' for i, t in enumerate(targets, 1))
    return f"<Relationships {RELS}>{body}</Relationships>"


def tiny_deck(path: Path) -> None:
    """Two slides whose file names run opposite to their presentation order."""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("ppt/presentation.xml",
                   f'<p:presentation {P} {R}><p:sldIdLst>'
                   f'<p:sldId id="256" r:id="rId1"/><p:sldId id="257" r:id="rId2"/>'
                   f"</p:sldIdLst></p:presentation>")
        z.writestr("ppt/_rels/presentation.xml.rels", rels("slides/slide2.xml", "slides/slide1.xml"))
        z.writestr("ppt/slides/slide2.xml", slide(text_shape("Title 1", "Comes first")))
        z.writestr("ppt/slides/_rels/slide2.xml.rels",
                   rels("../slideLayouts/slideLayout1.xml", "../notesSlides/notesSlide1.xml"))
        z.writestr("ppt/slides/slide1.xml",
                   slide(text_shape("Title 1", "Comes second"),
                         broken_shape("Subtitle 2", "|What it decides//Jonathan Jayes",
                                      "1|First half//second half")))
        z.writestr("ppt/slides/_rels/slide1.xml.rels", rels("../slideLayouts/slideLayout1.xml"))
        z.writestr("ppt/slideLayouts/slideLayout1.xml",
                   f'<p:sldLayout {P}><p:cSld name="Title Only"/></p:sldLayout>')
        z.writestr("ppt/notesSlides/notesSlide1.xml",
                   f"<p:notes {A} {P}><p:cSld><p:spTree>"
                   f"{text_shape('Notes 1', 'Say this out loud')}</p:spTree></p:cSld></p:notes>")


class TinyDeckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)
        deck = self.tmp / "tiny.pptx"
        tiny_deck(deck)
        self.out = self.tmp / "tiny.md"
        self.counts = pptx_to_md.convert(deck, self.out, self.tmp / "assets")
        self.md = self.out.read_text(encoding="utf8")

    def test_slides_follow_presentation_order_not_file_names(self):
        self.assertLess(self.md.index("Comes first"), self.md.index("Comes second"))

    def test_each_slide_is_headed_with_its_number_and_layout(self):
        self.assertIn("## Slide 1 — layout: Title Only", self.md)
        self.assertIn("## Slide 2 — layout: Title Only", self.md)

    def test_a_line_break_starts_a_new_line(self):
        # <a:br/> inside one paragraph is how a title block carries a subtitle
        # and an author. Joining the runs runs them together.
        self.assertIn("What it decides\nJonathan Jayes", self.md)

    def test_a_break_inside_a_bullet_stays_inside_the_bullet(self):
        self.assertIn("  - First half\n    second half", self.md)

    def test_notes_follow_their_own_slide(self):
        first, second = self.md.split("## Slide 2")
        self.assertIn("**Notes:**\n\nSay this out loud", first)
        self.assertNotIn("**Notes:**", second)
        self.assertEqual((2, 1), self.counts)


class RenderedDeckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = subprocess.run(
            ["quarto", "render", "tests/pptx-components.qmd", "--to", "nexer-pptx"],
            cwd=PROJECT, capture_output=True, text=True, shell=True,
        )
        if not DECK.exists():
            raise AssertionError(f"fixture did not render:\n{result.stdout}\n{result.stderr}")
        cls.tmp = Path(tempfile.mkdtemp())
        out = cls.tmp / "components.md"
        pptx_to_md.convert(DECK, out, cls.tmp / "assets")
        cls.md = out.read_text(encoding="utf8")
        cls.slides = re.split(r"^## Slide \d+ — ", cls.md, flags=re.M)[1:]

    @classmethod
    def tearDownClass(cls):
        __import__("shutil").rmtree(cls.tmp, True)

    def test_one_section_per_slide_with_the_layout_check_pptx_reports(self):
        layouts = [s.splitlines()[0].removeprefix("layout: ") for s in self.slides]
        self.assertEqual(layout_of_each_slide(DECK), layouts)

    def test_filter_shapes_are_named_where_they_land(self):
        self.assertIn("<!-- Nexer kicker -->", self.slides[2])
        self.assertIn("<!-- Nexer stat 1 -->", self.slides[3])

    def test_a_table_comes_out_as_a_markdown_table(self):
        self.assertRegex(self.slides[6], r"\| Route \| Risk sits with \| Time to value \|\n\|---\|---\|---\|")

    def test_pictures_are_extracted_and_linked(self):
        pics = list((self.tmp / "assets").iterdir())
        self.assertTrue(pics)
        self.assertIn(f"](assets/{pics[0].name})", self.md)


if __name__ == "__main__":
    unittest.main()
