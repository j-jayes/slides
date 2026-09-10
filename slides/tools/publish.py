"""Lift the rendered site out of _site/ into its two destinations.

    python tools/publish.py          # wired up as a project post-render step

Quarto has one output directory per project, but this kit produces two kinds of
thing that want to go to different places:

  docs/      the Reveal.js decks and the listing page, served by GitHub Pages
             ("deploy from branch: main, /docs"). Committed.
  reports/   the .pptx and any .pdf -- what you actually send a colleague.
             Not committed; regenerate with `quarto render`.

Everything is copied, not moved. Quarto reads a rendered .pptx back *after*
post-render scripts have run, so moving one out of _site/ makes any incremental
`quarto render my-deck.qmd` fail with "readfile ... _site/my-deck.pptx". _site/
is a build directory nobody opens, so the duplicate costs nothing.

Neither destination is ever wiped: a cookiecutter docs/ may hold a CNAME or
hand-written pages this project knows nothing about. The cost is that a
renamed deck leaves its old page behind -- delete docs/ and re-render to clear
it.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

# _site subdirectories that are kit fixtures rather than decks. They stay put:
# tools/check_pptx.py reads them straight out of _site.
UNPUBLISHED = {"tests"}

# Suffixes that go to reports/ instead of docs/.
SHAREABLE = {".pptx", ".pdf"}


def publish(site: Path, docs: Path, reports: Path) -> dict[str, int]:
    """Distribute everything under `site`. Returns counts, for the log line."""
    counts = {"docs": 0, "reports": 0}
    if not site.is_dir():
        raise SystemExit(f"nothing to publish: {site} does not exist")

    for src in sorted(site.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(site)
        if rel.parts[0] in UNPUBLISHED:
            continue

        shareable = src.suffix.lower() in SHAREABLE
        dest = (reports if shareable else docs) / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dest)
        except PermissionError as exc:
            # Almost always the deck open in PowerPoint. Say which one, and
            # fail the render: a half-published set is worse than none.
            raise SystemExit(f"cannot write {dest}: {exc.strerror}. "
                             f"Close it and re-render.") from exc
        counts["reports" if shareable else "docs"] += 1

    # GitHub Pages runs Jekyll over the branch otherwise, which eats the
    # underscore-prefixed directories Quarto emits. Quarto does not write this.
    docs.mkdir(parents=True, exist_ok=True)
    (docs / ".nojekyll").touch()
    return counts


def main() -> int:
    # Post-render scripts run with the project directory as the working dir.
    project = Path.cwd()
    counts = publish(project / "_site", project.parent / "docs",
                     project.parent / "reports")
    print(f"published {counts['docs']} files to docs/, "
          f"{counts['reports']} to reports/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
