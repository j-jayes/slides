"""Red/green cover for tools/publish.py -- where a rendered file ends up.

The rules are cheap to state and easy to get wrong: HTML goes to docs/, decks
go to reports/, tests/ goes nowhere, nothing leaves _site/ (Quarto reads the
.pptx back after post-render), and neither destination is ever wiped -- docs/
may hold things this project did not write.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import publish  # noqa: E402


def tree(root: Path, spec: dict) -> None:
    for rel, text in spec.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf8")


class PublishTest(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)
        self.site = self.tmp / "_site"
        self.docs = self.tmp / "docs"
        self.reports = self.tmp / "reports"
        tree(self.site, {
            "index.html": "listing",
            "template.html": "deck",
            "template.pptx": "deck-pptx",
            "template.pdf": "deck-pdf",
            "template_files/figure-revealjs/chart.png": "img",
            "site_libs/reveal/reveal.js": "js",
            "client/q3.html": "sub deck",
            "client/q3.pptx": "sub pptx",
            "tests/reference-smoke.pptx": "fixture",
        })

    def run_publish(self):
        return publish.publish(self.site, self.docs, self.reports)

    def test_html_and_assets_are_copied_to_docs(self):
        self.run_publish()
        for rel in ("index.html", "template.html", "client/q3.html",
                    "template_files/figure-revealjs/chart.png",
                    "site_libs/reveal/reveal.js"):
            self.assertTrue((self.docs / rel).is_file(), rel)
            self.assertTrue((self.site / rel).is_file(), f"{rel} should be copied, not moved")

    def test_decks_are_copied_to_reports_keeping_subpaths(self):
        self.run_publish()
        for rel in ("template.pptx", "template.pdf", "client/q3.pptx"):
            self.assertTrue((self.reports / rel).is_file(), rel)
            self.assertTrue((self.site / rel).is_file(),
                            f"{rel} must stay: quarto reads it back after post-render")

    def test_decks_never_reach_docs(self):
        self.run_publish()
        self.assertEqual([], sorted(self.docs.rglob("*.pptx")))
        self.assertEqual([], sorted(self.docs.rglob("*.pdf")))

    def test_fixtures_are_published_nowhere(self):
        self.run_publish()
        self.assertFalse((self.docs / "tests").exists())
        self.assertFalse((self.reports / "tests").exists())
        self.assertTrue((self.site / "tests/reference-smoke.pptx").is_file(),
                        "fixtures stay in _site so check_pptx can read them")

    def test_nojekyll_is_written(self):
        self.run_publish()
        self.assertTrue((self.docs / ".nojekyll").is_file())

    def test_publishing_never_deletes_what_it_did_not_write(self):
        tree(self.docs, {"CNAME": "slides.example.com", "old/hand-written.html": "keep me"})
        tree(self.reports, {"last-quarter.pptx": "keep me"})
        self.run_publish()
        self.assertEqual("slides.example.com", (self.docs / "CNAME").read_text(encoding="utf8"))
        self.assertTrue((self.docs / "old/hand-written.html").is_file())
        self.assertTrue((self.reports / "last-quarter.pptx").is_file())

    def test_second_publish_overwrites_rather_than_failing(self):
        self.run_publish()
        tree(self.site, {"index.html": "listing v2", "template.pptx": "deck-pptx v2"})
        self.run_publish()
        self.assertEqual("listing v2", (self.docs / "index.html").read_text(encoding="utf8"))
        self.assertEqual("deck-pptx v2", (self.reports / "template.pptx").read_text(encoding="utf8"))

    def test_a_locked_deck_fails_loudly_and_names_the_file(self):
        import shutil
        original = shutil.copy2

        def refuse(src, dst):
            if str(dst).endswith("template.pptx"):
                raise PermissionError(13, "in use")
            return original(src, dst)

        publish.shutil.copy2 = refuse
        self.addCleanup(setattr, publish.shutil, "copy2", original)
        with self.assertRaises(SystemExit) as caught:
            self.run_publish()
        self.assertIn("template.pptx", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
