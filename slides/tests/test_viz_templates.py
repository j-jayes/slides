"""Every viz-* skill template must actually render, and the helpers must format
numbers the way the skills promise.

A skill that ships a chart template nobody has run is worse than no template:
an agent copies it, it fails on ggplot2 4.0 or on a missing package, and the
agent improvises. So each `skills/viz-*/reference/*.R` is executed here with
Rscript, in a temp directory, and must leave behind a PNG (or HTML, for the gt
table) of a plausible size without warnings about deprecated arguments.

    python -m unittest discover -s tests            # everything
    python -m unittest tests.test_viz_templates -k amounts

Templates that declare `# requires: <pkg>` in their header are skipped, with the
install line as the reason, when that package is not installed. Each template
registers the Inter font from Google Fonts, so the suite needs a few seconds per
template and a network connection for the font; offline, the helper falls back
to the device font and the templates still render.
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILLS = REPO / "skills"
HELPERS = SKILLS / "viz-index" / "reference"
NEXER_HELPERS = REPO / "slides" / "R" / "nexer-ggplot.R"
CHECK_SCRIPT = Path(__file__).resolve().parent / "viz_helpers_check.R"
TEMPLATES = sorted(
    p for p in SKILLS.glob("viz-*/reference/*.R") if p.name != "viz.R"
)
# Skills that are prose only, and so ship no chart template.
NO_TEMPLATE_SKILLS = {"viz-index", "viz-review"}


def find_rscript():
    found = shutil.which("Rscript")
    if found:
        return found
    candidates = sorted(Path(r"C:\Program Files\R").glob("R-*/bin/Rscript.exe"))
    if candidates:
        return str(candidates[-1])
    home = os.environ.get("R_HOME")
    if home and (Path(home) / "bin" / "Rscript.exe").is_file():
        return str(Path(home) / "bin" / "Rscript.exe")
    return None


def requires_of(template: Path) -> list[str]:
    """Packages named in a `# requires:` header line, `none` dropped."""
    for line in template.read_text(encoding="utf8").splitlines()[:10]:
        m = re.match(r"#\s*requires:\s*(.*)", line)
        if m:
            return [p for p in re.split(r"[,\s]+", m.group(1).strip()) if p and p != "none"]
    return []


RSCRIPT = find_rscript()


@unittest.skipIf(RSCRIPT is None, "Rscript not found on PATH, in Program Files or R_HOME")
class VizTemplateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out = subprocess.run(
            [RSCRIPT, "-e", "cat(rownames(installed.packages()))"],
            capture_output=True, text=True, timeout=120,
        )
        cls.installed = set(out.stdout.split())

    def test_helpers_format_numbers_as_specified(self):
        env = {**os.environ, "VIZ_HELPERS": str(HELPERS), "NEXER_HELPERS": str(NEXER_HELPERS)}
        r = subprocess.run([RSCRIPT, str(CHECK_SCRIPT)], capture_output=True,
                           text=True, env=env, timeout=120)
        self.assertEqual(0, r.returncode, f"{r.stdout}\n{r.stderr}")

    def test_every_chart_skill_ships_a_template(self):
        for skill in sorted(SKILLS.glob("viz-*")):
            if skill.name in NO_TEMPLATE_SKILLS:
                continue
            with self.subTest(skill=skill.name):
                found = [p for p in (skill / "reference").glob("*.R") if p.name != "viz.R"] \
                    if (skill / "reference").is_dir() else []
                self.assertTrue(found, f"{skill.name} has no reference/*.R template")

    def test_at_least_one_template_exists(self):
        self.assertTrue(TEMPLATES, "no skills/viz-*/reference/*.R templates found")


def _make(template: Path):
    def test(self):
        missing = [p for p in requires_of(template) if p not in self.installed]
        if missing:
            self.skipTest(f"{template.name} needs {', '.join(missing)}: "
                          f"install.packages(c({', '.join(repr(p) for p in missing)}))")
        out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out, True)
        env = {**os.environ, "VIZ_OUT_DIR": str(out), "VIZ_HELPERS": str(HELPERS)}
        r = subprocess.run([RSCRIPT, str(template)], cwd=out, env=env,
                           capture_output=True, text=True, timeout=180)
        self.assertEqual(0, r.returncode, f"{template}\n{r.stdout}\n{r.stderr}")
        self.assertNotIn("deprecated", r.stderr.lower(), f"{template.name} uses a deprecated argument:\n{r.stderr}")
        self.assertNotIn("font family not found", r.stderr.lower(), f"{template.name} drew with an unregistered font:\n{r.stderr}")
        self.assertFalse((out / "Rplots.pdf").exists(),
                         f"{template.name} printed a plot instead of ggsave()")
        written = [f for f in out.iterdir() if f.suffix in (".png", ".html") and f.stat().st_size > 10_000]
        self.assertTrue(written, f"{template.name} wrote no PNG/HTML over 10 KB: "
                                 f"{sorted(p.name for p in out.iterdir())}")
    return test


for _t in TEMPLATES:
    _name = f"test_{_t.parent.parent.name}_{_t.stem}".replace("-", "_")
    setattr(VizTemplateTest, _name, _make(_t))
