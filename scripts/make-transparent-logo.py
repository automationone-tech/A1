#!/usr/bin/env python3
"""Faithfully make the Automation One logo background transparent.

No AI redraw: we process the existing pixels only.
  1. Background (near-white lavender) -> transparent via a soft color-distance
     alpha ramp, un-premultiplying edge pixels so no white halo remains.
  2. Nudge ONLY the "Business Systems" sub-line up ~2px (isolated region),
     leaving the AO mark and "Automation One" wordmark pixel-identical.
  3. Export a tight-trim version and a comfortably-padded version.
A gray-card composite is written to .pdf-cache for visual QA only.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

SRC = Path("/Users/home/.cursor/projects/Users-home-Downloads-automation-one-site/"
           "assets/Screenshot_2026-07-13_at_7.40.17_PM-cdff0dbd-3bd5-43b5-9f12-db353c6667eb.png")
OUT_DIR = Path("assets/logo")
QA_DIR = Path(".pdf-cache")

BG = np.array([249.0, 250.0, 255.0])   # measured background
# Region containing only the "Business Systems" sub-line (mark ends x<=254,
# wordmark top line ends at y<=99). Everything here is the sub-line.
SUB_X0 = 255
SUB_Y0 = 100
NUDGE = 2                               # pixels to shift up


def build_rgba(rgb: np.ndarray) -> np.ndarray:
    """Return HxWx4 float RGBA with soft alpha and no bg halo."""
    a = rgb.astype(np.float64)
    dist = np.sqrt(((a - BG) ** 2).sum(2))

    # Representative solid ink colour (median of clearly-inked pixels).
    ink = a[dist > 150]
    C = np.median(ink, axis=0)
    dist_C = np.sqrt(((C - BG) ** 2).sum())

    # Coverage alpha: soft ramp so anti-aliased edges are preserved.
    # low: below this treat as pure background (alpha 0)
    low, high = 8.0, dist_C
    alpha = np.clip((dist - low) / (high - low), 0.0, 1.0)

    # Un-premultiply: recover true ink colour, removing bg contribution on
    # partially covered edge pixels (kills the white halo).
    a_safe = np.clip(alpha, 1e-4, 1.0)[..., None]
    color = (a - (1 - a_safe) * BG) / a_safe
    color = np.clip(color, 0, 255)

    rgba = np.zeros((*rgb.shape[:2], 4), dtype=np.float64)
    rgba[..., :3] = color
    rgba[..., 3] = alpha * 255.0
    # Fully transparent pixels: neutralise stray colour.
    rgba[alpha <= 0.0, :3] = 0
    return rgba


def nudge_subline(rgba: np.ndarray) -> np.ndarray:
    """Shift only the Business Systems region up by NUDGE px."""
    out = rgba.copy()
    region = out[SUB_Y0:, SUB_X0:].copy()
    shifted = np.zeros_like(region)
    shifted[:-NUDGE] = region[NUDGE:]          # move content up
    shifted[-NUDGE:] = 0                        # vacated rows -> transparent
    out[SUB_Y0:, SUB_X0:] = shifted
    return out


def tight_trim(rgba: np.ndarray, margin: int) -> np.ndarray:
    alpha = rgba[..., 3]
    ys, xs = np.where(alpha > 3)
    y0, y1 = ys.min(), ys.max()
    x0, x1 = xs.min(), xs.max()
    y0 = max(0, y0 - margin); x0 = max(0, x0 - margin)
    y1 = min(rgba.shape[0] - 1, y1 + margin)
    x1 = min(rgba.shape[1] - 1, x1 + margin)
    return rgba[y0:y1 + 1, x0:x1 + 1]


def to_img(rgba: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA")


def gray_composite(img: Image.Image, box: int = 16) -> Image.Image:
    """Composite RGBA over a gray checkerboard for QA."""
    w, h = img.size
    bg = Image.new("RGB", (w, h), (200, 200, 205))
    px = bg.load()
    for y in range(h):
        for x in range(w):
            if (x // box + y // box) % 2 == 0:
                px[x, y] = (170, 170, 178)
    bg.paste(img, (0, 0), img)
    return bg


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)

    rgb = np.asarray(Image.open(SRC).convert("RGB"))
    rgba = build_rgba(rgb)
    rgba = nudge_subline(rgba)

    tight = to_img(tight_trim(rgba, margin=6))
    padded_arr = tight_trim(rgba, margin=6)
    # padded: add comfortable even padding around tight crop
    pad = 60
    ph, pw = padded_arr.shape[:2]
    canvas = np.zeros((ph + 2 * pad, pw + 2 * pad, 4), dtype=np.float64)
    canvas[pad:pad + ph, pad:pad + pw] = padded_arr
    padded = to_img(canvas)

    p_tight = OUT_DIR / "automation-one-logo-transparent.png"
    p_pad = OUT_DIR / "automation-one-logo-transparent-padded.png"
    tight.save(p_tight)
    padded.save(p_pad)

    gray_composite(tight).save(QA_DIR / "logo-qa-gray.png")
    gray_composite(padded).save(QA_DIR / "logo-qa-gray-padded.png")

    print("tight ", p_tight, tight.size)
    print("padded", p_pad, padded.size)


if __name__ == "__main__":
    main()
