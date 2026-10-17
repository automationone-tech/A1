#!/usr/bin/env python3
"""Generate logo variants with a thin white outline (halo) baked in.

On white backgrounds the halo is invisible, so light mode looks unchanged.
On dark backgrounds the halo keeps dark logo artwork readable even in email
clients (Outlook) that strip the CSS needed for proper image swapping.

Images are rendered at 3x their display size so the halo stays a crisp,
consistent ~2px at display scale.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SCALE = 3  # render at 3x display size

# (source, output, display_width_px, halo_display_px)
JOBS = (
    ("assets/logo/automation-one-logo-transparent.png",
     "assets/logo/automation-one-logo-halo.png", 280, 2.0),
    ("brand-logo-lexmark.png", "brand-logo-lexmark-halo.png", 73, 1.8),
    ("brand-logo-ideal.png", "brand-logo-ideal-halo.png", 37, 1.8),
)


def add_halo(src: Path, dst: Path, display_w: int, halo_display_px: float) -> None:
    img = Image.open(src).convert("RGBA")
    w = display_w * SCALE
    h = round(img.height * w / img.width)
    img = img.resize((w, h), Image.LANCZOS)

    halo_px = max(1, round(halo_display_px * SCALE))

    # Threshold the alpha so stray semi-transparent pixels don't balloon
    alpha = img.split()[3].point(lambda v: 255 if v > 90 else 0)
    size = 2 * halo_px + 1
    halo_alpha = alpha.filter(ImageFilter.MaxFilter(size))
    halo_alpha = halo_alpha.filter(ImageFilter.GaussianBlur(1.0))

    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    empty = Image.new("RGBA", img.size, (255, 255, 255, 0))
    halo = Image.composite(white, empty, halo_alpha)

    out = Image.alpha_composite(halo, img)
    out.save(ROOT / dst)
    print(f"{dst}: {out.size[0]}x{out.size[1]} (display {display_w}px, halo {halo_px}px @3x)")


def main() -> None:
    for src, dst, disp_w, halo_disp in JOBS:
        add_halo(ROOT / src, ROOT / dst, disp_w, halo_disp)


if __name__ == "__main__":
    main()
