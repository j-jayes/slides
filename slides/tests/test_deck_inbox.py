"""Red/green cover for tools/deck_inbox.py -- taking in a colleague's deck.

intake() is the one command run on a file that arrived from someone else, so
its promises are about custody rather than output: the original is copied and
never touched, the working copy sits at an ASCII path whatever the sender
called the file, and an existing work directory is refused rather than
overwritten.

Rendering needs PowerPoint, so the fast tests pass render=False and one
gated test covers the real thing.

    python -m unittest tests.test_deck_inbox
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import deck_inbox  # noqa: E402
import pptx_edit  # noqa: E402
from deckfixture import make_deck  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1]
RENDERED = PROJECT / "_site" / "tests" / "pptx-components.pptx"


def powerpoint_installed() -> bool:
    import winreg
    try:
        winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "PowerPoint.Application"))
        return True
    except OSError:
        return False


class IntakeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "repo"
        (self.root / "inbox").mkdir(parents=True)
        # The name a colleague actually sends: spaces, a dot, and an umlaut.
        self.src = make_deck(self.root / "inbox" / "Västerhuset 2.0_förslag.pptx")
        self.work = deck_inbox.intake(self.src, self.root, render=False)

    def test_the_work_directory_is_named_in_ascii(self):
        # COM resolves paths through the process locale and Quarto shells out;
        # neither is worth debugging over an umlaut.
        self.assertEqual("vasterhuset-2-0-forslag", self.work.name)
        self.assertEqual(self.root / "work" / "vasterhuset-2-0-forslag", self.work)
        self.assertTrue(str(self.work).isascii())

    def test_the_original_is_copied_byte_for_byte_and_left_alone(self):
        self.assertEqual(self.src.read_bytes(), (self.work / "original.pptx").read_bytes())
        self.assertEqual(self.src.read_bytes(), (self.work / "deck.pptx").read_bytes())

    def test_the_deck_comes_back_as_markdown_and_json(self):
        md = (self.work / "deck.md").read_text(encoding="utf8")
        self.assertIn("## Slide 1 — layout: Title and Content", md)
        inv = json.loads((self.work / "inventory.json").read_text(encoding="utf8"))
        self.assertEqual(3, len(inv["slides"]))
        self.assertEqual("template", inv["kind"])

    def test_a_change_log_is_started_for_the_colleague(self):
        self.assertIn("Västerhuset 2.0_förslag.pptx",
                      (self.work / "changes.md").read_text(encoding="utf8"))

    def test_an_existing_work_directory_is_refused(self):
        # Re-running would overwrite edits already made to deck.pptx.
        with self.assertRaises(SystemExit) as caught:
            deck_inbox.intake(self.src, self.root, render=False)
        self.assertIn("already", str(caught.exception))


class HandbackTest(unittest.TestCase):
    """What goes back to the colleague, and the evidence that goes with it."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "repo"
        (self.root / "inbox").mkdir(parents=True)
        self.src = make_deck(self.root / "inbox" / "Deras förslag v2.pptx")
        self.work = deck_inbox.intake(self.src, self.root, render=False)

    def test_the_deck_goes_out_under_the_name_it_came_in_under(self):
        out = deck_inbox.handback(self.work, render=False)
        # The colleague recognises their own file name; the suffix says who
        # touched it without making them hunt for the original.
        self.assertEqual("Deras förslag v2 (Nexer).pptx", out.name)
        self.assertEqual(self.root / "outbox", out.parent)

    def test_an_unedited_deck_goes_back_byte_for_byte(self):
        out = deck_inbox.handback(self.work, render=False)
        self.assertEqual(self.src.read_bytes(), out.read_bytes())

    def test_the_change_note_says_what_survived(self):
        pptx_edit.add_slide(self.work / "deck.pptx", clone=1, after=3)
        deck_inbox.handback(self.work, render=False)
        note = (self.root / "outbox" / "Deras förslag v2 (Nexer).changes.md").read_text(
            encoding="utf8")
        self.assertIn("3 of 3 slides", note)
        self.assertIn("Added: 1 slide(s)", note)

    def test_a_deck_that_would_not_open_never_leaves(self):
        # The last place to catch a broken package is here, not in the
        # colleague's PowerPoint.
        deck = self.work / "deck.pptx"
        pptx_edit.edit(deck, replace={pptx_edit.slide_parts(deck)[0]: b"<p:sld><oops>"})
        with self.assertRaises(SystemExit) as caught:
            deck_inbox.handback(self.work, render=False)
        self.assertIn("well-formed", str(caught.exception))
        self.assertFalse((self.root / "outbox").exists())

    def test_losing_a_part_stops_the_handback(self):
        pptx_edit.edit(self.work / "deck.pptx", drop={"ppt/theme/theme1.xml"})
        with self.assertRaises(SystemExit):
            deck_inbox.handback(self.work, render=False)


@unittest.skipUnless(powerpoint_installed(), "needs PowerPoint for COM export")
@unittest.skipUnless(RENDERED.exists(), "render tests/pptx-components.qmd first")
class RenderTest(unittest.TestCase):
    """The one test that proves an agent can actually see the deck."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        root = cls.tmp / "repo"
        (root / "inbox").mkdir(parents=True)
        src = root / "inbox" / "components.pptx"
        shutil.copy2(RENDERED, src)
        cls.work = deck_inbox.intake(src, root)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, True)

    def test_every_slide_is_exported_as_a_png(self):
        pngs = list((self.work / "before").glob("*.png"))
        inv = json.loads((self.work / "inventory.json").read_text(encoding="utf8"))
        self.assertEqual(len(inv["slides"]), len(pngs))

    def test_the_whole_deck_is_exported_as_one_pdf(self):
        pdf = self.work / "before.pdf"
        self.assertTrue(pdf.exists())
        self.assertEqual(b"%PDF", pdf.read_bytes()[:4])


if __name__ == "__main__":
    unittest.main()
