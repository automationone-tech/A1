#!/usr/bin/env python3
"""Automation One — Brand Guidelines (4 pages).

A tight, premium 4-page identity guide:
  1. Cover
  2. Logo
  3. Colour
  4. Typography
"""

from __future__ import annotations

import io
import math
import os
import shutil
from pathlib import Path

from reportlab.lib.colors import HexColor, Color
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as canvas_mod

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[misc, assignment]

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------

BASE = Path(__file__).resolve().parent
FONTS_DIR = BASE / "fonts"
OUTPUT_SITE = BASE / "Automation-One-Brand-Guidelines.pdf"
OUTPUT_DOWNLOADS = Path.home() / "Downloads" / "Automation-One-Brand-Guidelines.pdf"

LOGO_PRIMARY = BASE / "ao-nav-logo-primary.png"   # brand blue mark
LOGO_BLUE_900 = BASE / "ao-nav-logo-061a4a.png"   # Blue 900 mark
LOGO_REVERSE = BASE / "ao-nav-logo-ffffff.png"    # white mark
LOGO_BLACK = BASE / "ao-nav-logo-000000.png"      # mono black mark
LOCKUP_STACKED_PRIMARY = BASE / "ao-logo-lockup-stacked-primary.png"
LOCKUP_STACKED_WHITE = BASE / "ao-logo-lockup-stacked-white.png"
LOCKUP_HORIZONTAL_PRIMARY = BASE / "ao-logo-lockup-horizontal-primary.png"
LOCKUP_HORIZONTAL_BLUE500 = BASE / ".pdf-cache" / "horizontal-lockup-blue500.png"
LOCKUP_ASPECT = 685 / 704  # stacked lockup height / width (reference proportions)
LOCKUP_H_ASPECT = 136 / 636  # horizontal lockup height / width (reference screenshot)
LOCKUP_COVER_WHITE = BASE / ".pdf-cache" / "cover-lockup-white-on-black.png"
BLACK_COLORKEY = [0, 0, 0, 0, 0, 0]  # knock out black bg → crisp #FFFFFF logo

PAGE_W, PAGE_H = letter

# Generous editorial margins
MARGIN = 18 * mm

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

BLUE_50  = HexColor("#eef4ff")
BLUE_100 = HexColor("#d9e6ff")
BLUE_200 = HexColor("#b3ccff")
BLUE_300 = HexColor("#7ea7ff")
BLUE_400 = HexColor("#4a82ff")
BLUE_500 = HexColor("#1f5cf5")
BLUE_600 = HexColor("#1547d1")
BLUE_700 = HexColor("#0f389e")
BLUE_800 = HexColor("#0a2870")
BLUE_900 = HexColor("#061a4a")
TEXT_SOFT = HexColor("#0f389e")  # Blue 700 — supporting copy on light surfaces
PAPER    = HexColor("#f8faff")
WHITE    = HexColor("#ffffff")

PALETTE = [
    ("Blue 50",  "#eef4ff"),
    ("Blue 100", "#d9e6ff"),
    ("Blue 200", "#b3ccff"),
    ("Blue 300", "#7ea7ff"),
    ("Blue 400", "#4a82ff"),
    ("Blue 500", "#1f5cf5"),   # primary
    ("Blue 600", "#1547d1"),
    ("Blue 700", "#0f389e"),
    ("Blue 800", "#0a2870"),
    ("Blue 900", "#061a4a"),
]

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

FONT_BOOK = "Helvetica"
FONT_MED  = "Helvetica"
FONT_SEMI = "Helvetica-Bold"


def register_fonts() -> None:
    """Register Sequel Sans if available; fall back to Helvetica."""
    global FONT_BOOK, FONT_MED, FONT_SEMI

    candidates = {
        "SequelSans-Book": "SequelSans-DisplayBook.DS_QNCiF.ttf",
        "SequelSans-Display": "SequelSans-Display.BSxqJqbM.ttf",
        "SequelSans-Medium": "SequelSans-DisplayMedium.BYsR-9NK.ttf",
        "SequelSans-Semi": "SequelSans-DisplaySemi.BFge39nV.ttf",
    }
    registered = {}
    for name, fname in candidates.items():
        p = FONTS_DIR / fname
        if p.exists():
            try:
                pdfmetrics.registerFont(TTFont(name, str(p)))
                registered[name] = True
            except Exception:
                pass

    if "SequelSans-Book" in registered:
        FONT_BOOK = "SequelSans-Book"
    elif "SequelSans-Display" in registered:
        FONT_BOOK = "SequelSans-Display"
    if "SequelSans-Medium" in registered:
        FONT_MED = "SequelSans-Medium"
    if "SequelSans-Semi" in registered:
        FONT_SEMI = "SequelSans-Semi"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hex_to_cmyk(h: str) -> tuple[int, int, int, int]:
    r, g, b = hex_to_rgb(h)
    rf, gf, bf = r / 255, g / 255, b / 255
    k = 1 - max(rf, gf, bf)
    if k >= 1:
        return (0, 0, 0, 100)
    c = (1 - rf - k) / (1 - k)
    m = (1 - gf - k) / (1 - k)
    y = (1 - bf - k) / (1 - k)
    return tuple(round(v * 100) for v in (c, m, y, k))


def draw_vertical_gradient(c: canvas_mod.Canvas, x: float, y: float, w: float, h: float,
                            top: Color, bottom: Color, steps: int = 220) -> None:
    """Draw a smooth vertical gradient as N thin rectangles."""
    for i in range(steps):
        t = i / (steps - 1)
        r = top.red   + (bottom.red   - top.red)   * t
        g = top.green + (bottom.green - top.green) * t
        b = top.blue  + (bottom.blue  - top.blue)  * t
        c.setFillColorRGB(r, g, b)
        seg_h = h / steps
        c.rect(x, y + h - (i + 1) * seg_h, w, seg_h + 0.4, stroke=0, fill=1)


def draw_radial_glow(c: canvas_mod.Canvas, cx: float, cy: float, max_r: float,
                     inner: Color, alpha: float = 0.55, rings: int = 60) -> None:
    """Cheap radial highlight using stacked translucent circles."""
    for i in range(rings, 0, -1):
        t = i / rings
        a = alpha * (1 - t) ** 2
        c.setFillColorRGB(inner.red, inner.green, inner.blue, alpha=a)
        c.circle(cx, cy, max_r * t, stroke=0, fill=1)


def ensure_blue900_logo() -> Path:
    """Build Blue 900 mark asset from the primary mark."""
    if LOGO_BLUE_900.exists() or Image is None or not LOGO_PRIMARY.exists():
        return LOGO_BLUE_900
    im = Image.open(LOGO_PRIMARY).convert("RGBA")
    px = im.load()
    tr, tg, tb = hex_to_rgb("#061a4a")
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, g, b, a = px[x, y]
            if a < 16:
                continue
            px[x, y] = (tr, tg, tb, a)
    im.save(LOGO_BLUE_900)
    return LOGO_BLUE_900


def build_horizontal_lockup_blue500() -> Path | None:
    """Reference horizontal lockup → Blue 500, preserving original stroke weight."""
    src = LOCKUP_HORIZONTAL_PRIMARY
    if not src.exists() or Image is None:
        return None

    im = Image.open(src).convert("RGBA")
    tr, tg, tb = hex_to_rgb("#1f5cf5")
    bg = (248.0, 250.0, 255.0)
    core = (49.0, 68.0, 142.0)
    max_dist = math.sqrt(sum((c - b) ** 2 for c, b in zip(core, bg)))

    px = im.load()
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    op = out.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, g, b, a = px[x, y]
            if r > 240 and g > 242 and b > 248:
                continue
            dist = math.sqrt((r - bg[0]) ** 2 + (g - bg[1]) ** 2 + (b - bg[2]) ** 2)
            alpha = min(255, max(0, int(255 * dist / max_dist)))
            if alpha < 6:
                continue
            op[x, y] = (tr, tg, tb, alpha)

    out = out.resize((out.width * 2, out.height * 2), Image.LANCZOS)
    LOCKUP_HORIZONTAL_BLUE500.parent.mkdir(exist_ok=True)
    out.save(LOCKUP_HORIZONTAL_BLUE500)
    return LOCKUP_HORIZONTAL_BLUE500


def horizontal_lockup_size(h: float) -> tuple[float, float]:
    """Width and height from reference horizontal lockup aspect ratio."""
    return h / LOCKUP_H_ASPECT, h


def build_cover_lockup_white(path: Path) -> Path | None:
    """White logo on black (no alpha) — color-key renders true white in PDF."""
    if not path.exists() or Image is None:
        return None

    pil = Image.open(path).convert("RGBA")
    w, h = pil.size
    px = pil.load()
    out = Image.new("RGB", (w, h), (0, 0, 0))
    op = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 128:
                continue
            if r > 235 and g > 235 and b > 235:
                continue
            op[x, y] = (255, 255, 255)

    LOCKUP_COVER_WHITE.parent.mkdir(exist_ok=True)
    out.save(LOCKUP_COVER_WHITE)
    return LOCKUP_COVER_WHITE


def page_meta(c: canvas_mod.Canvas, label: str, page_num: int, *, dark: bool = False) -> None:
    """Footer + corner page meta on every interior page."""
    ink = WHITE if dark else BLUE_900
    soft = HexColor("#aac1ff") if dark else HexColor("#6478b5")
    c.setStrokeColor(soft if dark else HexColor("#d3dcf2"))
    c.setLineWidth(0.5)
    c.line(MARGIN, MARGIN + 12, PAGE_W - MARGIN, MARGIN + 12)

    c.setFillColor(soft)
    c.setFont(FONT_MED, 8)
    c.drawString(MARGIN, MARGIN, "AUTOMATION ONE  ·  BRAND GUIDELINES")
    c.setFillColor(ink)
    c.setFont(FONT_MED, 8)
    c.drawRightString(PAGE_W - MARGIN, MARGIN, f"{label.upper()}   ·   {page_num:02d}")


# ---------------------------------------------------------------------------
# Page 1 — Cover
# ---------------------------------------------------------------------------

def draw_cover(c: canvas_mod.Canvas) -> None:
    # Deep blue editorial gradient
    draw_vertical_gradient(c, 0, 0, PAGE_W, PAGE_H, BLUE_800, BLUE_900)

    # Two subtle highlights for depth
    draw_radial_glow(c, PAGE_W * 0.82, PAGE_H * 0.88, PAGE_W * 0.55,
                     HexColor("#3868f7"), alpha=0.50, rings=70)
    draw_radial_glow(c, PAGE_W * 0.16, PAGE_H * 0.10, PAGE_W * 0.55,
                     HexColor("#1f5cf5"), alpha=0.42, rings=70)

    # Hairline frame
    c.setStrokeColorRGB(1, 1, 1, alpha=0.22)
    c.setLineWidth(0.7)
    c.rect(MARGIN, MARGIN, PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN, stroke=1, fill=0)

    # Top eyebrow
    c.setFillColorRGB(1, 1, 1, alpha=0.78)
    c.setFont(FONT_MED, 9)
    c.drawRightString(PAGE_W - MARGIN - 12 * mm, PAGE_H - MARGIN - 12 * mm,
                      "VOL. 01  ·  JUN 2026")

    # Stacked lockup — original proportions, rendered white
    c.setFillColor(WHITE)  # reset fill alpha (glow/eyebrow leave ca < 1 → grey logo)
    lockup_w = 112 * mm
    lockup_h = lockup_w * LOCKUP_ASPECT
    lx = (PAGE_W - lockup_w) / 2
    ly = PAGE_H * 0.56 - lockup_h / 2
    lockup_src = LOCKUP_STACKED_PRIMARY if LOCKUP_STACKED_PRIMARY.exists() else LOCKUP_STACKED_WHITE
    lockup_path = build_cover_lockup_white(lockup_src)
    if lockup_path:
        c.drawImage(str(lockup_path), lx, ly, lockup_w, lockup_h,
                    mask=BLACK_COLORKEY, preserveAspectRatio=True)

    # Tagline + title block (tagline above)
    tagline_x = MARGIN + 12 * mm
    c.setFillColor(WHITE)
    c.setFont(FONT_MED, 28)
    c.drawString(tagline_x, PAGE_H * 0.275, "Business Solutions")
    c.drawString(tagline_x, PAGE_H * 0.235, "Made Simple.")

    c.setFillColor(WHITE)
    c.setFont(FONT_MED, 10)
    c.drawCentredString(PAGE_W / 2, PAGE_H * 0.16, "B R A N D   G U I D E L I N E S")

    # Footer
    c.setStrokeColorRGB(1, 1, 1, alpha=0.22)
    c.setLineWidth(0.5)
    c.line(MARGIN + 12 * mm, MARGIN + 18 * mm,
           PAGE_W - MARGIN - 12 * mm, MARGIN + 18 * mm)

    c.setFillColorRGB(1, 1, 1, alpha=0.68)
    c.setFont(FONT_MED, 8)
    c.drawRightString(PAGE_W - MARGIN - 12 * mm, MARGIN + 11 * mm,
                      "INTERNAL USE   ·   © 2026 AUTOMATION ONE BUSINESS SYSTEMS INC.")

    c.showPage()


# ---------------------------------------------------------------------------
# Section header helper (interior pages)
# ---------------------------------------------------------------------------

def draw_section_head(c: canvas_mod.Canvas, num: str, label: str, title: str,
                       subtitle: str) -> float:
    y_top = PAGE_H - MARGIN - 10 * mm

    # Section number (large, light)
    c.setFillColor(BLUE_100)
    c.setFont(FONT_MED, 90)
    c.drawString(MARGIN, y_top - 28 * mm, num)

    # Section label
    c.setFillColor(BLUE_700)
    c.setFont(FONT_MED, 9)
    c.drawString(MARGIN + 50 * mm, y_top - 6 * mm, label.upper())

    # Title
    c.setFillColor(BLUE_900)
    c.setFont(FONT_MED, 32)
    c.drawString(MARGIN + 50 * mm, y_top - 18 * mm, title)

    # Subtitle
    c.setFillColor(TEXT_SOFT)
    c.setFont(FONT_BOOK, 11)
    c.drawString(MARGIN + 50 * mm, y_top - 26 * mm, subtitle)

    # Divider
    c.setStrokeColor(HexColor("#d3dcf2"))
    c.setLineWidth(0.6)
    c.line(MARGIN, y_top - 36 * mm, PAGE_W - MARGIN, y_top - 36 * mm)

    return y_top - 36 * mm  # y position below header for body content


# ---------------------------------------------------------------------------
# Page 2 — Logo
# ---------------------------------------------------------------------------

def draw_logo_page(c: canvas_mod.Canvas) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    y = draw_section_head(c, "01", "Logo", "The mark",
                          "Primary identity, clear-space and minimum sizes.")

    # ---- Hero lockup with clear-space cage ----
    lockup_h = 30 * mm
    lockup_path = build_horizontal_lockup_blue500()
    lockup_w, _ = horizontal_lockup_size(lockup_h)

    pad = lockup_h * 0.5  # "X" = half lockup height
    cage_w = lockup_w + pad * 2
    cage_h = lockup_h + pad * 2
    cage_x = MARGIN + (PAGE_W - 2 * MARGIN - cage_w) / 2
    hero_x = cage_x + pad
    hero_y = y - 28 * mm - cage_h + pad
    cage_y = hero_y - pad

    # Cage
    c.setStrokeColor(BLUE_300)
    c.setDash(2, 2)
    c.setLineWidth(0.8)
    c.rect(cage_x, cage_y, cage_w, cage_h, stroke=1, fill=0)
    c.setDash()

    # Primary lockup — reference image, all Blue 500
    c.setFillColor(WHITE)
    if lockup_path:
        c.drawImage(str(lockup_path), hero_x, hero_y, lockup_w, lockup_h, mask="auto")

    # Corner "X" markers + label
    tick = pad
    for cx_, cy_ in [(cage_x, cage_y), (cage_x + cage_w, cage_y),
                     (cage_x, cage_y + cage_h), (cage_x + cage_w, cage_y + cage_h)]:
        c.setFillColor(BLUE_500)
        c.circle(cx_, cy_, 1.4, stroke=0, fill=1)

    c.setFillColor(BLUE_700)
    c.setFont(FONT_MED, 8)
    c.drawString(cage_x, cage_y + cage_h + 3 * mm, "CLEAR SPACE")
    c.setFillColor(TEXT_SOFT)
    c.setFont(FONT_BOOK, 8)
    c.drawRightString(cage_x + cage_w, cage_y + cage_h + 3 * mm,
                       "X  =  1/2 mark height")

    # ---- Variant row (4 across) ----
    ensure_blue900_logo()
    grid_top = cage_y - 12 * mm
    gap = 5 * mm
    cell_w = (PAGE_W - 2 * MARGIN - 3 * gap) / 4
    cell_h = 32 * mm
    cells = [
        ("Primary",   LOGO_PRIMARY,    WHITE,    BLUE_500,  HexColor("#dbe5fc")),
        ("Blue 900",  LOGO_BLUE_900,   WHITE,    BLUE_900,  HexColor("#dbe5fc")),
        ("Reverse",   LOGO_REVERSE,    BLUE_800, WHITE,     None),
        ("Mono",      LOGO_BLACK,      WHITE,    BLUE_900,  HexColor("#dbe5fc")),
    ]
    for i, (name, logo, bg, txt, border) in enumerate(cells):
        x = MARGIN + i * (cell_w + gap)
        yy = grid_top - cell_h
        c.setFillColor(bg)
        c.rect(x, yy, cell_w, cell_h, stroke=0, fill=1)
        if border:
            c.setStrokeColor(border)
            c.setLineWidth(0.6)
            c.rect(x, yy, cell_w, cell_h, stroke=1, fill=0)
        # Mark only (no wordmark for these small chips)
        ratio = 288 / 416
        mh = 12 * mm
        mw = mh / ratio
        if logo.exists():
            c.drawImage(ImageReader(str(logo)),
                        x + (cell_w - mw) / 2,
                        yy + (cell_h - mh) / 2 + 4 * mm,
                        mw, mh, mask="auto")
        # Label
        c.setFillColor(txt if name != "Reverse" else WHITE)
        c.setFont(FONT_MED, 8)
        c.drawCentredString(x + cell_w / 2, yy + 5 * mm, name.upper())

    # ---- Minimum sizes + don'ts ----
    base_y = MARGIN + 22 * mm
    half = (PAGE_W - 2 * MARGIN - 8 * mm) / 2

    # Min sizes
    c.setFillColor(WHITE)
    c.rect(MARGIN, base_y, half, 28 * mm, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#dbe5fc"))
    c.setLineWidth(0.6)
    c.rect(MARGIN, base_y, half, 28 * mm, stroke=1, fill=0)

    c.setFillColor(BLUE_700)
    c.setFont(FONT_MED, 8)
    c.drawString(MARGIN + 6 * mm, base_y + 21 * mm, "MINIMUM SIZE")
    c.setFillColor(BLUE_900)
    c.setFont(FONT_MED, 11)
    c.drawString(MARGIN + 6 * mm, base_y + 14 * mm, "Digital   ·   30 px wordmark height  /  50 px mark")
    c.drawString(MARGIN + 6 * mm, base_y + 7 * mm, "Print       ·   10 pt wordmark             /  8 mm mark")

    # Don'ts
    dx = MARGIN + half + 8 * mm
    c.setFillColor(WHITE)
    c.rect(dx, base_y, half, 28 * mm, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#dbe5fc"))
    c.rect(dx, base_y, half, 28 * mm, stroke=1, fill=0)

    c.setFillColor(BLUE_700)
    c.setFont(FONT_MED, 8)
    c.drawString(dx + 6 * mm, base_y + 21 * mm, "DON'T")
    c.setFillColor(BLUE_900)
    c.setFont(FONT_BOOK, 9.5)
    donts = [
        "Recolour the mark outside the approved palette.",
        "Stretch, skew, rotate or add drop shadows.",
        "Place the mark on busy imagery without a scrim.",
    ]
    for i, line in enumerate(donts):
        c.drawString(dx + 6 * mm, base_y + 14 * mm - i * 5 * mm, "—  " + line)

    page_meta(c, "Logo", 2)
    c.showPage()


# ---------------------------------------------------------------------------
# Page 3 — Colour
# ---------------------------------------------------------------------------

def draw_colour_page(c: canvas_mod.Canvas) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    y = draw_section_head(c, "02", "Colour", "Primary palette",
                          "A confident, single-hue system anchored by Blue 500.")

    # ---- Hero swatch: primary ----
    hero_w = (PAGE_W - 2 * MARGIN) * 0.50
    hero_h = 78 * mm
    hero_x = MARGIN
    hero_y = y - hero_h - 6 * mm
    c.setFillColor(BLUE_500)
    c.rect(hero_x, hero_y, hero_w, hero_h, stroke=0, fill=1)

    c.setFillColor(WHITE)
    c.setFont(FONT_MED, 9)
    c.drawString(hero_x + 8 * mm, hero_y + hero_h - 10 * mm, "PRIMARY")
    c.setFont(FONT_MED, 30)
    c.drawString(hero_x + 8 * mm, hero_y + hero_h - 22 * mm, "Blue 500")
    c.setFont(FONT_BOOK, 10)
    c.setFillColorRGB(1, 1, 1, alpha=0.82)
    c.drawString(hero_x + 8 * mm, hero_y + hero_h - 30 * mm,
                 "The signature mark. Reserve for primary CTAs,")
    c.drawString(hero_x + 8 * mm, hero_y + hero_h - 35 * mm,
                 "brand surfaces, and headline accents.")

    rgb = hex_to_rgb("#1f5cf5")
    cmyk = hex_to_cmyk("#1f5cf5")
    c.setFont(FONT_MED, 9)
    c.setFillColor(WHITE)
    lines = [
        f"HEX     #1F5CF5",
        f"RGB     {rgb[0]}  ·  {rgb[1]}  ·  {rgb[2]}",
        f"CMYK   {cmyk[0]}  ·  {cmyk[1]}  ·  {cmyk[2]}  ·  {cmyk[3]}",
        f"PANTONE  2728 C (closest)",
    ]
    for i, line in enumerate(lines):
        c.drawString(hero_x + 8 * mm, hero_y + 8 * mm + (3 - i) * 5.5 * mm, line)

    # ---- Right column: neutrals + role ----
    rx = MARGIN + hero_w + 8 * mm
    rw = PAGE_W - MARGIN - rx
    # Blue 900 card
    ink_h = (hero_h - 6 * mm) / 2
    c.setFillColor(BLUE_900)
    c.rect(rx, hero_y + hero_h - ink_h, rw, ink_h, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(FONT_MED, 9)
    c.drawString(rx + 6 * mm, hero_y + hero_h - 10 * mm, "BLUE 900")
    c.setFont(FONT_MED, 20)
    c.drawString(rx + 6 * mm, hero_y + hero_h - 22 * mm, "#061A4A")
    c.setFont(FONT_BOOK, 9)
    c.setFillColorRGB(1, 1, 1, alpha=0.78)
    c.drawString(rx + 6 * mm, hero_y + hero_h - 30 * mm,
                 "Body text on light surfaces.")

    # Paper card
    c.setFillColor(PAPER)
    c.rect(rx, hero_y, rw, ink_h, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#dbe5fc"))
    c.setLineWidth(0.6)
    c.rect(rx, hero_y, rw, ink_h, stroke=1, fill=0)
    c.setFillColor(BLUE_700)
    c.setFont(FONT_MED, 9)
    c.drawString(rx + 6 * mm, hero_y + ink_h - 10 * mm, "PAPER")
    c.setFillColor(BLUE_900)
    c.setFont(FONT_MED, 20)
    c.drawString(rx + 6 * mm, hero_y + ink_h - 22 * mm, "#F8FAFF")
    c.setFillColor(TEXT_SOFT)
    c.setFont(FONT_BOOK, 9)
    c.drawString(rx + 6 * mm, hero_y + ink_h - 30 * mm,
                 "Section background, off-white.")

    # ---- Full scale row (Blue 50 → 900) ----
    scale_y = hero_y - 20 * mm
    c.setFillColor(BLUE_700)
    c.setFont(FONT_MED, 9)
    c.drawString(MARGIN, scale_y + 6 * mm, "FULL SCALE")
    c.setFillColor(BLUE_900)
    c.setFont(FONT_BOOK, 9)
    c.drawRightString(PAGE_W - MARGIN, scale_y + 6 * mm,
                      "Tints expand for backgrounds, hover states, and depth.")

    swatch_w = (PAGE_W - 2 * MARGIN - 9 * 2) / 10
    swatch_h = 28 * mm
    sy = scale_y - swatch_h - 4 * mm
    for i, (name, hexcode) in enumerate(PALETTE):
        sx = MARGIN + i * (swatch_w + 2)
        col = HexColor(hexcode)
        c.setFillColor(col)
        c.rect(sx, sy, swatch_w, swatch_h, stroke=0, fill=1)
        # Label inside (white text on dark, Blue 900 on light)
        r, g, b = hex_to_rgb(hexcode)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        text_color = BLUE_900 if luminance > 0.55 else WHITE
        c.setFillColor(text_color)
        c.setFont(FONT_MED, 7)
        short_name = name.replace("Blue ", "")
        c.drawString(sx + 3 * mm, sy + swatch_h - 6 * mm, short_name)
        c.setFont(FONT_BOOK, 6.5)
        c.drawString(sx + 3 * mm, sy + 3 * mm, hexcode.upper())

    # ---- Usage note ----
    note_y = sy - 18 * mm
    c.setStrokeColor(HexColor("#dbe5fc"))
    c.setLineWidth(0.6)
    c.line(MARGIN, note_y + 8 * mm, PAGE_W - MARGIN, note_y + 8 * mm)
    c.setFillColor(BLUE_700)
    c.setFont(FONT_MED, 9)
    c.drawString(MARGIN, note_y + 1 * mm, "USAGE")
    c.setFillColor(BLUE_900)
    c.setFont(FONT_BOOK, 9.5)
    c.drawString(MARGIN + 22 * mm, note_y + 1 * mm,
                 "60% Paper · 25% Blue 900 · 15% Blue 500. Reserve Blue 800/900 for hero surfaces.")

    page_meta(c, "Colour", 3)
    c.showPage()


# ---------------------------------------------------------------------------
# Page 4 — Typography
# ---------------------------------------------------------------------------

def draw_type_page(c: canvas_mod.Canvas) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    y = draw_section_head(c, "03", "Typography", "Sequel Sans",
                          "Editorial, geometric, quietly confident.")

    # ---- Aa specimen ----
    spec_h = 60 * mm
    spec_y = y - spec_h - 4 * mm
    c.setFillColor(BLUE_800)
    c.rect(MARGIN, spec_y, PAGE_W - 2 * MARGIN, spec_h, stroke=0, fill=1)

    c.setFillColor(WHITE)
    c.setFont(FONT_MED, 180)
    c.drawString(MARGIN + 10 * mm, spec_y + 10 * mm, "Aa")

    c.setFillColorRGB(1, 1, 1, alpha=0.72)
    c.setFont(FONT_MED, 9)
    c.drawString(MARGIN + 90 * mm, spec_y + spec_h - 10 * mm, "PRIMARY TYPEFACE")
    c.setFillColor(WHITE)
    c.setFont(FONT_MED, 28)
    c.drawString(MARGIN + 90 * mm, spec_y + spec_h - 22 * mm, "Sequel Sans")
    c.setFillColorRGB(1, 1, 1, alpha=0.82)
    c.setFont(FONT_BOOK, 10)
    c.drawString(MARGIN + 90 * mm, spec_y + spec_h - 30 * mm,
                 "Used for every surface of the brand — headlines,")
    c.drawString(MARGIN + 90 * mm, spec_y + spec_h - 35 * mm,
                 "body, UI and signage.")

    c.setFillColorRGB(1, 1, 1, alpha=0.55)
    c.setFont(FONT_BOOK, 8.5)
    c.drawString(MARGIN + 90 * mm, spec_y + 10 * mm,
                 "Fallback: Inter, Montserrat, system-ui, sans-serif.")

    # ---- Weights row ----
    weights_y = spec_y - 22 * mm
    c.setFillColor(BLUE_700)
    c.setFont(FONT_MED, 9)
    c.drawString(MARGIN, weights_y + 8 * mm, "WEIGHTS")

    col_w = (PAGE_W - 2 * MARGIN) / 4
    weight_specs = [
        ("Book",    FONT_BOOK, 400, "Long-form copy"),
        ("Display", FONT_BOOK, 425, "Editorial reads"),
        ("Medium",  FONT_MED,  500, "Headlines · CTAs"),
        ("Semi",    FONT_SEMI, 600, "Eyebrows · tags"),
    ]
    for i, (label, font, w_num, role) in enumerate(weight_specs):
        cx = MARGIN + i * col_w
        c.setFillColor(BLUE_900)
        c.setFont(font, 36)
        c.drawString(cx, weights_y - 12 * mm, "Aa")
        c.setFillColor(BLUE_700)
        c.setFont(FONT_MED, 8)
        c.drawString(cx, weights_y - 18 * mm, f"{w_num}  ·  {label.upper()}")
        c.setFillColor(TEXT_SOFT)
        c.setFont(FONT_BOOK, 8.5)
        c.drawString(cx, weights_y - 24 * mm, role)

    # ---- Type scale ----
    scale_y = weights_y - 38 * mm
    c.setStrokeColor(HexColor("#dbe5fc"))
    c.setLineWidth(0.6)
    c.line(MARGIN, scale_y + 8 * mm, PAGE_W - MARGIN, scale_y + 8 * mm)

    c.setFillColor(BLUE_700)
    c.setFont(FONT_MED, 9)
    c.drawString(MARGIN, scale_y + 1 * mm, "SCALE")
    c.setFillColor(TEXT_SOFT)
    c.setFont(FONT_BOOK, 8.5)
    c.drawRightString(PAGE_W - MARGIN, scale_y + 1 * mm,
                       "Tracking +1% on display sizes, +0% on body.")

    rows = [
        ("Display",  FONT_MED, 40, "Aa", "Hero headlines"),
        ("H1",       FONT_MED, 28, "Aa", "Page titles"),
        ("H2",       FONT_MED, 20, "Aa", "Section heads"),
        ("Body",     FONT_BOOK, 13, "Aa", "Long-form, UI copy"),
        ("Caption",  FONT_MED, 9,  "Aa", "Labels, eyebrows"),
    ]
    ry = scale_y - 12 * mm
    for label, font, size, glyph, role in rows:
        baseline = ry
        c.setFillColor(BLUE_900)
        c.setFont(font, size)
        c.drawString(MARGIN, baseline, glyph)
        c.setFillColor(BLUE_700)
        c.setFont(FONT_MED, 8)
        c.drawString(MARGIN + 38 * mm, baseline + size * 0.30, label.upper())
        c.setFillColor(BLUE_900)
        c.setFont(FONT_MED, 9)
        c.drawString(MARGIN + 58 * mm, baseline + size * 0.30,
                     f"{size} / {round(size * 1.18)}  ·  +1%")
        c.setFillColor(TEXT_SOFT)
        c.setFont(FONT_BOOK, 9)
        c.drawRightString(PAGE_W - MARGIN, baseline + size * 0.30, role)
        ry -= max(size * 1.25, 11 * mm)

    page_meta(c, "Typography", 4)
    c.showPage()


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build(path: Path) -> None:
    c = canvas_mod.Canvas(str(path), pagesize=letter)
    c.setTitle("Automation One — Brand Guidelines")
    c.setAuthor("Automation One Business Systems")
    c.setSubject("Brand Identity")
    c.setKeywords("Automation One, brand, logo, colour, typography")

    register_fonts()

    draw_cover(c)
    draw_logo_page(c)
    draw_colour_page(c)
    draw_type_page(c)

    c.save()


def main() -> None:
    build(OUTPUT_SITE)
    try:
        shutil.copy2(OUTPUT_SITE, OUTPUT_DOWNLOADS)
    except Exception as exc:
        print(f"Warning: could not copy to Downloads: {exc}")
    print(f"Wrote: {OUTPUT_SITE}")
    print(f"Wrote: {OUTPUT_DOWNLOADS}")
    print(f"Size:  {OUTPUT_SITE.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
