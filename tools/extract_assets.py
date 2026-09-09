"""Extract Nexer brand assets from the corporate deck into assets/.

Run from anywhere:  python tools/extract_assets.py
Source of truth is temp/Sales presentation 2026.pptx -- nothing here is hand-drawn.
"""
import io
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "temp" / "Sales presentation 2026.pptx"
OUT = ROOT / "assets"

# Verified by decoding the PNGs: image23 is the white wordmark on transparent,
# image4 is the same mark in black but only 186x41.
LOGO_WHITE = "ppt/media/image23.png"
# Full-bleed 2000x1125 "swirl" backgrounds from the '... - swirl alt N' layouts.
# image7 is a white swirl on white, image11 a black swirl on black; both keep the
# left ~60% of the frame empty, which is where slide text goes.
SWIRLS = {"ppt/media/image7.png": "swirl-light.jpg", "ppt/media/image11.png": "swirl-dark.jpg"}

# The corporate deck is not tracked in this repo, so this script only runs when
# a copy has been placed under temp/.
MISSING_DECK = """source deck not found: {deck}

The corporate deck is not kept in this repo -- it is ~90 MB and only needed to
regenerate assets. Put a copy at

  temp/Sales presentation 2026.pptx

and re-run. The assets it produces are committed, so you only need this when the
corporate deck itself changes."""


def main() -> None:
    if not DECK.exists():
        raise SystemExit(MISSING_DECK.format(deck=DECK))
    OUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DECK) as z:
        white = Image.open(io.BytesIO(z.read(LOGO_WHITE))).convert("RGBA")
        white.save(OUT / "nexer-logo-white.png")

        # The black wordmark shipped in the deck is 186x41 -- too small to use.
        # Recolour the high-res white mark instead, preserving its alpha.
        black = Image.new("RGBA", white.size, (0, 0, 0, 0))
        black.putalpha(white.getchannel("A"))
        black.save(OUT / "nexer-logo.png")

        # Favicon: the "n" is not separable from the wordmark, so use a solid
        # Nexer-purple rounded tile as a stand-in.
        fav = Image.new("RGBA", (256, 256), (0x5A, 0x1F, 0x9F, 255))
        fav.save(OUT / "favicon.png")

        for src, name in SWIRLS.items():
            im = Image.open(io.BytesIO(z.read(src))).convert("RGB")
            im.thumbnail((1600, 900), Image.LANCZOS)
            im.save(OUT / name, quality=82, optimize=True)

    for p in sorted(OUT.iterdir()):
        print(f"{p.name:24} {p.stat().st_size:>8,} bytes")


if __name__ == "__main__":
    main()
