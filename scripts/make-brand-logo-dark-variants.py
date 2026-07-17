#!/usr/bin/env python3
"""Generate dark-mode brand logo variants for email signatures.

Recolors dark neutral pixels to white while preserving brand colors
(green for Lexmark icon, red for Ideal.MBM).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent

BRANDS = (
    ("brand-logo-lexmark.png", "brand-logo-lexmark-dark.png"),
    ("brand-logo-ideal.png", "brand-logo-ideal-dark.png"),
)


def make_dark_mode_variant(src: Path, dst: Path) -> None:
    img = np.array(Image.open(src).convert("RGBA"), dtype=np.float64)
    r, g, b, a = img[..., 0], img[..., 1], img[..., 2], img[..., 3]

    is_green = (g > r * 1.15) & (g > b * 1.05) & (g > 55)
    is_red = (r > g * 1.15) & (r > b * 1.05) & (r > 80)
    is_brand_color = is_green | is_red

    max_rgb = np.maximum(np.maximum(r, g), b)
    dark = (~is_brand_color) & (a > 8) & (max_rgb < 220)

    out = img.copy()
    out[dark, 0] = 255
    out[dark, 1] = 255
    out[dark, 2] = 255

    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA").save(dst)
    print(dst)


def main() -> None:
    for src_name, dst_name in BRANDS:
        make_dark_mode_variant(ROOT / src_name, ROOT / dst_name)


if __name__ == "__main__":
    main()
