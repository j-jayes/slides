"""Export a rendered Reveal.js deck to PDF with headless Chrome.

    python tools/export_pdf.py _site/my-deck.html              # one deck
    python tools/export_pdf.py --post-render                   # every deck that opts in

Quarto has no PDF output for revealjs. The documented route is to open the deck
with `?print-pdf` and drive Chrome's print dialog by hand, which is not something
you want between you and a client deck. This is that route, headless.

Wired up as a project post-render hook in _quarto.yml, so a deck asks for a PDF
from its own front matter:

    ---
    title: "My deck"
    export-pdf: true
    ---

`--run-all-compositor-stages-before-draw` is not optional: without it Chrome
prints before Reveal has laid the slides out and writes a one-page blank. The
page count is checked against the deck for exactly that reason.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

CHROME = Path(os.environ.get("CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe"))


def slide_count(html: str) -> int:
    """Leaf <section> elements, which is what Reveal prints one page each of.

    Quarto nests the `##` slides of a `#` section inside a wrapper <section>,
    so the wrappers have to be discounted or every section is counted twice.
    """
    body = html[html.find('<div class="slides">'):]
    stack: list[bool] = []
    leaves = 0
    for m in re.finditer(r"<section\b|</section>", body):
        if m.group(0) == "</section>":
            if not stack:
                continue
            if not stack.pop():
                leaves += 1
            if stack:
                stack[-1] = True
        else:
            stack.append(False)
    return leaves


def page_count(pdf: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf))


def export(html: Path, pdf: Path) -> None:
    """Print one deck, then assert the PDF actually has its slides in it."""
    url = html.resolve().as_uri() + "?print-pdf"
    result = subprocess.run(
        [
            str(CHROME),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            # Wait for layout to settle, or the PDF comes out blank.
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=30000",
            f"--print-to-pdf={pdf.resolve()}",
            url,
        ],
        capture_output=True,
    )
    if result.returncode != 0 or not pdf.exists():
        raise SystemExit(
            f"chrome failed on {html}:\n{result.stderr.decode('utf8', 'ignore')}"
        )

    slides = slide_count(html.read_text(encoding="utf8", errors="ignore"))
    pages = page_count(pdf.read_bytes())
    if pages < slides:
        raise SystemExit(
            f"{pdf}: {pages} pages for {slides} slides -- Chrome printed before "
            f"Reveal finished laying out. Raise --virtual-time-budget."
        )
    print(f"{pdf}  ({pages} pages, {pdf.stat().st_size // 1024} KB)")


def wants_pdf(qmd: Path) -> bool:
    """Whether the deck's own front matter carries `export-pdf: true`."""
    if not qmd.exists():
        return False
    front = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", qmd.read_text(encoding="utf8", errors="ignore"), re.S)
    return bool(front and re.search(r"^export-pdf:\s*true\s*$", front.group(1), re.M))


def source_of(html: Path) -> Path:
    """The .qmd that produced this output.

    In a project the two are not siblings: the deck is at `template.qmd` and
    its output at `_site/template.html`, so the output directory has to be
    stripped off first. Outside a project they do sit side by side.
    """
    out_dir = os.environ.get("QUARTO_PROJECT_OUTPUT_DIR")
    if out_dir:
        try:
            rel = html.resolve().relative_to(Path(out_dir).resolve())
            return rel.with_suffix(".qmd")
        except ValueError:
            pass          # not under the output dir after all
    return html.with_suffix(".qmd")


def opted_in_outputs() -> list[Path]:
    """The HTML this render produced, filtered to decks that asked for a PDF.

    Quarto sets QUARTO_PROJECT_OUTPUT_FILES for post-render scripts, with paths
    relative to the project directory, which is also the working directory.
    """
    listed = os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "")
    return [
        html
        for line in listed.splitlines()
        if (html := Path(line.strip())).suffix == ".html"
        and wants_pdf(source_of(html))
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="Export a Reveal.js deck to PDF.")
    ap.add_argument("html", nargs="*", type=Path, help="rendered deck(s)")
    ap.add_argument("-o", "--output", type=Path, help="PDF path (single deck only)")
    ap.add_argument(
        "--post-render",
        action="store_true",
        help="take the decks from QUARTO_PROJECT_OUTPUT_FILES, honouring export-pdf",
    )
    args = ap.parse_args()

    if args.post_render:
        if args.html or args.output:
            ap.error("--post-render takes its targets from the environment")
        targets = opted_in_outputs()
    elif args.html:
        targets = args.html
    else:
        ap.error("give a deck to export, or --post-render")

    if args.output and len(targets) != 1:
        ap.error("--output needs exactly one deck")

    if not CHROME.exists() and targets:
        print(f"Chrome not found at {CHROME}; set CHROME to override", file=sys.stderr)
        return 1

    for html in targets:
        if not html.exists():
            print(f"no such deck: {html}", file=sys.stderr)
            return 1
        export(html, args.output or html.with_suffix(".pdf"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
