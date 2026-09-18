"""Red/green cover for tools/pptx_edit.py -- changing a colleague's deck.

Every edit is a zip rewritten to a zip, copying the bytes of every part it
was not asked to touch. That is the whole basis of the promise made back to
the colleague, so rewrite() is tested harder than anything it is used for.

    python -m unittest tests.test_pptx_edit
"""
import re
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import pptx_diff  # noqa: E402
import pptx_edit  # noqa: E402
import pptx_inventory  # noqa: E402
from deckfixture import make_deck  # noqa: E402

DIALECTS = ("powerpoint", "pandoc")


def parts(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


def order(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as z:
        return z.namelist()


class RewriteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.src = make_deck(self.tmp / "src.pptx", media=True)
        self.dst = self.tmp / "dst.pptx"

    def test_an_untouched_copy_is_part_for_part_identical(self):
        pptx_edit.rewrite(self.src, self.dst)
        self.assertEqual(parts(self.src), parts(self.dst))
        self.assertEqual(order(self.src), order(self.dst))

    def test_the_source_is_still_readable_afterwards(self):
        # Handing a source ZipInfo to writestr mutates it, and every later
        # read from that source then fails with a CRC error. It is a silent
        # trap: the first copy looks perfect.
        pptx_edit.rewrite(self.src, self.dst)
        pptx_edit.rewrite(self.src, self.tmp / "again.pptx")
        self.assertEqual(parts(self.src), parts(self.tmp / "again.pptx"))
        with zipfile.ZipFile(self.src) as z:
            self.assertIsNone(z.testzip())

    def test_replacing_one_part_leaves_every_other_byte_alone(self):
        before = parts(self.src)
        pptx_edit.rewrite(self.src, self.dst,
                          replace={"ppt/presentation.xml": b"<new/>"})
        after = parts(self.dst)
        self.assertEqual(b"<new/>", after["ppt/presentation.xml"])
        self.assertEqual({"ppt/presentation.xml"},
                         {n for n in before if before[n] != after[n]})

    def test_added_parts_arrive_and_dropped_parts_go(self):
        pptx_edit.rewrite(self.src, self.dst,
                          add={"ppt/slides/slide9.xml": b"<sld/>"},
                          drop={"ppt/media/image1.gif"})
        after = parts(self.dst)
        self.assertEqual(b"<sld/>", after["ppt/slides/slide9.xml"])
        self.assertNotIn("ppt/media/image1.gif", after)
        # A dropped part must not leave its neighbours' order disturbed.
        self.assertEqual([n for n in order(self.src) if n != "ppt/media/image1.gif"],
                         order(self.dst)[:-1])

    def test_replacing_a_part_that_is_not_there_is_refused(self):
        # A mistyped part name would otherwise write a deck that silently
        # lacks the edit, and the edit would be blamed on PowerPoint.
        with self.assertRaises(SystemExit) as caught:
            pptx_edit.rewrite(self.src, self.dst, replace={"ppt/slide1.xml": b"x"})
        self.assertIn("ppt/slide1.xml", str(caught.exception))

    def test_adding_a_part_that_is_already_there_is_refused(self):
        with self.assertRaises(SystemExit):
            pptx_edit.rewrite(self.src, self.dst,
                              add={"ppt/presentation.xml": b"x"})


class InPlaceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.deck = make_deck(self.tmp / "deck.pptx")

    def test_an_edit_lands_on_the_deck_itself(self):
        pptx_edit.edit(self.deck, replace={"ppt/presentation.xml": b"<new/>"})
        self.assertEqual(b"<new/>", parts(self.deck)["ppt/presentation.xml"])

    def test_a_failed_write_leaves_the_deck_as_it_was_and_says_why(self):
        # The deck being open in PowerPoint is the ordinary case, and the
        # message has to name the cure rather than the errno.
        before = self.deck.read_bytes()
        with mock.patch("os.replace", side_effect=PermissionError(13, "in use")):
            with self.assertRaises(SystemExit) as caught:
                pptx_edit.edit(self.deck, replace={"ppt/presentation.xml": b"<new/>"})
        self.assertIn("PowerPoint", str(caught.exception))
        self.assertEqual(before, self.deck.read_bytes())
        self.assertEqual([], list(self.tmp.glob("*.tmp")))


class AddSlideTest(unittest.TestCase):
    """A slide has to be registered in four places or PowerPoint repairs the file."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def deck(self, dialect="powerpoint", **kwargs):
        return make_deck(self.tmp / f"{dialect}.pptx", dialect=dialect, **kwargs)

    def test_a_cloned_slide_lands_where_it_was_asked_for(self):
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d)
                made = pptx_edit.add_slide(deck, clone=1, after=1)
                self.assertEqual(2, made["position"])
                order = pptx_edit.slide_parts(deck)
                self.assertEqual(4, len(order))
                self.assertEqual(made["part"], order[1])

    def test_it_goes_first_when_asked_for_after_zero(self):
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d)
                made = pptx_edit.add_slide(deck, clone=2, after=0)
                self.assertEqual(made["part"], pptx_edit.slide_parts(deck)[0])

    def test_the_new_part_never_reuses_an_existing_file_name(self):
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d)
                # The fixture already holds slide1..slide3, presentation order
                # running the other way. Renumbering any of them would break
                # every relationship pointing at them.
                self.assertEqual("ppt/slides/slide4.xml",
                                 pptx_edit.add_slide(deck, clone=1, after=3)["part"])

    def test_the_slide_id_clears_every_id_already_in_use(self):
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d)
                # The fixture's ids are 256, 271, 258: a count-based guess
                # would collide, and a duplicate id is a repair prompt.
                self.assertEqual(272, pptx_edit.add_slide(deck, clone=1, after=3)["sldId"])

    def test_the_relationship_id_clears_the_presentation_as_well_as_its_rels(self):
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d)
                rid = pptx_edit.add_slide(deck, clone=1, after=3)["rId"]
                self.assertEqual("rId10", rid)
                pres = pptx_edit.read(deck, "ppt/presentation.xml")
                self.assertEqual(1, pres.count(f'r:id="{rid}"'))

    def test_the_four_registrations_are_all_made(self):
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d)
                made = pptx_edit.add_slide(deck, clone=1, after=1)
                name = Path(made["part"]).name
                with zipfile.ZipFile(deck) as z:
                    self.assertIn(made["part"], z.namelist())
                    self.assertIn(f"ppt/slides/_rels/{name}.rels", z.namelist())
                self.assertIn(f'PartName="/{made["part"]}"',
                              pptx_edit.read(deck, "[Content_Types].xml"))
                self.assertIn(f'Target="slides/{name}"',
                              pptx_edit.read(deck, "ppt/_rels/presentation.xml.rels"))

    def test_a_clone_gets_its_own_notes_page_or_none_at_all(self):
        # Two slides sharing one notesSlide is a defect PowerPoint repairs,
        # and it would mean editing one slide's notes changed the other's.
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d)
                made = pptx_edit.add_slide(deck, clone=1, after=1)
                rels = pptx_edit.read(deck, f"ppt/slides/_rels/{Path(made['part']).name}.rels")
                self.assertNotIn("notesSlide", rels)
                self.assertIn("slideLayout", rels)

    def test_the_presentation_children_keep_their_order(self):
        # A PptxGenJS deck puts notesMasterIdLst where the schema does not
        # expect it. PowerPoint reads that happily and tidying it kills the
        # deck, so an edit must not so much as reorder siblings.
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d)
                before = re.findall(r"<(/?p:[a-zA-Z]+)",
                                    pptx_edit.read(deck, "ppt/presentation.xml"))
                pptx_edit.add_slide(deck, clone=1, after=1)
                after = re.findall(r"<(/?p:[a-zA-Z]+)",
                                   pptx_edit.read(deck, "ppt/presentation.xml"))
                self.assertEqual(before.count("p:sldId") + 1, after.count("p:sldId"))
                self.assertEqual([t for t in before if t != "p:sldId"],
                                 [t for t in after if t != "p:sldId"])

    def test_every_other_part_comes_through_byte_for_byte(self):
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d, media=True)
                before = parts(deck)
                made = pptx_edit.add_slide(deck, clone=1, after=1)
                after = parts(deck)
                self.assertEqual({"ppt/presentation.xml", "ppt/_rels/presentation.xml.rels",
                                  "[Content_Types].xml"},
                                 {n for n in before if before[n] != after[n]})
                self.assertEqual({made["part"],
                                  f"ppt/slides/_rels/{Path(made['part']).name}.rels"},
                                 set(after) - set(before))

    def test_an_authored_slide_can_be_inserted_from_xml(self):
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d)
                xml = pptx_edit.read(deck, pptx_edit.slide_parts(deck)[0])
                xml = xml.replace("Opening", "Authored here").encode("utf8")
                made = pptx_edit.add_slide(deck, xml=xml, after=3)
                self.assertIn("Authored here", pptx_edit.read(deck, made["part"]))

    def test_malformed_xml_is_refused_and_the_deck_is_left_alone(self):
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d)
                before = deck.read_bytes()
                with self.assertRaises(SystemExit) as caught:
                    pptx_edit.add_slide(deck, xml=b"<p:sld><unclosed>", after=1)
                self.assertIn("XML", str(caught.exception))
                self.assertEqual(before, deck.read_bytes())

    def test_a_reference_the_rels_cannot_satisfy_is_refused(self):
        # A dangling r:embed is the single commonest cause of the repair
        # dialog, and it is cheap to catch before writing anything.
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d)
                xml = pptx_edit.read(deck, pptx_edit.slide_parts(deck)[0])
                xml = xml.replace("<p:spTree>", '<p:spTree><p:pic><a:blip r:embed="rId99"/></p:pic>')
                before = deck.read_bytes()
                with self.assertRaises(SystemExit) as caught:
                    pptx_edit.add_slide(deck, xml=xml.encode("utf8"), after=1)
                self.assertIn("rId99", str(caught.exception))
                self.assertEqual(before, deck.read_bytes())

    def test_an_out_of_range_request_is_refused(self):
        deck = self.deck()
        for kwargs in ({"clone": 9, "after": 1}, {"clone": 1, "after": 9}):
            with self.subTest(kwargs), self.assertRaises(SystemExit):
                pptx_edit.add_slide(deck, **kwargs)


class SetTextTest(unittest.TestCase):
    """Rewriting a paragraph in place, keeping the formatting around it."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def deck(self, dialect="powerpoint"):
        return make_deck(self.tmp / f"{dialect}.pptx", dialect=dialect)

    def words(self, deck, slide):
        """What pptx_to_md reads back off one slide."""
        import pptx_to_md
        out = self.tmp / "read.md"
        pptx_to_md.convert(deck, out, self.tmp / "a")
        body = out.read_text(encoding="utf8").split("## Slide ")[slide]
        return body

    def test_a_paragraph_is_replaced_and_the_rest_left_alone(self):
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d)
                pptx_edit.set_text(deck, slide=1, shape=3, para=0, text="Nytt innehåll")
                self.assertIn("Nytt innehåll", self.words(deck, 1))
                self.assertNotIn("Stamped on", self.words(deck, 1))
                self.assertIn("Opening", self.words(deck, 1))

    def test_the_run_formatting_survives_the_edit(self):
        # The whole point. Assigning to a text frame wholesale is what loses
        # the size, weight and typeface; the run properties are kept here.
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d)
                before = pptx_inventory.inventory(deck)["slides"][0]["shapes"][0]
                pptx_edit.set_text(deck, slide=1, shape=2, para=0, text="Ny rubrik")
                after = pptx_inventory.inventory(deck)["slides"][0]["shapes"][0]
                self.assertEqual("Ny rubrik", after["paragraphs"][0]["text"])
                self.assertEqual(before["paragraphs"][0]["formats"],
                                 after["paragraphs"][0]["formats"])

    def test_only_that_one_slide_changes(self):
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d)
                before = parts(deck)
                pptx_edit.set_text(deck, slide=1, shape=2, para=0, text="Ny rubrik")
                after = parts(deck)
                self.assertEqual({pptx_edit.slide_parts(deck)[0]},
                                 {n for n in before if before[n] != after[n]})

    def test_a_mixed_paragraph_is_refused_unless_flattening_is_asked_for(self):
        # A bold lead-in followed by normal text cannot survive being rewritten
        # as one run, so the caller has to say they accept that.
        for d in DIALECTS:
            with self.subTest(d):
                deck = self.deck(d)
                with self.assertRaises(SystemExit) as caught:
                    pptx_edit.set_text(deck, slide=2, shape=4, para=0, text="Ett stycke")
                self.assertIn("--flatten", str(caught.exception))
                pptx_edit.set_text(deck, slide=2, shape=4, para=0, text="Ett stycke",
                                   flatten=True)
                self.assertIn("Ett stycke", self.words(deck, 2))

    def test_the_characters_xml_cares_about_are_escaped(self):
        deck = self.deck()
        pptx_edit.set_text(deck, slide=1, shape=2, para=0, text='Risk & "reward" <nu>')
        self.assertEqual([], pptx_diff.validate(deck))
        self.assertIn('Risk & "reward" <nu>', self.words(deck, 1))

    def test_a_leading_space_is_preserved_rather_than_eaten(self):
        deck = self.deck()
        pptx_edit.set_text(deck, slide=1, shape=2, para=0, text="  indraget")
        self.assertIn('xml:space="preserve"', pptx_edit.read(deck, pptx_edit.slide_parts(deck)[0]))

    def test_an_unknown_shape_or_paragraph_is_refused(self):
        deck = self.deck()
        for kwargs in ({"shape": 999, "para": 0}, {"shape": 2, "para": 9}):
            with self.subTest(kwargs), self.assertRaises(SystemExit):
                pptx_edit.set_text(deck, slide=1, text="x", **kwargs)


if __name__ == "__main__":
    unittest.main()
