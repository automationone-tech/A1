#!/usr/bin/env python3
"""Generate signature logo images with a baked-in white rounded background.

Email clients (especially Outlook) strip <style> blocks from pasted
signatures, so CSS-based light/dark image swapping is unreliable. These
"chip" versions stay readable in dark mode because the white background
is part of the image itself; on a white email background the chip is
invisible.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent

# (source, output, display_width, horiz_pad_display, vert display height of chip)
BRAND_CHIP_HEIGHT = 34  # uniform display height so the row looks tidy
BRANDS = (
    ("brand-logo-canon.png", "brand-logo-canon-chip.png", 76),
    ("brand-logo-fp.png", "brand-logo-fp-chip.png", 43),
    ("brand-logo-lexmark.png", "brand-logo-lexmark-chip.png", 73),
    ("brand-logo-ideal.png", "brand-logo-ideal-chip.png", 37),
    ("brand-logo-xerox.png", "brand-logo-xerox-chip.png", 73),
)
BRAND_HPAD = 8   # display px padding left/right inside chip
BRAND_RADIUS = 8
SCALE = 3        # render at 3x for retina crispness

AO_SRC = ROOT / "assets/logo/automation-one-logo-transparent.png"
AO_OUT = ROOT / "assets/logo/automation-one-logo-chip.png"
AO_DISPLAY_W = 280
AO_PAD = 20
AO_RADIUS = 14


def rounded_white_canvas(w: int, h: int, radius: int) -> Image.Image:
    """White rounded rect on transparent canvas, antialiased via supersampling."""
    ss = 4
    mask = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=radius * ss, fill=255)
    mask = mask.resize((w, h), Image.LANCZOS)
    canvas = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    white = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    canvas.paste(white, (0, 0), mask)
    return canvas


def make_chip(src: Path, dst: Path, logo_disp_w: int, chip_disp_h: int,
              hpad: int, radius: int) -> tuple[int, int]:
    logo = Image.open(src).convert("RGBA")
    aspect = logo.height / logo.width
    logo_w = logo_disp_w * SCALE
    logo_h = round(logo_w * aspect)
    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

    chip_w = (logo_disp_w + 2 * hpad) * SCALE
    chip_h = chip_disp_h * SCALE
    chip = rounded_white_canvas(chip_w, chip_h, radius * SCALE)
    chip.alpha_composite(logo, ((chip_w - logo_w) // 2, (chip_h - logo_h) // 2))
    chip.save(dst)
    disp = (chip_w // SCALE, chip_h // SCALE)
    print(f"{dst.name}: display {disp[0]}x{disp[1]}")
    return disp


def main() -> None:
    for src_name, dst_name, disp_w in BRANDS:
        make_chip(ROOT / src_name, ROOT / dst_name, disp_w,
                  BRAND_CHIP_HEIGHT, BRAND_HPAD, BRAND_RADIUS)

    # Automation One lockup: taller chip sized from its aspect ratio
    logo = Image.open(AO_SRC)
    ao_disp_h = round(AO_DISPLAY_W * logo.height / logo.width) + 2 * AO_PAD
    make_chip(AO_SRC, AO_OUT, AO_DISPLAY_W, ao_disp_h, AO_PAD, AO_RADIUS)


if __name__ == "__main__":
    main()
