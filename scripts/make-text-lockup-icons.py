#!/usr/bin/env python3
"""Extract icon-only images for the text-based signature lockups.

The signature renders wordmarks as real HTML text so Outlook's automatic
dark mode converts them to white. Only the icon glyphs stay as images, in
colors that read on both white and dark backgrounds:
  - AO mark recolored to the site accent blue #1f5cf5
  - Lexmark green square kept in its brand greens
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ACCENT = (31, 92, 245)  # #1f5cf5


def tight_trim(arr: np.ndarray, margin: int = 2) -> np.ndarray:
    ys, xs = np.where(arr[..., 3] > 10)
    y0, y1 = max(0, ys.min() - margin), min(arr.shape[0], ys.max() + margin + 1)
    x0, x1 = max(0, xs.min() - margin), min(arr.shape[1], xs.max() + margin + 1)
    return arr[y0:y1, x0:x1]


def main() -> None:
    # AO icon: left of the gap at x=252..285, recolored to accent blue
    ao = np.array(Image.open(ROOT / "assets/logo/automation-one-logo-transparent.png").convert("RGBA"))
    icon = tight_trim(ao[:, :253].copy())
    mask = icon[..., 3] > 0
    icon[mask, 0], icon[mask, 1], icon[mask, 2] = ACCENT
    Image.fromarray(icon).save(ROOT / "assets/logo/ao-icon-accent.png")
    print("ao-icon-accent.png", icon.shape[1], "x", icon.shape[0])

    # Lexmark icon: left of the gap at x=201..284, colors unchanged
    lex = np.array(Image.open(ROOT / "brand-logo-lexmark.png").convert("RGBA"))
    licon = tight_trim(lex[:, :202].copy())
    Image.fromarray(licon).save(ROOT / "brand-logo-lexmark-icon.png")
    print("brand-logo-lexmark-icon.png", licon.shape[1], "x", licon.shape[0])


if __name__ == "__main__":
    main()
