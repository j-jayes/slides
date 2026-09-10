"""Build _extensions/nexer/bg/<rrggbb>.png -- one solid tile per brand colour.

    python tools/build_bg_pngs.py

Pandoc honours `background-image` on a slide heading and writes it into the
slide as a stretched blip fill, but it has no notion of `background-color` for
pptx at any version. So `## Context {background-color="#5A1F9F"}` needs an
actual purple image to point at, and pptx-nexer.lua swaps one in by hex.

Colours are read out of _brand.yml so the two cannot drift; the tiles are
committed, so this only runs when the palette changes.

Deliberately stdlib zlib + struct rather than Pillow: the kit's other build
scripts need Pillow, but a deck does not, and neither should this.
"""
from __future__ import annotations

import re
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "_brand.yml"
OUT = ROOT / "_extensions" / "nexer" / "bg"

# Stretched to fill the slide, so the tile only has to carry the colour. 16:9
# so that any viewer that letterboxes rather than stretches still gets it right.
WIDTH, HEIGHT = 32, 18


def palette() -> dict[str, str]:
    """The `color: palette:` block of _brand.yml, as name -> RRGGBB."""
    text = BRAND.read_text(encoding="utf8")
    block = re.search(r"^color:\n(?:.*\n)*?  palette:\n((?:    .*\n)+)", text, re.M)
    if not block:
        raise SystemExit(f"no color.palette block in {BRAND}")
    found = re.findall(r'^    ([\w-]+):\s*"?#([0-9A-Fa-f]{6})"?', block.group(1), re.M)
    if not found:
        raise SystemExit(f"no colours in the palette block of {BRAND}")
    return {name: hex_ for name, hex_ in found}


def png(hex_: str) -> bytes:
    """A minimal truecolour PNG of one flat colour."""
    r, g, b = (int(hex_[i:i + 2], 16) for i in (0, 2, 4))
    # Each scanline is a filter byte (0 = none) then the raw pixels.
    raw = (b"\x00" + bytes((r, g, b)) * WIDTH) * HEIGHT

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (struct.pack(">I", len(payload)) + kind + payload
                + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))

    return b"".join([
        b"\x89PNG\r\n\x1a\n",
        chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)),
        chunk(b"IDAT", zlib.compress(raw, 9)),
        chunk(b"IEND", b""),
    ])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, hex_ in sorted(palette().items()):
        path = OUT / f"{hex_.lower()}.png"
        path.write_bytes(png(hex_))
        print(f"{name:14} #{hex_.upper()}  {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
