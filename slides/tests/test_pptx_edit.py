"""Red/green cover for tools/pptx_edit.py -- changing a colleague's deck.

Every edit is a zip rewritten to a zip, copying the bytes of every part it
was not asked to touch. That is the whole basis of the promise made back to
the colleague, so rewrite() is tested harder than anything it is used for.

    python -m unittest tests.test_pptx_edit
"""
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import pptx_edit  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
