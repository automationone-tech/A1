#!/usr/bin/env python3
"""Automation One — Brand Guidelines (6 pages).

A tight, premium 6-page identity guide:
  1. Cover
  2. Logo — stacked lockup & wordmark (primary & secondary)
  3. Logo — reverse wordmarks & marks
  4. Colour
  5. Logo — slogans
  6. Typography
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
LOGO_BLUE_800 = BASE / "ao-nav-logo-0a2870.png"   # Blue 800 mark
LOGO_BLUE_900 = BASE / "ao-nav-logo-061a4a.png"   # Blue 900 mark
LOGO_REVERSE = BASE / "ao-nav-logo-ffffff.png"    # white mark
LOGO_BLACK = BASE / "ao-nav-logo-000000.png"      # mono black mark
LOCKUP_STACKED_PRIMARY = BASE / "ao-logo-lockup-stacked-primary.png"
LOCKUP_STACKED_WHITE = BASE / "ao-logo-lockup-stacked-white.png"
LOCKUP_HORIZONTAL_PRIMARY = BASE / "ao-logo-lockup-horizontal-primary.png"
LOCKUP_HORIZONTAL_BLUE500 = BASE / ".pdf-cache" / "horizontal-lockup-blue500.png"
LOCKUP_HORIZONTAL_BLUE800 = BASE / ".pdf-cache" / "horizontal-lockup-blue800.png"
LOCKUP_HORIZONTAL_WHITE = BASE / ".pdf-cache" / "horizontal-lockup-white.png"
LOCKUP_STACKED_BASE = BASE / ".pdf-cache" / "stacked-lockup-base.png"
LOCKUP_STACKED_BLUE500 = BASE / ".pdf-cache" / "stacked-lockup-blue500.png"
LOCKUP_STACKED_BLUE800 = BASE / ".pdf-cache" / "stacked-lockup-blue800.png"
FONT_DISPLAY_SEMI = FONTS_DIR / "SequelSans-DisplaySemi.BFge39nV.ttf"
FONT_DISPLAY_MED = FONTS_DIR / "SequelSans-DisplayMedium.BYsR-9NK.ttf"
STACKED_SUB_Y0 = 1720
STACKED_SUB_Y1 = 1875
STACKED_SUB_RIGHT = 1935
STACKED_SUB_SIZE = 145
STACKED_NAME_INK = (49, 80, 171)
STACKED_BG = (248, 250, 255)
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


_ICC_SRGB = Path("/System/Library/ColorSync/Profiles/sRGB Profile.icc")
_ICC_CMYK = Path("/System/Library/ColorSync/Profiles/Generic CMYK Profile.icc")
_CMYK_CACHE: dict[str, tuple[int, int, int, int]] = {}


def hex_to_cmyk(h: str) -> tuple[int, int, int, int]:
    """sRGB → CMYK via ColorSync when available (closer print match than naive math)."""
    key = h.lower()
    if key in _CMYK_CACHE:
        return _CMYK_CACHE[key]

    r, g, b = hex_to_rgb(h)
    cmyk_vals: tuple[int, int, int, int] | None = None
    if Image is not None and _ICC_SRGB.exists() and _ICC_CMYK.exists():
        try:
            from PIL import ImageCms

            srgb = ImageCms.getOpenProfile(str(_ICC_SRGB))
            cmyk_prof = ImageCms.getOpenProfile(str(_ICC_CMYK))
            im = Image.new("RGB", (1, 1), (r, g, b))
            out = ImageCms.profileToProfile(
                im,
                srgb,
                cmyk_prof,
                outputMode="CMYK",
                renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
                inPlace=False,
            )
            C, M, Y, K = out.getpixel((0, 0))
            cmyk_vals = tuple(int(round(v / 255 * 100)) for v in (C, M, Y, K))
        except Exception:
            cmyk_vals = None

    if cmyk_vals is None:
        # Fallback: rich (K=0-biased) conversion — preserves chroma vs undercolour-removed blues
        rf, gf, bf = r / 255, g / 255, b / 255
        c = 1 - rf
        m = 1 - gf
        y = 1 - bf
        k = min(c, m, y)
        # Pull only a light black plate so blues stay cleaner
        k *= 0.35
        if k >= 1:
            cmyk_vals = (0, 0, 0, 100)
        else:
            c = (c - k) / (1 - k)
            m = (m - k) / (1 - k)
            y = (y - k) / (1 - k)
            cmyk_vals = tuple(round(v * 100) for v in (c, m, y, k))

    _CMYK_CACHE[key] = cmyk_vals
    return cmyk_vals


def cmyk_label(h: str, *, compact: bool = False) -> str:
    """Format ICC CMYK for captions (e.g. 79 · 52 · 0 · 0)."""
    c, m, y, k = hex_to_cmyk(h)
    if compact:
        return f"{c}·{m}·{y}·{k}"
    return f"{c}  ·  {m}  ·  {y}  ·  {k}"


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


def _recolor_mark(src: Path, dest: Path, hex_color: str) -> Path:
    """Recolour a mark PNG to a single palette colour."""
    if dest.exists() or Image is None or not src.exists():
        return dest
    im = Image.open(src).convert("RGBA")
    px = im.load()
    tr, tg, tb = hex_to_rgb(hex_color)
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, g, b, a = px[x, y]
            if a < 16:
                continue
            px[x, y] = (tr, tg, tb, a)
    im.save(dest)
    return dest


def ensure_blue800_logo() -> Path:
    """Build Blue 800 mark asset from the primary mark."""
    return _recolor_mark(LOGO_PRIMARY, LOGO_BLUE_800, "#0a2870")


def ensure_blue900_logo() -> Path:
    """Build Blue 900 mark asset from the primary mark."""
    return _recolor_mark(LOGO_PRIMARY, LOGO_BLUE_900, "#061a4a")


def _recolor_lockup_rgba(im: "Image.Image", hex_color: str) -> "Image.Image":
    """Soft recolour for lockup PNGs — preserves anti-aliased stroke weight."""
    tr, tg, tb = hex_to_rgb(hex_color)
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
    return out


def _repair_stacked_subline(im: "Image.Image") -> "Image.Image":
    """Re-render Business Systems at Medium weight (lighter than baked Semi)."""
    from PIL import ImageDraw, ImageFont

    px = im.load()
    w, h = im.size
    for y in range(STACKED_SUB_Y0, STACKED_SUB_Y1 + 1):
        for x in range(w):
            px[x, y] = (*STACKED_BG, 255)

    if not FONT_DISPLAY_MED.exists():
        return im

    font = ImageFont.truetype(str(FONT_DISPLAY_MED), STACKED_SUB_SIZE)
    text = "Business Systems"
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = STACKED_SUB_RIGHT - tw - bbox[0]
    ty = 1731 + (1860 - 1731 + 1 - th) // 2 - bbox[1]

    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((tx, ty), text, fill=(*STACKED_NAME_INK, 255), font=font)
    return Image.alpha_composite(im.convert("RGBA"), layer)


def build_stacked_lockup_base() -> Path | None:
    """Stacked reference with corrected subline weight."""
    src = LOCKUP_STACKED_PRIMARY
    if not src.exists() or Image is None:
        return None
    if LOCKUP_STACKED_BASE.exists() and LOCKUP_STACKED_BASE.stat().st_mtime >= src.stat().st_mtime:
        return LOCKUP_STACKED_BASE

    im = _repair_stacked_subline(Image.open(src).convert("RGBA"))
    LOCKUP_STACKED_BASE.parent.mkdir(exist_ok=True)
    im.save(LOCKUP_STACKED_BASE)
    return LOCKUP_STACKED_BASE


def build_stacked_lockup(hex_color: str, dest: Path) -> Path | None:
    """Stacked lockup → target colour."""
    base = build_stacked_lockup_base()
    if not base or Image is None:
        return None

    out = _recolor_lockup_rgba(Image.open(base).convert("RGBA"), hex_color)
    out = out.resize((out.width * 2, out.height * 2), Image.LANCZOS)
    dest.parent.mkdir(exist_ok=True)
    out.save(dest)
    return dest


def build_stacked_lockup_blue500() -> Path | None:
    return build_stacked_lockup("#1f5cf5", LOCKUP_STACKED_BLUE500)


def build_stacked_lockup_blue800() -> Path | None:
    return build_stacked_lockup("#0a2870", LOCKUP_STACKED_BLUE800)


def build_horizontal_lockup(hex_color: str, dest: Path) -> Path | None:
    """Reference horizontal lockup → target colour, preserving stroke weight."""
    src = LOCKUP_HORIZONTAL_PRIMARY
    if not src.exists() or Image is None:
        return None

    out = _recolor_lockup_rgba(Image.open(src).convert("RGBA"), hex_color)
    out = out.resize((out.width * 2, out.height * 2), Image.LANCZOS)
    dest.parent.mkdir(exist_ok=True)
    out.save(dest)
    return dest


def build_horizontal_lockup_blue500() -> Path | None:
    return build_horizontal_lockup("#1f5cf5", LOCKUP_HORIZONTAL_BLUE500)


def build_horizontal_lockup_blue800() -> Path | None:
    return build_horizontal_lockup("#0a2870", LOCKUP_HORIZONTAL_BLUE800)


def build_horizontal_lockup_white() -> Path | None:
    return build_horizontal_lockup("#ffffff", LOCKUP_HORIZONTAL_WHITE)


def horizontal_lockup_size(h: float) -> tuple[float, float]:
    """Width and height from reference horizontal lockup aspect ratio."""
    return h / LOCKUP_H_ASPECT, h


def stacked_lockup_size(h: float) -> tuple[float, float]:
    """Width and height from reference stacked lockup aspect ratio."""
    return h / LOCKUP_ASPECT, h


def _fit_stacked_height(max_width: float, max_height: float) -> float:
    """Stacked lockup height that fits inside a box."""
    by_width = max_width * LOCKUP_ASPECT
    return min(max_height, by_width)


def _content_width() -> float:
    return PAGE_W - 2 * MARGIN


def _content_bottom() -> float:
    """Lowest y for body content (above footer band)."""
    return MARGIN + 24 * mm


def _fit_lockup_height(max_width: float, max_height: float) -> float:
    """Lockup height that fits inside a box while preserving aspect ratio."""
    by_width = max_width * LOCKUP_H_ASPECT
    return min(max_height, by_width)


def _centered_x(content_w: float) -> float:
    return MARGIN + (_content_width() - content_w) / 2


def _draw_horizontal_lockup(c: canvas_mod.Canvas, path: Path | None,
                            x: float, y: float, h: float, *, white: bool = False) -> float:
    """Draw a horizontal lockup; returns rendered width."""
    w, _ = horizontal_lockup_size(h)
    if path and path.exists():
        if white:
            c.setFillColor(WHITE)
        c.drawImage(str(path), x, y, w, h, mask="auto")
    return w


def _draw_stacked_lockup(c: canvas_mod.Canvas, path: Path | None,
                         x: float, y: float, h: float) -> float:
    """Draw a stacked lockup; returns rendered width."""
    w, _ = stacked_lockup_size(h)
    if path and path.exists():
        c.drawImage(str(path), x, y, w, h, mask="auto")
    return w


def _draw_clear_space_cage(c: canvas_mod.Canvas, cage_x: float, cage_y: float,
                           cage_w: float, cage_h: float, *, show_labels: bool = True,
                           label_center_y: float | None = None) -> None:
    c.setStrokeColor(BLUE_300)
    c.setDash(2, 2)
    c.setLineWidth(0.8)
    c.rect(cage_x, cage_y, cage_w, cage_h, stroke=1, fill=0)
    c.setDash()

    for cx_, cy_ in [(cage_x, cage_y), (cage_x + cage_w, cage_y),
                     (cage_x, cage_y + cage_h), (cage_x + cage_w, cage_y + cage_h)]:
        c.setFillColor(BLUE_500)
        c.circle(cx_, cy_, 1.4, stroke=0, fill=1)

    if show_labels:
        if label_center_y is not None:
            label_y = label_center_y + 2 * mm
        else:
            label_y = cage_y + cage_h + 1.5 * mm
        c.setFillColor(BLUE_700)
        c.setFont(FONT_MED, 8)
        c.drawCentredString(cage_x + cage_w / 2, label_y, "CLEAR SPACE")
        c.setFillColor(TEXT_SOFT)
        c.setFont(FONT_BOOK, 8)
        c.drawCentredString(cage_x + cage_w / 2, label_y - 4 * mm,
                            "X  =  1/2 mark height")


def _wrap_text_lines(text: str, font: str, size: float, max_width: float) -> list[str]:
    """Wrap text to fit a maximum line width."""
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word])
        if pdfmetrics.stringWidth(trial, font, size) <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _font_descender(font: str, font_size: float) -> float:
    """Distance below baseline to bottom of glyphs (positive, in points)."""
    face = pdfmetrics.getFont(font).face
    return abs(face.descent) / 1000.0 * font_size


def _info_line_height(font_size: float) -> float:
    return font_size * 0.36 * mm + 0.75 * mm


def _info_box_height(
    num_lines: int,
    font_size: float,
    *,
    font: str = FONT_BOOK,
    pad_top: float = 3.5 * mm,
    pad_bottom: float = 0.8 * mm,
) -> float:
    """Tight vertical height for a wrapped info box (matches _draw_info_box line metrics)."""
    line_h = _info_line_height(font_size)
    if num_lines <= 0:
        return pad_top + pad_bottom
    return pad_top + (num_lines - 1) * line_h + _font_descender(font, font_size) + pad_bottom


def _draw_info_box(
    c: canvas_mod.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    lines: list[str] | None = None,
    *,
    text: str | None = None,
    font_size: float = 9.5,
    full_width: bool = False,
    pad_x: float = 5 * mm,
    pad_top: float = 3.5 * mm,
    pad_bottom: float = 0.8 * mm,
) -> None:
    """Light bordered callout for usage or legal notes."""
    text_w = w - 2 * pad_x
    font = FONT_BOOK

    if text is not None:
        content_lines = _wrap_text_lines(text, font, font_size, text_w)
    elif full_width and lines:
        content_lines = []
        for line in lines:
            content_lines.extend(_wrap_text_lines(line, font, font_size, text_w))
    else:
        content_lines = lines or []

    c.setFillColor(WHITE)
    c.rect(x, y, w, h, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#dbe5fc"))
    c.setLineWidth(0.6)
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.setFillColor(BLUE_900)
    c.setFont(font, font_size)
    line_h = _info_line_height(font_size)
    ty = y + h - pad_top
    for line in content_lines:
        c.drawString(x + pad_x, ty, line)
        ty -= line_h


def _draw_section_kicker(c: canvas_mod.Canvas, y: float, label: str) -> None:
    """Small-caps section label in Blue 800."""
    c.setFillColor(BLUE_800)
    c.setFont(FONT_MED, 8)
    c.drawString(MARGIN, y, label)


def _draw_lockup_label(c: canvas_mod.Canvas, x: float, y: float, role: str,
                       colour_name: str, hex_code: str, *, align: str = "left") -> None:
    c.setFillColor(BLUE_700)
    c.setFont(FONT_MED, 8)
    line1 = role.upper()
    line2 = f"{colour_name}  ·  {cmyk_label(hex_code)}"
    if align == "right":
        c.drawRightString(x, y, line1)
        c.setFillColor(TEXT_SOFT)
        c.setFont(FONT_BOOK, 8)
        c.drawRightString(x, y - 4.5 * mm, line2)
    elif align == "center":
        c.drawCentredString(x, y, line1)
        c.setFillColor(TEXT_SOFT)
        c.setFont(FONT_BOOK, 8)
        c.drawCentredString(x, y - 4.5 * mm, line2)
    else:
        c.drawString(x, y, line1)
        c.setFillColor(TEXT_SOFT)
        c.setFont(FONT_BOOK, 8)
        c.drawString(x, y - 4.5 * mm, line2)


def _draw_dual_colour_cage(
    c: canvas_mod.Canvas,
    *,
    y_top: float,
    block_h: float,
    lockup_gap: float,
    pad_ratio: float,
    fit_height,
    lockup_size,
    draw_lockup,
    primary_path: Path | None,
    secondary_path: Path | None,
    layout: str = "vertical",
    label_col_w: float = 0,
    label_x: float | None = None,
    show_clear: bool = True,
    min_bottom: float | None = None,
    block_overhead: float | None = None,
    clear_band: float | None = None,
    kicker_offset: float | None = None,
) -> float:
    """Primary + secondary pair in a clear-space cage; returns y below section."""
    label_h = 7 * mm if layout == "horizontal" else 0
    if clear_band is None:
        clear_band = 8 * mm if show_clear else 0
    overhead = block_overhead if block_overhead is not None else 10 * mm
    k_offset = kicker_offset if kicker_offset is not None else 3 * mm
    max_cage_w = _content_width() - label_col_w

    if layout == "horizontal":
        max_lockup_w = (max_cage_w - lockup_gap - 8 * mm) / 2
        max_lockup_h = block_h - overhead - label_h - clear_band
        if min_bottom is not None:
            floor_overhead = k_offset + label_h + clear_band + 6 * mm
            by_floor = (y_top - floor_overhead - min_bottom) / (1 + 2 * pad_ratio)
            max_lockup_h = min(max_lockup_h, by_floor)
        lockup_h = fit_height(max_lockup_w, max(10 * mm, max_lockup_h))
        lockup_w, _ = lockup_size(lockup_h)
        pad = lockup_h * pad_ratio
        inner_w = lockup_w * 2 + lockup_gap
        cage_w = inner_w + pad * 2
        cage_h = lockup_h + pad * 2
        cage_x = _centered_x(cage_w)
        cage_y = y_top - k_offset - cage_h - clear_band
        lockup_y = cage_y + pad
        primary_x = cage_x + pad
        secondary_x = cage_x + pad + lockup_w + lockup_gap

        _draw_clear_space_cage(
            c, cage_x, cage_y, cage_w, cage_h, show_labels=show_clear,
            label_center_y=y_top - clear_band / 2 if show_clear else None,
        )
        draw_lockup(c, primary_path, primary_x, lockup_y, lockup_h)
        draw_lockup(c, secondary_path, secondary_x, lockup_y, lockup_h)

        label_y = cage_y - 3 * mm
        _draw_lockup_label(c, primary_x + lockup_w / 2, label_y,
                           "Primary", "Blue 800", "#0a2870", align="center")
        _draw_lockup_label(c, secondary_x + lockup_w / 2, label_y,
                           "Secondary", "Blue 500", "#1f5cf5", align="center")
        return cage_y - label_h
    else:
        max_lockup_h = (block_h - 14 * mm) / 2.8
        lockup_h = fit_height(max_cage_w - 20 * mm, max(10 * mm, max_lockup_h))
        lockup_w, _ = lockup_size(lockup_h)
        pad = lockup_h * pad_ratio
        inner_h = lockup_h * 2 + lockup_gap
        cage_w = lockup_w + pad * 2
        cage_h = inner_h + pad * 2
        cage_x = MARGIN
        cage_y = y_top - 6 * mm - cage_h
        hero_x = cage_x + pad
        primary_y = cage_y + pad + lockup_h + lockup_gap
        secondary_y = cage_y + pad

        _draw_clear_space_cage(c, cage_x, cage_y, cage_w, cage_h, show_labels=show_clear)
        draw_lockup(c, primary_path, hero_x, primary_y, lockup_h)
        draw_lockup(c, secondary_path, hero_x, secondary_y, lockup_h)

        if label_x is not None:
            _draw_lockup_label(c, label_x, primary_y + lockup_h * 0.35,
                               "Primary", "Blue 800", "#0a2870", align="right")
            _draw_lockup_label(c, label_x, secondary_y + lockup_h * 0.35,
                               "Secondary", "Blue 500", "#1f5cf5", align="right")
        return cage_y


# ---------------------------------------------------------------------------
# Page 2 — Logo (stacked lockup & wordmark)
# ---------------------------------------------------------------------------

def draw_logo_page(c: canvas_mod.Canvas) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    y = draw_section_head(
        c, 2, "Stacked lockup & wordmark",
        "Blue 800 is primary. Blue 500 is secondary — same mark, two colourways.",
    )

    gap = 4 * mm
    kicker_h = 2 * mm
    note_font = 9.5
    note_y0 = MARGIN + 14 * mm
    lockup_gap = 8 * mm
    content_w = _content_width()
    mark_font = 8.5
    mark_pad_x = 5 * mm
    mark_text = (
        "Our mark is a stylised AO that forms an infinity symbol — a new expression of Automation One "
        "that stays true to our roots. The continuous loop represents lasting client relationships and "
        "the limitless ways we help improve business workflows. Its seamless, interlocking form reflects "
        "the synergistic efficiency our solutions and services deliver."
    )
    usage_text = (
        "Use the stacked lockup for hero placements and the wordmark for navigation, headers, "
        "and tight horizontal spaces — both share the same clear space."
    )
    mark_lines = _wrap_text_lines(
        mark_text, FONT_BOOK, mark_font, content_w - 2 * mark_pad_x,
    )
    usage_lines = _wrap_text_lines(
        usage_text, FONT_BOOK, note_font, content_w - 10 * mm,
    )
    mark_box_h = _info_box_height(len(mark_lines), mark_font)
    note_h = _info_box_height(len(usage_lines), note_font)
    body_floor = note_y0 + note_h + 2 * mm

    body_top = y - 3 * mm
    mark_section = kicker_h + mark_box_h + gap
    lockup_area = body_top - body_floor - mark_section - kicker_h - gap - 2 * mm
    stacked_block_h = lockup_area * 0.58
    wordmark_block_h = lockup_area * 0.42

    stacked_primary = build_stacked_lockup_blue800()
    stacked_secondary = build_stacked_lockup_blue500()
    wordmark_primary = build_horizontal_lockup_blue800()
    wordmark_secondary = build_horizontal_lockup_blue500()

    y_cursor = body_top
    _draw_section_kicker(c, y_cursor, "THE MARK")
    y_cursor -= kicker_h
    _draw_info_box(
        c, MARGIN, y_cursor - mark_box_h, content_w, mark_box_h,
        text=mark_text, font_size=mark_font,
    )
    y_cursor -= mark_box_h + gap

    _draw_section_kicker(c, y_cursor, "STACKED LOCKUP")
    y_cursor -= kicker_h
    y_top = y_cursor
    stacked_bottom = _draw_dual_colour_cage(
        c,
        y_top=y_top,
        block_h=stacked_block_h,
        lockup_gap=lockup_gap,
        pad_ratio=0.12,
        fit_height=_fit_stacked_height,
        lockup_size=stacked_lockup_size,
        draw_lockup=_draw_stacked_lockup,
        primary_path=stacked_primary,
        secondary_path=stacked_secondary,
        layout="horizontal",
        block_overhead=1 * mm,
        clear_band=5 * mm,
        kicker_offset=0,
    )
    y_cursor = stacked_bottom - gap - 2 * mm

    _draw_section_kicker(c, y_cursor, "WORDMARK")
    y_cursor -= kicker_h + 3 * mm
    y_top = y_cursor
    _draw_dual_colour_cage(
        c,
        y_top=y_top,
        block_h=wordmark_block_h,
        lockup_gap=lockup_gap,
        pad_ratio=0.24,
        fit_height=_fit_lockup_height,
        lockup_size=horizontal_lockup_size,
        draw_lockup=_draw_horizontal_lockup,
        primary_path=wordmark_primary,
        secondary_path=wordmark_secondary,
        layout="horizontal",
        show_clear=False,
        min_bottom=body_floor,
        block_overhead=1 * mm,
        kicker_offset=0,
    )

    _draw_info_box(
        c, MARGIN, note_y0, content_w, note_h,
        text=usage_text,
        font_size=note_font,
    )

    page_meta(c, 2)
    c.showPage()


# ---------------------------------------------------------------------------
# Page 3 — Logo reverse & mark variants
# ---------------------------------------------------------------------------

def draw_logo_reverse_page(c: canvas_mod.Canvas) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    y = draw_section_head(
        c, 3, "Reverse wordmarks",
        "White wordmarks on Blue 800 and Blue 500 backgrounds.",
    )

    white_path = build_horizontal_lockup_white()
    panel_pad = 6 * mm
    panel_label_h = 8 * mm
    panel_gap = 8 * mm
    content_w = _content_width()
    marks_note_font = 9
    marks_note_text = (
        "Stacked lockups, wordmarks, and marks must appear only in the colour combinations "
        "shown above, or in another combination drawn from the palette on the following page "
        "with the written approval of Automation One Business Systems Inc."
    )
    marks_note_lines = _wrap_text_lines(
        marks_note_text, FONT_BOOK, marks_note_font, content_w - 10 * mm,
    )
    marks_note_h = _info_box_height(len(marks_note_lines), marks_note_font)
    base_y = MARGIN + 22 * mm
    cell_h = 30 * mm
    grid_gap = 12 * mm
    marks_kicker_h = 6 * mm
    panel_top = y - 12 * mm
    panel_w = (_content_width() - panel_gap) / 2
    avail = (panel_top - base_y - 28 * mm - marks_kicker_h - cell_h - grid_gap
             - marks_note_h - 8 * mm)
    max_lockup_w = panel_w - panel_pad * 2
    max_lockup_h = avail - panel_pad * 2 - panel_label_h
    lockup_h = _fit_lockup_height(max_lockup_w, max(14 * mm, max_lockup_h))
    lockup_w, _ = horizontal_lockup_size(lockup_h)
    panel_h = lockup_h + panel_pad * 2 + panel_label_h
    panel_y = panel_top - panel_h

    reverse_cells = [
        ("Primary reverse", "Blue 800", "#0a2870", BLUE_800),
        ("Secondary reverse", "Blue 500", "#1f5cf5", BLUE_500),
    ]
    for i, (role, colour_name, hex_code, bg) in enumerate(reverse_cells):
        px = MARGIN + i * (panel_w + panel_gap)
        c.setFillColor(bg)
        c.rect(px, panel_y, panel_w, panel_h, stroke=0, fill=1)
        lx = px + (panel_w - lockup_w) / 2
        ly = panel_y + panel_pad + 2 * mm
        _draw_horizontal_lockup(c, white_path, lx, ly, lockup_h, white=True)
        c.setFillColor(WHITE)
        c.setFont(FONT_MED, 8)
        c.drawCentredString(px + panel_w / 2, panel_y + 3 * mm, role.upper())
        c.setFont(FONT_BOOK, 7.5)
        c.setFillColorRGB(1, 1, 1, alpha=0.82)
        c.drawCentredString(px + panel_w / 2, panel_y + panel_h - 4 * mm,
                            f"{colour_name}  ·  {cmyk_label(hex_code)}")

    ensure_blue800_logo()
    ensure_blue900_logo()
    marks_top = panel_y - grid_gap
    _draw_section_kicker(c, marks_top, "MARKS")

    grid_top = marks_top - marks_kicker_h
    gap = 4 * mm
    cell_w = (_content_width() - 4 * gap) / 5
    grid_bottom = grid_top - cell_h
    if grid_bottom < base_y + 28 * mm + marks_note_h + 8 * mm:
        grid_top = base_y + 28 * mm + marks_note_h + 8 * mm + cell_h
    cells = [
        ("Primary",           LOGO_BLUE_800, WHITE,    BLUE_800,  HexColor("#dbe5fc"), BLUE_800),
        ("Secondary",         LOGO_PRIMARY,  WHITE,    BLUE_500,  HexColor("#dbe5fc"), BLUE_500),
        ("Primary reverse",   LOGO_REVERSE,  BLUE_800, WHITE,     None,                WHITE),
        ("Secondary reverse", LOGO_REVERSE,  BLUE_500, WHITE,     None,                WHITE),
        ("Mono",              LOGO_BLACK,    WHITE,    BLUE_900,  HexColor("#dbe5fc"), BLUE_900),
    ]
    for i, (name, logo, bg, _border_fill, border, label_color) in enumerate(cells):
        x = MARGIN + i * (cell_w + gap)
        yy = grid_top - cell_h
        c.setFillColor(bg)
        c.rect(x, yy, cell_w, cell_h, stroke=0, fill=1)
        if border:
            c.setStrokeColor(border)
            c.setLineWidth(0.6)
            c.rect(x, yy, cell_w, cell_h, stroke=1, fill=0)
        ratio = 288 / 416
        mh = min(14 * mm, cell_h * 0.55)
        mw = mh / ratio
        if logo.exists():
            c.setFillColor(WHITE)
            c.drawImage(ImageReader(str(logo)),
                        x + (cell_w - mw) / 2,
                        yy + (cell_h - mh) / 2 + 4 * mm,
                        mw, mh, mask="auto")
        c.setFillColor(label_color)
        c.setFont(FONT_MED, 7)
        if "reverse" in name.lower():
            parts = name.upper().split(" REVERSE")
            c.drawCentredString(x + cell_w / 2, yy + 7 * mm, parts[0])
            c.drawCentredString(x + cell_w / 2, yy + 3.5 * mm, "REVERSE")
        else:
            c.drawCentredString(x + cell_w / 2, yy + 5 * mm, name.upper())

    marks_note_y = grid_top - cell_h - 6 * mm - marks_note_h
    _draw_info_box(
        c, MARGIN, marks_note_y, content_w, marks_note_h,
        text=marks_note_text,
        font_size=marks_note_font,
    )

    base_y = MARGIN + 22 * mm
    half = (PAGE_W - 2 * MARGIN - 8 * mm) / 2

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
    c.drawString(MARGIN + 6 * mm, base_y + 14 * mm,
                 "Digital   ·   30 px wordmark height  /  50 px mark")
    c.drawString(MARGIN + 6 * mm, base_y + 7 * mm,
                 "Print       ·   10 pt wordmark             /  8 mm mark")

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

    page_meta(c, 3)
    c.showPage()


# ---------------------------------------------------------------------------
# Page 5 — Slogans
# ---------------------------------------------------------------------------

def draw_slogans_page(c: canvas_mod.Canvas) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    y = draw_section_head(
        c, 5, "Slogans",
        "Primary and secondary taglines for marketing, sales, and brand communications.",
    )

    card_gap = 10 * mm
    card_h = 52 * mm
    card_w = _content_width()
    slogan_size = 20
    primary_y = y - 18 * mm - card_h
    secondary_y = primary_y - card_gap - card_h

    slogans = (
        (primary_y, "Primary slogan", "Business solutions made simple."),
        (secondary_y, "Secondary slogan",
         "One independent partner. Infinite possibilities."),
    )
    for card_y, role, slogan in slogans:
        c.setFillColor(WHITE)
        c.rect(MARGIN, card_y, card_w, card_h, stroke=0, fill=1)
        c.setStrokeColor(HexColor("#dbe5fc"))
        c.setLineWidth(0.6)
        c.rect(MARGIN, card_y, card_w, card_h, stroke=1, fill=0)

        c.setFillColor(BLUE_700)
        c.setFont(FONT_MED, 8)
        c.drawString(MARGIN + 8 * mm, card_y + card_h - 10 * mm, role.upper())
        c.setFillColor(TEXT_SOFT)
        c.setFont(FONT_BOOK, 8)
        c.drawString(MARGIN + 8 * mm, card_y + card_h - 16 * mm,
                     f"Blue 800  ·  {cmyk_label('#0a2870')}")

        c.setFillColor(BLUE_800)
        c.setFont(FONT_MED, slogan_size)
        c.drawString(MARGIN + 8 * mm, card_y + card_h / 2 - 4 * mm, slogan)

    note_y = secondary_y - 14 * mm - 22 * mm
    _draw_info_box(
        c, MARGIN, note_y, card_w, 22 * mm,
        [
            "Use the primary slogan on hero placements, cover pages, and key brand moments.",
            "The secondary slogan supports campaigns, proposals, and partner communications.",
        ],
        font_size=10,
    )

    page_meta(c, 5)
    c.showPage()


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


def page_meta(c: canvas_mod.Canvas, page_num: int, *, dark: bool = False) -> None:
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
    c.drawRightString(PAGE_W - MARGIN, MARGIN, str(page_num))


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
                      "VOL. 1 - Jul 2026")

    # Stacked lockup — original proportions, rendered white
    c.setFillColor(WHITE)  # reset fill alpha (glow/eyebrow leave ca < 1 → grey logo)
    lockup_w = 112 * mm
    lockup_h = lockup_w * LOCKUP_ASPECT
    lx = (PAGE_W - lockup_w) / 2
    ly = PAGE_H * 0.56 - lockup_h / 2
    lockup_src = build_stacked_lockup_base() or (
        LOCKUP_STACKED_PRIMARY if LOCKUP_STACKED_PRIMARY.exists() else LOCKUP_STACKED_WHITE
    )
    lockup_path = build_cover_lockup_white(lockup_src)
    if lockup_path:
        c.drawImage(str(lockup_path), lx, ly, lockup_w, lockup_h,
                    mask=BLACK_COLORKEY, preserveAspectRatio=True)

    # Tagline + title block (tagline above)
    tagline_x = MARGIN + 12 * mm
    c.setFillColor(WHITE)
    c.setFont(FONT_MED, 28)
    c.drawString(tagline_x, PAGE_H * 0.275, "Business solutions")
    c.drawString(tagline_x, PAGE_H * 0.235, "made simple")

    c.setFillColor(WHITE)
    c.setFont(FONT_MED, 10)
    c.drawCentredString(PAGE_W / 2, PAGE_H * 0.16, "B R A N D   G U I D E L I N E S")

    # Footer
    c.setStrokeColorRGB(1, 1, 1, alpha=0.22)
    c.setLineWidth(0.5)
    c.line(MARGIN + 12 * mm, MARGIN + 18 * mm,
           PAGE_W - MARGIN - 12 * mm, MARGIN + 18 * mm)

    c.setFillColor(WHITE)
    c.setFont(FONT_MED, 8)
    c.drawRightString(PAGE_W - MARGIN - 12 * mm, MARGIN + 11 * mm,
                      "© 2026 AUTOMATION ONE BUSINESS SYSTEMS INC.")

    c.showPage()


# ---------------------------------------------------------------------------
# Section header helper (interior pages)
# ---------------------------------------------------------------------------

def draw_section_head(c: canvas_mod.Canvas, page_num: int, title: str,
                      subtitle: str) -> float:
    y_top = PAGE_H - MARGIN - 10 * mm
    title_x = MARGIN + 24 * mm

    c.setFillColor(BLUE_100)
    c.setFont(FONT_MED, 90)
    c.drawString(MARGIN, y_top - 28 * mm, str(page_num))

    c.setFillColor(BLUE_900)
    c.setFont(FONT_MED, 32)
    c.drawString(title_x, y_top - 14 * mm, title)

    c.setFillColor(TEXT_SOFT)
    c.setFont(FONT_BOOK, 11)
    c.drawString(title_x, y_top - 22 * mm, subtitle)

    # Divider
    c.setStrokeColor(HexColor("#d3dcf2"))
    c.setLineWidth(0.6)
    c.line(MARGIN, y_top - 36 * mm, PAGE_W - MARGIN, y_top - 36 * mm)

    return y_top - 36 * mm  # y position below header for body content


# ---------------------------------------------------------------------------
# Page 4 — Colour
# ---------------------------------------------------------------------------

def draw_colour_page(c: canvas_mod.Canvas) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    y = draw_section_head(c, 4, "Primary palette",
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
        f"CMYK   {cmyk[0]}  ·  {cmyk[1]}  ·  {cmyk[2]}  ·  {cmyk[3]}",
        f"HEX     #1F5CF5",
        f"RGB     {rgb[0]}  ·  {rgb[1]}  ·  {rgb[2]}",
        f"PANTONE  2728 C (closest)",
    ]
    for i, line in enumerate(lines):
        c.drawString(hero_x + 8 * mm, hero_y + 8 * mm + (3 - i) * 5.5 * mm, line)

    # ---- Right column: neutrals + role ----
    rx = MARGIN + hero_w + 8 * mm
    rw = PAGE_W - MARGIN - rx
    # Blue 900 card
    ink_h = (hero_h - 6 * mm) / 2
    c900 = hex_to_cmyk("#061a4a")
    c.setFillColor(BLUE_900)
    c.rect(rx, hero_y + hero_h - ink_h, rw, ink_h, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(FONT_MED, 9)
    c.drawString(rx + 6 * mm, hero_y + hero_h - 10 * mm, "BLUE 900")
    c.setFont(FONT_MED, 16)
    c.drawString(rx + 6 * mm, hero_y + hero_h - 20 * mm,
                 f"{c900[0]}  ·  {c900[1]}  ·  {c900[2]}  ·  {c900[3]}")
    c.setFont(FONT_BOOK, 9)
    c.setFillColorRGB(1, 1, 1, alpha=0.78)
    c.drawString(rx + 6 * mm, hero_y + hero_h - 28 * mm,
                 "Body text on light surfaces.")

    # Paper card
    paper_cmyk = hex_to_cmyk("#f8faff")
    c.setFillColor(PAPER)
    c.rect(rx, hero_y, rw, ink_h, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#dbe5fc"))
    c.setLineWidth(0.6)
    c.rect(rx, hero_y, rw, ink_h, stroke=1, fill=0)
    c.setFillColor(BLUE_700)
    c.setFont(FONT_MED, 9)
    c.drawString(rx + 6 * mm, hero_y + ink_h - 10 * mm, "PAPER")
    c.setFillColor(BLUE_900)
    c.setFont(FONT_MED, 16)
    c.drawString(rx + 6 * mm, hero_y + ink_h - 20 * mm,
                 f"{paper_cmyk[0]}  ·  {paper_cmyk[1]}  ·  {paper_cmyk[2]}  ·  {paper_cmyk[3]}")
    c.setFillColor(TEXT_SOFT)
    c.setFont(FONT_BOOK, 9)
    c.drawString(rx + 6 * mm, hero_y + ink_h - 28 * mm,
                 "Section background, off-white.")

    # ---- Full scale row (Blue 50 → 900) ----
    scale_y = hero_y - 20 * mm
    c.setFillColor(BLUE_700)
    c.setFont(FONT_MED, 9)
    c.drawString(MARGIN, scale_y + 6 * mm, "FULL SCALE")
    c.setFillColor(BLUE_900)
    c.setFont(FONT_BOOK, 9)
    c.drawRightString(PAGE_W - MARGIN, scale_y + 6 * mm,
                      "CMYK values · tints for backgrounds, hover states, and depth.")

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
        c.drawString(sx + 2 * mm, sy + swatch_h - 6 * mm, short_name)
        c.setFont(FONT_BOOK, 5.5)
        c.drawString(sx + 2 * mm, sy + 3 * mm, cmyk_label(hexcode, compact=True))

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

    page_meta(c, 4)
    c.showPage()


# ---------------------------------------------------------------------------
# Page 6 — Typography
# ---------------------------------------------------------------------------

def draw_type_page(c: canvas_mod.Canvas) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    y = draw_section_head(c, 6, "Typography — Sequel Sans",
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

    page_meta(c, 6)
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
    draw_logo_reverse_page(c)
    draw_colour_page(c)
    draw_slogans_page(c)
    draw_type_page(c)

    c.save()


def main() -> None:
    build(OUTPUT_SITE)
    fixed = BASE / "_bg-guidelines-fixed.pdf"
    desktop = Path.home() / "Desktop" / "Automation-One-Brand-Guidelines.pdf"
    shutil.copy2(OUTPUT_SITE, fixed)
    for dest in (OUTPUT_DOWNLOADS, desktop):
        try:
            shutil.copy2(OUTPUT_SITE, dest)
            print(f"Wrote: {dest}")
        except Exception as exc:
            print(f"Warning: could not copy to {dest}: {exc}")
    print(f"Wrote: {OUTPUT_SITE}")
    print(f"Wrote: {fixed}")
    print(f"Size:  {OUTPUT_SITE.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
