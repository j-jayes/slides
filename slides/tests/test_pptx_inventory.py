"""Red/green cover for tools/pptx_inventory.py -- the addressable view of a deck.

pptx_to_md.py gives an agent the words. This gives it the handles: the shape
id to edit, the geometry and colours to copy when authoring a slide that has
to look native, and the layouts and placeholders to use when the deck has any.

Every test runs against both XML dialects, because a regex that only knows
PowerPoint's `<x/>` passes on a fixture and breaks on a Quarto render.

    python -m unittest tests.test_pptx_inventory
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import pptx_inventory  # noqa: E402
from deckfixture import make_deck  # noqa: E402

DIALECTS = ("powerpoint", "pandoc")


class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def inv(self, **kwargs):
        """The inventory of a fixture deck, per dialect."""
        dialect = kwargs.pop("dialect")
        deck = make_deck(self.tmp / f"{dialect}.pptx", dialect=dialect, **kwargs)
        return pptx_inventory.inventory(deck)

    def test_deck_facts_an_author_needs(self):
        for d in DIALECTS:
            with self.subTest(d):
                inv = self.inv(dialect=d)
                self.assertEqual([12192000, 6858000], inv["slide_size"])
                self.assertEqual("Cambria", inv["theme"]["major"])
                self.assertEqual("Calibri", inv["theme"]["minor"])
                self.assertEqual("4472C4", inv["theme"]["colours"]["accent1"])

    def test_layouts_are_listed_with_their_placeholders(self):
        for d in DIALECTS:
            with self.subTest(d):
                layouts = self.inv(dialect=d)["layouts"]
                self.assertEqual(1, len(layouts))
                self.assertEqual("Title and Content", layouts[0]["name"])
                self.assertEqual(["title", "body"], layouts[0]["placeholders"])

    def test_kind_says_whether_the_layouts_can_be_built_on(self):
        # The whole authoring decision turns on this. A deck with placeholders
        # gets slides built on its layouts; one without -- a PptxGenJS export,
        # say -- gets shapes copied off a neighbouring slide instead.
        for d in DIALECTS:
            with self.subTest(d):
                self.assertEqual("template", self.inv(dialect=d)["kind"])
                self.assertEqual("free-shape",
                                 self.inv(dialect=d, placeholders=False)["kind"])

    def test_slides_come_in_presentation_order_carrying_their_ids(self):
        for d in DIALECTS:
            with self.subTest(d):
                slides = self.inv(dialect=d)["slides"]
                self.assertEqual([1, 2, 3], [s["n"] for s in slides])
                # Not contiguous, and not the file-name order.
                self.assertEqual([256, 271, 258], [s["sldId"] for s in slides])
                self.assertEqual("ppt/slides/slide1.xml", slides[1]["part"])
                self.assertEqual("Title and Content", slides[0]["layout"])

    def test_a_shape_carries_the_handle_and_the_look(self):
        for d in DIALECTS:
            with self.subTest(d):
                shape = self.inv(dialect=d)["slides"][0]["shapes"][1]
                self.assertEqual(3, shape["id"])
                self.assertEqual("Rectangle 3", shape["name"])
                self.assertEqual("sp", shape["kind"])
                self.assertEqual("rect", shape["geom"])
                self.assertEqual([548640, 457200, 2000000, 500000], shape["xywh"])
                self.assertEqual("0F172A", shape["fill"])

    def test_a_placeholder_shape_says_which_one_it_fills(self):
        for d in DIALECTS:
            with self.subTest(d):
                self.assertEqual("title", self.inv(dialect=d)["slides"][0]["shapes"][0]["ph"])

    def test_paragraphs_are_numbered_the_way_an_edit_addresses_them(self):
        for d in DIALECTS:
            with self.subTest(d):
                paras = self.inv(dialect=d)["slides"][1]["shapes"][1]["paragraphs"]
                self.assertEqual([0, 1, 2], [p["i"] for p in paras])
                self.assertEqual("Lead-in: then the rest", paras[0]["text"])
                self.assertEqual(1, paras[1]["lvl"])

    def test_mixed_marks_the_paragraphs_an_edit_would_flatten(self):
        # A bold lead-in followed by normal text cannot survive being rewritten
        # as one run, so the edit tool refuses it and this is the warning.
        for d in DIALECTS:
            with self.subTest(d):
                paras = self.inv(dialect=d)["slides"][1]["shapes"][1]["paragraphs"]
                self.assertTrue(paras[0]["mixed"])
                self.assertFalse(paras[1]["mixed"])

    def test_run_formats_are_reported_once_not_per_run(self):
        for d in DIALECTS:
            with self.subTest(d):
                title = self.inv(dialect=d)["slides"][0]["shapes"][0]["paragraphs"][0]
                self.assertEqual([{"typeface": "Calibri", "sz": 4000, "b": True}],
                                 title["formats"])

    def test_a_picture_records_the_file_it_embeds(self):
        for d in DIALECTS:
            with self.subTest(d):
                shapes = self.inv(dialect=d, media=True)["slides"][1]["shapes"]
                pic = [s for s in shapes if s["kind"] == "pic"][0]
                self.assertEqual("ppt/media/image1.gif", pic["embeds"])

    def test_notes_travel_with_their_slide(self):
        for d in DIALECTS:
            with self.subTest(d):
                slides = self.inv(dialect=d)["slides"]
                self.assertEqual("Narration for slide1.xml", slides[1]["notes"])
                self.assertIsNone(self.inv(dialect=d, notes=False)["slides"][1]["notes"])


if __name__ == "__main__":
    unittest.main()
