"""Screenshot rendered Reveal.js slides with headless Chrome.

Verification aid: a deck that renders is not the same as a deck that looks right.

    python tools/shoot_slides.py template.html market-context bridge
    python tools/shoot_slides.py template.html --all

Slides are addressed by their section id (the heading, slugified), because
Quarto nests `##` slides vertically under each `#` section and a bare `#/n`
only walks the horizontal axis.

Images land in <scratch>/slideshots/ so they never pollute the repo.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def out_dir() -> Path:
    scratch = os.environ.get("CLAUDE_SCRATCHPAD") or os.environ.get("TEMP") or "."
    d = Path(scratch) / "slideshots"
    d.mkdir(parents=True, exist_ok=True)
    return d


def slide_ids(html: Path) -> list[str]:
    """Section ids in document order, skipping Quarto's wrapper sections."""
    text = html.read_text(encoding="utf8", errors="ignore")
    body = text[text.find('<div class="slides">'):]
    return re.findall(r'<section[^>]*id="([^"]+)"', body)


def shoot(html: Path, slide: str, dest: Path) -> Path:
    url = html.resolve().as_uri() + f"#/{slide}"
    png = dest / f"{slide}.png"
    subprocess.run(
        [
            str(CHROME),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            "--window-size=1600,900",
            "--virtual-time-budget=9000",
            f"--screenshot={png}",
            url,
        ],
        check=True,
        capture_output=True,
    )
    return png


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html", type=Path)
    ap.add_argument("slides", nargs="*")
    ap.add_argument("--all", action="store_true", help="every slide in the deck")
    args = ap.parse_args()

    if not CHROME.exists():
        print(f"Chrome not found at {CHROME}", file=sys.stderr)
        return 1

    targets = list(args.slides)
    if args.all or not targets:
        targets = slide_ids(args.html)
    dest = out_dir()
    for t in targets:
        print(shoot(args.html, t, dest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
