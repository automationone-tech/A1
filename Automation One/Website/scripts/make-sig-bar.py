#!/usr/bin/env python3
"""Generate vertical accent bar PNGs for email signatures (rounded left edge)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets/signature/icons"

DISPLAY_W = 5
DISPLAY_H = 340
RADIUS = 4
SCALE = 3

BARS = (
    ("sig-bar-navy.png", (0, 42, 118)),   # #002a76
    ("sig-bar-white.png", (255, 255, 255)),
)


def make_bar(name: str, rgb: tuple[int, int, int]) -> None:
    w, h = DISPLAY_W * SCALE, DISPLAY_H * SCALE
    r = RADIUS * SCALE
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Left-rounded pill: straight right edge, rounded top-left + bottom-left only
    draw.rectangle([0, r, w - 1, h - r - 1], fill=(*rgb, 255))
    draw.pieslice([0, 0, 2 * r - 1, 2 * r - 1], 180, 270, fill=(*rgb, 255))
    draw.rectangle([r - 1, 0, w - 1, r - 1], fill=(*rgb, 255))
    draw.pieslice([0, h - 2 * r, 2 * r - 1, h - 1], 90, 180, fill=(*rgb, 255))
    draw.rectangle([r - 1, h - r, w - 1, h - 1], fill=(*rgb, 255))
    dst = OUT_DIR / name
    img.save(dst)
    print(f"{dst.name}: {DISPLAY_W}x{DISPLAY_H} display, radius {RADIUS}px left")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, rgb in BARS:
        make_bar(name, rgb)


if __name__ == "__main__":
    main()
