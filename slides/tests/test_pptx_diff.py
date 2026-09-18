"""Red/green cover for tools/pptx_diff.py -- the proof that goes back with the deck.

Two jobs. validate() is the pre-flight: the defects that make PowerPoint
offer to repair a file are all cheap to find in the package, and finding one
here is worth more than finding it in front of the colleague. diff() is the
evidence: which slides are byte-for-byte what arrived, and which are not.

Defects are seeded with pptx_edit.rewrite, so the fixtures stay honest --
every broken deck here is a real package with one real thing wrong.

    python -m unittest tests.test_pptx_diff
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import pptx_diff  # noqa: E402
import pptx_edit  # noqa: E402
from deckfixture import make_deck  # noqa: E402

DIALECTS = ("powerpoint", "pandoc")


class ValidateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def broken(self, dialect="powerpoint", **changes) -> Path:
        src = make_deck(self.tmp / "src.pptx", dialect=dialect, media=True)
        dst = self.tmp / "broken.pptx"
        dst.unlink(missing_ok=True)
        pptx_edit.rewrite(src, dst, **changes)
        return dst

    def test_a_sound_deck_has_nothing_to_report(self):
        for d in DIALECTS:
            with self.subTest(d):
                self.assertEqual([], pptx_diff.validate(
                    make_deck(self.tmp / f"{d}.pptx", dialect=d, media=True)))

    def test_a_relationship_pointing_at_nothing_is_caught(self):
        # The commonest cause of the repair dialog by a distance.
        deck = self.broken(drop={"ppt/media/image1.gif"})
        self.assertIn("image1.gif", " ".join(pptx_diff.validate(deck)))

    def test_a_part_with_no_content_type_is_caught(self):
        # media=True to match the deck being broken: a Content_Types taken
        # from a deck without media would also drop the gif Default, and the
        # test would pass on the wrong defect.
        ct = pptx_edit.read(make_deck(self.tmp / "s.pptx", media=True), "[Content_Types].xml")
        deck = self.broken(replace={"[Content_Types].xml": ct.replace(
            '<Override PartName="/ppt/slides/slide1.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument'
            '.presentationml.slide+xml"/>', "").encode("utf8")})
        self.assertIn("slide1.xml", " ".join(pptx_diff.validate(deck)))

    def test_a_duplicate_slide_id_is_caught(self):
        pres = pptx_edit.read(make_deck(self.tmp / "s.pptx"), "ppt/presentation.xml")
        deck = self.broken(replace={
            "ppt/presentation.xml": pres.replace('id="271"', 'id="256"').encode("utf8")})
        self.assertIn("256", " ".join(pptx_diff.validate(deck)))

    def test_a_slide_id_below_the_floor_is_caught(self):
        pres = pptx_edit.read(make_deck(self.tmp / "s.pptx"), "ppt/presentation.xml")
        deck = self.broken(replace={
            "ppt/presentation.xml": pres.replace('id="256"', 'id="12"').encode("utf8")})
        self.assertIn("256", " ".join(pptx_diff.validate(deck)))

    def test_two_slides_sharing_one_notes_page_is_caught(self):
        rels = pptx_edit.read(make_deck(self.tmp / "s.pptx"), "ppt/slides/_rels/slide2.xml.rels")
        deck = self.broken(replace={"ppt/slides/_rels/slide2.xml.rels":
                                    rels.replace("notesSlide3", "notesSlide1").encode("utf8")})
        self.assertIn("notesSlide1", " ".join(pptx_diff.validate(deck)))

    def test_a_slide_bound_to_two_layouts_is_caught(self):
        rels = pptx_edit.read(make_deck(self.tmp / "s.pptx"), "ppt/slides/_rels/slide1.xml.rels")
        deck = self.broken(replace={"ppt/slides/_rels/slide1.xml.rels": rels.replace(
            "</Relationships>",
            '<Relationship Id="rId9" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/slideLayout" '
            'Target="../slideLayouts/slideLayout1.xml"/></Relationships>').encode("utf8")})
        self.assertIn("slide1.xml", " ".join(pptx_diff.validate(deck)))

    def test_page_numbers_typed_as_text_are_reported(self):
        # A deck whose slide numbers are literal text rather than a slidenum
        # field goes stale the moment anyone inserts a slide -- including us.
        # The client deck arrived already wrong this way, so it is worth
        # saying out loud before handing anything back.
        src = make_deck(self.tmp / "src.pptx")
        part = pptx_edit.slide_parts(src)[2]
        numbered = pptx_edit.read(src, part).replace(
            "<p:spTree>",
            '<p:spTree><p:sp><p:nvSpPr><p:cNvPr id="90" name="Slide number"/>'
            '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            '<p:spPr><a:xfrm><a:off x="11521440" y="6492240"/>'
            '<a:ext cx="457200" cy="274320"/></a:xfrm></p:spPr>'
            "<p:txBody><a:bodyPr/><a:p><a:r><a:t>7</a:t></a:r></a:p></p:txBody></p:sp>")
        deck = self.broken(replace={part: numbered.encode("utf8")})
        note = " ".join(pptx_diff.validate(deck))
        self.assertIn("note:", note)
        self.assertIn("slide 3", note)

    def test_a_page_number_that_agrees_with_its_position_is_not_reported(self):
        src = make_deck(self.tmp / "src.pptx")
        part = pptx_edit.slide_parts(src)[2]
        numbered = pptx_edit.read(src, part).replace(
            "<p:spTree>",
            '<p:spTree><p:sp><p:nvSpPr><p:cNvPr id="90" name="Slide number"/>'
            '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            '<p:spPr><a:xfrm><a:off x="11521440" y="6492240"/>'
            '<a:ext cx="457200" cy="274320"/></a:xfrm></p:spPr>'
            "<p:txBody><a:bodyPr/><a:p><a:r><a:t>3</a:t></a:r></a:p></p:txBody></p:sp>")
        deck = self.broken(replace={part: numbered.encode("utf8")})
        self.assertEqual([], pptx_diff.validate(deck))

    def test_slide_xml_that_does_not_parse_is_caught(self):
        deck = self.broken(replace={"ppt/slides/slide1.xml": b"<p:sld><unclosed>"})
        self.assertIn("slide1.xml", " ".join(pptx_diff.validate(deck)))


class DiffTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.before = make_deck(self.tmp / "before.pptx", media=True)
        self.after = self.tmp / "after.pptx"
        shutil.copy2(self.before, self.after)

    def test_an_untouched_deck_reports_every_slide_identical(self):
        report = pptx_diff.diff(self.before, self.after)
        self.assertEqual([256, 271, 258], report["slides"]["identical"])
        self.assertEqual([], report["slides"]["changed"])
        self.assertEqual({"changed": [], "added": [], "removed": []}, report["parts"])
        self.assertTrue(report["ok"])

    def test_an_added_slide_leaves_the_rest_identical(self):
        made = pptx_edit.add_slide(self.after, clone=1, after=1)
        report = pptx_diff.diff(self.before, self.after)
        self.assertEqual([256, 271, 258], report["slides"]["identical"])
        self.assertEqual([made["sldId"]], report["slides"]["added"])
        self.assertEqual([], report["slides"]["changed"])
        # Adding a slide touches the three registration parts and no others.
        self.assertEqual(["[Content_Types].xml", "ppt/_rels/presentation.xml.rels",
                          "ppt/presentation.xml"], report["parts"]["changed"])
        self.assertTrue(report["ok"])

    def test_slides_are_matched_by_id_not_by_position(self):
        # Inserting a slide shifts every later slide's number. Comparing by
        # position would report all of them changed.
        pptx_edit.add_slide(self.after, clone=1, after=0)
        report = pptx_diff.diff(self.before, self.after)
        self.assertEqual([256, 271, 258], report["slides"]["identical"])

    def test_an_edited_slide_is_named(self):
        part = pptx_edit.slide_parts(self.after)[1]
        pptx_edit.edit(self.after, replace={
            part: pptx_edit.read(self.after, part).replace("Second", "Changed").encode("utf8")})
        report = pptx_diff.diff(self.before, self.after)
        self.assertEqual([271], report["slides"]["changed"])
        self.assertEqual([256, 258], report["slides"]["identical"])

    def test_a_part_lost_with_no_slide_deleted_is_not_acceptable(self):
        pptx_edit.edit(self.after, drop={"ppt/media/image1.gif"})
        report = pptx_diff.diff(self.before, self.after)
        self.assertEqual(["ppt/media/image1.gif"], report["parts"]["removed"])
        self.assertFalse(report["ok"])

    def test_the_parts_a_deleted_slide_took_with_it_are_acceptable(self):
        # Deleting a slide is a thing we do on purpose, and it legitimately
        # removes the slide, its rels, its notes page and any media only it
        # was using. Reporting that as damage would make the check useless
        # the first time anyone deletes anything.
        gone = pptx_edit.delete_slide(self.after, 2)
        report = pptx_diff.diff(self.before, self.after)
        self.assertEqual([271], report["slides"]["removed"])
        self.assertIn("ppt/media/image1.gif", report["parts"]["removed"])
        self.assertTrue(report["ok"])

    def test_a_theme_lost_is_never_acceptable_even_alongside_a_delete(self):
        pptx_edit.delete_slide(self.after, 2)
        pptx_edit.edit(self.after, drop={"ppt/theme/theme1.xml"})
        report = pptx_diff.diff(self.before, self.after)
        self.assertFalse(report["ok"])

    def test_a_disturbed_theme_is_not_acceptable(self):
        # Nothing we do should rewrite the master, the theme or the layouts.
        # If one moves, the colleague's untouched slides may render differently.
        pptx_edit.edit(self.after, replace={"ppt/theme/theme1.xml": b"<a:theme/>"})
        report = pptx_diff.diff(self.before, self.after)
        self.assertIn("ppt/theme/theme1.xml", report["parts"]["changed"])
        self.assertFalse(report["ok"])


if __name__ == "__main__":
    unittest.main()
