"""Red/green cover for the one thing that broke when outputs moved to _site/.

export_pdf.py decides which decks want a PDF by reading `export-pdf: true` out
of the deck's own front matter. It gets from the rendered .html back to the
.qmd by name, which was the same directory until the kit became a website
project and outputs moved to _site/.
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import export_pdf  # noqa: E402


class SourceOfTest(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.tmp)
        (self.tmp / "_site" / "client").mkdir(parents=True)
        self.addCleanup(os.environ.pop, "QUARTO_PROJECT_OUTPUT_DIR", None)
        os.environ["QUARTO_PROJECT_OUTPUT_DIR"] = str(self.tmp / "_site")

    def test_output_maps_back_to_its_source_deck(self):
        self.assertEqual(Path("template.qmd"),
                         export_pdf.source_of(Path("_site/template.html")))

    def test_a_deck_in_a_subfolder_keeps_its_subfolder(self):
        self.assertEqual(Path("client/q3.qmd"),
                         export_pdf.source_of(Path("_site/client/q3.html")))

    def test_a_deck_rendered_outside_a_project_sits_beside_its_output(self):
        del os.environ["QUARTO_PROJECT_OUTPUT_DIR"]
        self.assertEqual(Path("my-deck.qmd"),
                         export_pdf.source_of(Path("my-deck.html")))


if __name__ == "__main__":
    unittest.main()
