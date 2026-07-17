#!/usr/bin/env python3
"""Rebuild brand logos with white ink for dark-mode email signatures.

Preserves original shapes, alpha, and anti-aliasing. Brand colors that
already read on dark backgrounds (Lexmark greens, Ideal.MBM red) are kept.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def to_white_preserving_alpha(src: Path, dst: Path) -> None:
    """Every ink pixel becomes white; alpha (anti-alias) is unchanged."""
    arr = np.array(Image.open(src).convert("RGBA"), dtype=np.float64)
    a = arr[..., 3]
    ink = a > 0
    arr[ink, 0] = 255
    arr[ink, 1] = 255
    arr[ink, 2] = 255
    # Keep original alpha so soft edges stay soft
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA").save(dst)
    print(f"white lockup: {dst.name} {Image.open(dst).size}")


def recolor_dark_neutrals_to_white(src: Path, dst: Path) -> None:
    """Keep brand greens/reds; turn dark grey/black ink white."""
    arr = np.array(Image.open(src).convert("RGBA"), dtype=np.float64)
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]

    is_green = (g > r * 1.15) & (g > b * 1.05) & (g > 55)
    is_red = (r > g * 1.15) & (r > b * 1.05) & (r > 80)
    is_brand = is_green | is_red

    max_rgb = np.maximum(np.maximum(r, g), b)
    # Dark neutrals (and near-black anti-alias) -> white
    dark = (~is_brand) & (a > 8) & (max_rgb < 220)

    out = arr.copy()
    out[dark, 0] = 255
    out[dark, 1] = 255
    out[dark, 2] = 255
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA").save(dst)
    print(f"white neutrals: {dst.name} {Image.open(dst).size}")


def main() -> None:
    out_logo = ROOT / "assets/logo"
    out_logo.mkdir(parents=True, exist_ok=True)

    # Full Automation One lockup -> pure white (same geometry as light logo)
    to_white_preserving_alpha(
        ROOT / "assets/logo/automation-one-logo-transparent.png",
        out_logo / "automation-one-logo-white.png",
    )

    # Lexmark: keep green mark, white wordmark
    recolor_dark_neutrals_to_white(
        ROOT / "brand-logo-lexmark.png",
        ROOT / "brand-logo-lexmark-white.png",
    )

    # Ideal.MBM: keep red MBM, white leaf / IDEAL / CORPORATION
    recolor_dark_neutrals_to_white(
        ROOT / "brand-logo-ideal.png",
        ROOT / "brand-logo-ideal-white.png",
    )

    # Also keep -dark aliases pointing at the same files for older signatures
    for src_name, alias in (
        ("brand-logo-lexmark-white.png", "brand-logo-lexmark-dark.png"),
        ("brand-logo-ideal-white.png", "brand-logo-ideal-dark.png"),
    ):
        data = (ROOT / src_name).read_bytes()
        (ROOT / alias).write_bytes(data)
        print(f"alias {alias}")


if __name__ == "__main__":
    main()
