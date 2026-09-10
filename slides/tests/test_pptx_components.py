"""What the pptx filter must put on each slide of tests/pptx-components.qmd.

The failure this guards against is silent: a deck renders, opens, and is simply
plain. So the assertions are about *named shapes* -- the filter labels every
shape it builds "Nexer <thing>", which is also what you see in PowerPoint's
selection pane -- plus the slide count and layout sequence, because the way a
raw shape goes wrong is by making pandoc split a slide or pick a smaller
content placeholder.

    python -m unittest discover -s tests

Renders the fixture once for the whole class; that takes a few seconds.
"""
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_pptx import layout_of_each_slide  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1]
FIXTURE = PROJECT / "tests" / "pptx-components.qmd"
DECK = PROJECT / "_site" / "tests" / "pptx-components.pptx"

# (layout, shapes that must be present, shapes that must NOT be)
#
# "Nexer kicker" and "Nexer rule" ride along on every slide that has both a
# `##` locator and a `###` action title, which is every content slide here.
KICKER = ["Nexer kicker", "Nexer rule"]
EXPECTED = [
    ("Title Slide", [], KICKER),
    ("Section Header", [], KICKER),
    ("Title and Content", KICKER, []),
    ("Title and Content", KICKER + ["Nexer stat 1", "Nexer stat 2", "Nexer stat 3",
                                    "Nexer stat 4", "Nexer takeaway", "Nexer source"], []),
    ("Two Content", KICKER + ["Nexer takeaway", "Nexer source"], ["Nexer stat 1"]),
    ("Title and Content", KICKER + ["Nexer source"], ["Nexer takeaway"]),
    ("Title and Content", KICKER + ["Nexer source"], ["Nexer takeaway"]),
    ("Title and Content", KICKER, ["Nexer source"]),
    ("Content with Caption", KICKER, ["Nexer source"]),
    ("Blank", [], KICKER),
]


def slide_xml(deck: Path) -> list[str]:
    with zipfile.ZipFile(deck) as z:
        return [
            z.read(f"ppt/slides/slide{i}.xml").decode("utf8")
            for i in range(1, len(EXPECTED) + 1)
            if f"ppt/slides/slide{i}.xml" in z.namelist()
        ]


class ComponentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = subprocess.run(
            ["quarto", "render", "tests/pptx-components.qmd", "--to", "nexer-pptx"],
            cwd=PROJECT, capture_output=True, text=True, shell=True,
        )
        if not DECK.exists():
            raise AssertionError(f"fixture did not render:\n{result.stdout}\n{result.stderr}")
        cls.slides = slide_xml(DECK)
        cls.layouts = layout_of_each_slide(DECK)

    def test_the_deck_has_one_slide_per_archetype_and_no_splits(self):
        self.assertEqual(len(EXPECTED), len(self.slides))

    def test_every_slide_is_well_formed_xml(self):
        # The raw OpenXML the filter writes is never parsed by pandoc, so a
        # stray unclosed tag reaches PowerPoint as a repair prompt.
        for i, xml in enumerate(self.slides, 1):
            with self.subTest(slide=i):
                ET.fromstring(xml)

    def test_each_slide_keeps_its_intended_layout(self):
        self.assertEqual([e[0] for e in EXPECTED], self.layouts)

    def test_each_slide_carries_the_shapes_it_should(self):
        for i, (_, wanted, unwanted) in enumerate(EXPECTED, 1):
            for name in wanted:
                with self.subTest(slide=i, shape=name):
                    self.assertIn(f'name="{name}"', self.slides[i - 1])
            for name in unwanted:
                with self.subTest(slide=i, absent=name):
                    self.assertNotIn(f'name="{name}"', self.slides[i - 1])

    def test_shape_ids_do_not_collide_within_a_slide(self):
        for i, xml in enumerate(self.slides, 1):
            ids = [int(m) for m in __import__("re").findall(r'<p:cNvPr id="(\d+)"', xml)]
            mine = [x for x in ids if x >= 1000]
            with self.subTest(slide=i):
                self.assertEqual(sorted(set(mine)), sorted(mine))

    def test_a_background_colour_becomes_a_real_slide_background(self):
        self.assertIn("<p:bg>", self.slides[7], "the statement slide should be purple")

    def test_a_section_divider_does_not_re_embed_the_layout_artwork(self):
        self.assertNotIn("<p:bg>", self.slides[1])

    def test_chips_survive_as_highlighted_runs(self):
        self.assertIn("<a:highlight>", self.slides[2])

    def test_the_exhibit_slides_keep_their_exhibit(self):
        self.assertIn("<p:pic>", self.slides[4], "chart in a column")
        self.assertIn("<p:pic>", self.slides[5], "full-width image")
        self.assertIn("<a:tbl>", self.slides[6], "table stays a real table")
        self.assertIn("<p:pic>", self.slides[8], "framing text then image")


if __name__ == "__main__":
    unittest.main()
