#!/usr/bin/env python3
"""Generate Automation One brand guidelines PDF (blue palette + applications)."""

import os
import shutil
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch, mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing, Rect

BASE = os.path.dirname(os.path.abspath(__file__))
LOGO_MARK = os.path.join(BASE, "ao-nav-logo.png")
LOGO_BLUE_CACHE = os.path.join(BASE, "ao-nav-logo-primary.png")
AUTHORIZED_DEALER_IMG = os.path.join(BASE, "ao-authorized-dealer.png")
LOCKUP_BOX_INSET_PT = 8  # safety margin so lockups sit inside frames
FONTS_DIR = os.path.join(BASE, "fonts")
OUTPUT_SITE = os.path.join(BASE, "Automation-One-Brand-Guidelines.pdf")
OUTPUT_DL = os.path.join(os.path.expanduser("~/Downloads"), "Automation-One-Brand-Guidelines.pdf")

NAME_LINE = "Automation\u00a0One"
SUB_LINE = "Business\u00a0Systems"
BRAND_BLUE = "#1f5cf5"
MARK_RATIO = 288 / 416  # image height / width
CLEAR_SPACE = 5 * mm  # minimum clear space on all sides
MARK_TEXT_GAP_MIN = 2 * mm  # minimum space between mark and wordmark
MIN_NAME_PT = 10  # print minimum for “Automation One”
MIN_NAME_PX = 30  # digital minimum (website nav)
MIN_MARK_HEIGHT_PX = 50  # digital minimum mark height (website nav)
INK_BLACK = "#000000"
BLUE_PRIMARY = "#1f5cf5"
BLUE_DARK = "#0a2870"

# Blue-only palette (+ neutrals for print)
COLORS = {
    "Blue 50": "#eef4ff",
    "Blue 100": "#d9e6ff",
    "Blue 200": "#b3ccff",
    "Blue 300": "#7ea7ff",
    "Blue 400": "#4a82ff",
    "Blue 500 (Primary)": "#1f5cf5",
    "Blue 600": "#1547d1",
    "Blue 700": "#0f389e",
    "Blue 800": "#0a2870",
    "Blue 900": "#061a4a",
    "Ink (on light)": "#0b1330",
    "Ink soft": "#1a2347",
    "Nav / logo ink": "#2b4593",
    "Paper": "#f8faff",
    "White": "#ffffff",
    "Transition UI": "#3868f7",
}

GRADIENTS = [
    ("Hero", ["#1f5cf5", "#1547d1", "#0a2870"]),
    ("CTA & buttons", ["#1f5cf5", "#0f389e"]),
    ("Light shimmer", ["#b9d0ff", "#ffffff", "#d9e6ff"]),
    ("Section wash", ["#f8faff", "#eef4ff"]),
]

FONT_NAME = "SequelSans-Semi"
FONT_SUB = "SequelSans-Medium"
FONT_BODY = "SequelSans-Display"
FONT_BOOK = "SequelSans-Book"
FONT_REGISTERED = False
DOC_VERSION = "3.0"
PAGE_MARGIN = 1.5 * cm  # 1.5 cm on all sides
INNER_PAD = 6  # extra points inside frame so borders never touch margin edge
CONTENT_W = letter[0] - 2 * PAGE_MARGIN
SAFE_W = CONTENT_W - 2 * INNER_PAD
CONTENT_H = letter[1] - 2 * PAGE_MARGIN
PAIR_COL_GAP = 0.12 * inch


def sync_frame(doc):
    """Match platypus frame width after margins are applied."""
    global CONTENT_W, SAFE_W, CONTENT_H
    CONTENT_W = doc.width
    CONTENT_H = doc.height
    SAFE_W = CONTENT_W - 2 * INNER_PAD


def hex_color(h):
    return colors.HexColor("#" + h.lstrip("#"))


def register_fonts():
    global FONT_REGISTERED, FONT_NAME, FONT_SUB, FONT_BODY, FONT_BOOK
    if FONT_REGISTERED:
        return
    paths = {
        FONT_NAME: "SequelSans-DisplaySemi.BFge39nV.ttf",
        FONT_SUB: "SequelSans-DisplayMedium.BYsR-9NK.ttf",
        FONT_BODY: "SequelSans-Display.BSxqJqbM.ttf",
        FONT_BOOK: "SequelSans-DisplayBook.DS_QNCiF.ttf",
    }
    if all(os.path.isfile(os.path.join(FONTS_DIR, f)) for f in paths.values()):
        for key, fname in paths.items():
            pdfmetrics.registerFont(TTFont(key, os.path.join(FONTS_DIR, fname)))
        registerFontFamily(
            FONT_BOOK,
            normal=FONT_BOOK,
            bold=FONT_NAME,
            italic=FONT_BOOK,
            boldItalic=FONT_NAME,
        )
        registerFontFamily(
            FONT_BODY,
            normal=FONT_BODY,
            bold=FONT_NAME,
            italic=FONT_BODY,
            boldItalic=FONT_NAME,
        )
        FONT_REGISTERED = True
        return
    FONT_NAME = FONT_SUB = "Helvetica-Bold"
    FONT_BODY = FONT_BOOK = "Helvetica"
    registerFontFamily(FONT_BOOK, normal=FONT_BOOK, bold=FONT_NAME, italic=FONT_BOOK, boldItalic=FONT_NAME)
    FONT_REGISTERED = True


def brand_styles():
    """Typography and spacing tuned for a premium brand-system PDF."""
    register_fonts()
    ink = hex_color("#0b1330")
    ink_soft = hex_color("#1a2347")
    blue = hex_color(BRAND_BLUE)
    muted = hex_color("#5a6f9e")
    return {
        "display": ParagraphStyle(
            "AODisplay",
            fontName=FONT_NAME,
            fontSize=34,
            leading=38,
            textColor=ink,
            spaceAfter=4,
        ),
        "cover_kicker": ParagraphStyle(
            "AOKicker",
            fontName=FONT_NAME,
            fontSize=9,
            leading=11,
            textColor=muted,
            spaceAfter=14,
        ),
        "cover_sub": ParagraphStyle(
            "AOCoverSub",
            fontName=FONT_BOOK,
            fontSize=12,
            leading=17,
            textColor=ink_soft,
            spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "AOH2",
            fontName=FONT_NAME,
            fontSize=20,
            leading=24,
            textColor=ink,
            spaceBefore=6,
            spaceAfter=12,
        ),
        "h3": ParagraphStyle(
            "AOH3",
            fontName=FONT_NAME,
            fontSize=12,
            leading=15,
            textColor=hex_color("#1547d1"),
            spaceBefore=14,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "AOBody",
            fontName=FONT_BOOK,
            fontSize=10.5,
            leading=16,
            textColor=ink_soft,
            spaceAfter=10,
            splitLongWords=True,
        ),
        "lead": ParagraphStyle(
            "AOLead",
            fontName=FONT_BOOK,
            fontSize=12,
            leading=18,
            textColor=ink_soft,
            spaceAfter=14,
        ),
        "caption": ParagraphStyle(
            "AOCap",
            fontName=FONT_BODY,
            fontSize=8.5,
            leading=12,
            textColor=hex_color("#0f389e"),
            spaceAfter=8,
        ),
        "toc_item": ParagraphStyle(
            "AOToc",
            fontName=FONT_BOOK,
            fontSize=11,
            leading=22,
            textColor=ink_soft,
            leftIndent=0,
        ),
        "toc_num": ParagraphStyle(
            "AOTocNum",
            fontName=FONT_NAME,
            fontSize=11,
            leading=22,
            textColor=blue,
            alignment=TA_RIGHT,
        ),
        "panel_title": ParagraphStyle(
            "AOPanelTitle",
            fontName=FONT_NAME,
            fontSize=11,
            textColor=blue,
            spaceAfter=8,
        ),
        "label": ParagraphStyle(
            "AOLabel",
            fontName=FONT_BODY,
            fontSize=7.5,
            textColor=muted,
            alignment=TA_CENTER,
        ),
        "principle_title": ParagraphStyle(
            "AOPrinciple",
            fontName=FONT_NAME,
            fontSize=11,
            textColor=ink,
            spaceAfter=4,
        ),
        "principle_body": ParagraphStyle(
            "AOPrincipleBody",
            fontName=FONT_BOOK,
            fontSize=9,
            leading=13,
            textColor=ink_soft,
        ),
    }


def premium_table(rows, col_widths, font_size=9, header_fill="#0a2870"):
    """Tables with navy header, wrapped Paragraph cells (no column bleed)."""
    register_fonts()
    lead = font_size + 4
    head_st = ParagraphStyle(
        "ptHead",
        fontName=FONT_NAME,
        fontSize=font_size,
        leading=lead,
        textColor=hex_color("#ffffff"),
    )
    body_st = ParagraphStyle(
        "ptBody",
        fontName=FONT_BOOK,
        fontSize=font_size,
        leading=lead,
        textColor=hex_color("#1a2347"),
    )
    data = []
    for r, row in enumerate(rows):
        if r == 0:
            data.append([Paragraph(f"<b>{cell}</b>", head_st) for cell in row])
        else:
            data.append([Paragraph(cell, body_st) for cell in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), hex_color(header_fill)),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 1), (-1, -2), 0.35, hex_color("#e2ebff")),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), hex_color("#fafcff")))
    t.setStyle(TableStyle(cmds))
    return wrap_to_safe_width(t)


def table_cols_fixed(*widths_inch):
    """Column widths in inches; last column fills remainder; total never exceeds SAFE_W."""
    if len(widths_inch) == 1:
        return [SAFE_W]
    fixed = sum(w * inch for w in widths_inch[:-1])
    last = SAFE_W - fixed
    if last < 0.55 * inch:
        scale = (SAFE_W - 0.55 * inch) / max(fixed, 1)
        fixed = fixed * scale
        last = SAFE_W - fixed
    return [w * inch for w in widths_inch[:-1]] + [last]


def two_col_widths(gap=None):
    """Equal column widths for side-by-side panels within safe area."""
    g = PAIR_COL_GAP if gap is None else gap
    half = (SAFE_W - g) / 2.0
    return half, half


def wrap_to_safe_width(flowable):
    """Force any flowable/table to stay inside SAFE_W."""
    t = Table([[flowable]], colWidths=[SAFE_W])
    t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def section_band(number, title, subtitle=None):
    """Section opener — numeral top-aligned with title; rule below both."""
    st = brand_styles()
    title_p = Paragraph(title, st["h2"])
    out = []
    if number is not None and str(number).strip() != "":
        num_style = ParagraphStyle(
            "secN",
            fontName=FONT_NAME,
            fontSize=20,
            leading=24,
            textColor=hex_color("#1f5cf5"),
            spaceBefore=0,
            spaceAfter=0,
        )
        num = Paragraph(number, num_style)
        header = Table([[num, title_p]], colWidths=[0.42 * inch, SAFE_W - 0.42 * inch])
        header.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (0, 0), 0),
                    ("RIGHTPADDING", (0, 0), (0, 0), 8),
                ]
            )
        )
        out.append(header)
    else:
        out.append(title_p)
    rule = Table([[""]], colWidths=[SAFE_W], rowHeights=[3])
    rule.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 0), (-1, 0), 2, hex_color("#1f5cf5")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    out.append(rule)
    if subtitle:
        out.append(Paragraph(subtitle, st["lead"]))
    out.append(Spacer(1, 0.18 * inch))
    return out


def brand_principles_row():
    st = brand_styles()
    pillars = [
        ("Clarity", "One blue palette. One type family. Every application should feel unmistakably Automation One."),
        ("Consistency", "Primary lockup first. Secondary only on brand blue. Alternates are the exception, not the default."),
        ("Restraint", "Generous space, precise alignment, and production-ready minimums — never decorative clutter."),
    ]
    cols = []
    for title, text in pillars:
        cols.append(
            [
                Paragraph(title, st["principle_title"]),
                Paragraph(text, st["principle_body"]),
            ]
        )
    t = Table([cols], colWidths=[SAFE_W / 3.0] * 3)
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ("TOPPADDING", (0, 0), (-1, -1), 18),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
                ("BACKGROUND", (0, 0), (-1, -1), hex_color("#f8faff")),
                ("BOX", (0, 0), (-1, -1), 0.5, hex_color("#d9e6ff")),
                ("LINEAFTER", (0, 0), (0, -1), 0.5, hex_color("#d9e6ff")),
                ("LINEAFTER", (1, 0), (1, -1), 0.5, hex_color("#d9e6ff")),
            ]
        )
    )
    return wrap_to_safe_width(t)


def table_of_contents():
    st = brand_styles()
    entries = [
        ("1", "Brand overview"),
        ("2", "Logo & lockups"),
        ("3", "Colour system"),
        ("4", "Typography"),
        ("5", "Applications"),
        ("6", "Usage standards"),
    ]
    rows = []
    for num, label in entries:
        rows.append(
            [
                Paragraph(num, st["toc_num"]),
                Paragraph(label, st["toc_item"]),
            ]
        )
    t = Table(rows, colWidths=[0.5 * inch, SAFE_W - 0.5 * inch])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, hex_color("#e8efff")),
            ]
        )
    )
    return t


def elevated_frame(inner_table, pad=10, shadow="#d9e6ff", bg="#ffffff"):
    """Soft card frame for application mockups."""
    outer = Table([[inner_table]], colWidths=[SAFE_W])
    outer.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), hex_color(bg)),
                ("BOX", (0, 0), (-1, -1), 0.5, hex_color(shadow)),
                ("TOPPADDING", (0, 0), (-1, -1), pad + 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), pad + 6),
                ("LEFTPADDING", (0, 0), (-1, -1), pad + 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), pad),
            ]
        )
    )
    shadow_row = Table([[outer]], colWidths=[SAFE_W])
    shadow_row.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), hex_color("#eef4ff")),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return shadow_row


def m_index_in_automation(text):
    t = text.replace("\u00a0", " ")
    auto = (t.split()[0] if t.split() else t)
    for i, c in enumerate(auto):
        if c in "mM":
            return t.index(c)
    return t.lower().find("m")


def text_width(text, font, size_pt, char_space=0):
    if not text:
        return 0.0
    w = 0.0
    for i, ch in enumerate(text):
        w += pdfmetrics.stringWidth(ch, font, size_pt)
        if i < len(text) - 1:
            w += char_space
    return w


def fit_sub_size_pt(name_size_pt):
    """Match ao-logo-lockup.js: sub ~53.5% of name, B under m, right edges aligned."""
    register_fonts()
    name_cs = -0.02 * name_size_pt
    sub_cs = 0.01 * name_size_pt
    lock_w = text_width(NAME_LINE, FONT_NAME, name_size_pt, name_cs)
    mi = m_index_in_automation(NAME_LINE)
    m_left = text_width(NAME_LINE[:mi], FONT_NAME, name_size_pt, name_cs)

    best_px = name_size_pt * 0.535
    best_score = 1e9
    px = name_size_pt * 0.46
    end = name_size_pt * 0.60
    while px <= end + 0.001:
        sub_w = text_width(SUB_LINE, FONT_SUB, px, sub_cs)
        b_gap = (lock_w - sub_w) - m_left
        score = abs(b_gap)
        if score < best_score:
            best_score = score
            best_px = px
        px += 0.05
    return best_px, lock_w, name_cs, sub_cs


def pt_to_mm(pt):
    return pt * 25.4 / 72.0


def effective_mark_text_gap(gap_pt=None):
    """Gap between mark and wordmark — never less than MARK_TEXT_GAP_MIN."""
    if gap_pt is None:
        return MARK_TEXT_GAP_MIN
    return max(gap_pt, MARK_TEXT_GAP_MIN)


def draw_text_line(c, x, y, text, font, size_pt, color, char_space=0, align="left", box_width=0):
    """Single-line text (never wraps)."""
    c.setFillColor(color)
    c.setFont(font, size_pt)
    tw = text_width(text, font, size_pt, char_space)
    ox = x + (box_width - tw) if align == "right" and box_width else x
    if char_space:
        cx = ox
        for i, ch in enumerate(text):
            c.drawString(cx, y, ch)
            cx += pdfmetrics.stringWidth(ch, font, size_pt) + (char_space if i < len(text) - 1 else 0)
    else:
        c.drawString(ox, y, text)


class AoStackedLockupFlowable(Flowable):
    """Canvas-drawn stacked lockup — no paragraph wrapping."""

    def __init__(self, name_size_pt, ink="#0b1330", sub_ink=None, mark_tint=None, on_dark=False):
        Flowable.__init__(self)
        register_fonts()
        if on_dark:
            ink, sub_ink = "#ffffff", "#ffffff"
            mark_tint = "#ffffff"
        if sub_ink is None:
            sub_ink = ink
        self.name_size_pt = name_size_pt
        self.ink = hex_color(ink)
        self.sub_ink = hex_color(sub_ink)
        self.mark_tint = mark_tint
        self.sub_pt, self.lock_w, self.name_cs, self.sub_cs = fit_sub_size_pt(name_size_pt)
        self.mark_text_gap = MARK_TEXT_GAP_MIN
        self.width, self.height = lockup_dimensions_pt(name_size_pt, horizontal=False)

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        lock_w = self.lock_w
        y = 0
        draw_text_line(c, 0, y, SUB_LINE, FONT_SUB, self.sub_pt, self.sub_ink, self.sub_cs, "right", lock_w)
        y += self.sub_pt * 1.05 + 2
        draw_text_line(c, 0, y, NAME_LINE, FONT_NAME, self.name_size_pt, self.ink, self.name_cs, "left", lock_w)
        y += self.name_size_pt * 1.05 + self.mark_text_gap
        mark_h = lock_w * MARK_RATIO
        if self.mark_tint and os.path.isfile(LOGO_MARK):
            path = ensure_tinted_logo(self.mark_tint)
            c.drawImage(ImageReader(path), 0, y, width=lock_w, height=mark_h, mask="auto", preserveAspectRatio=True)


class AoHorizontalLockupFlowable(Flowable):
    """Canvas-drawn horizontal lockup — no paragraph wrapping."""

    def __init__(self, name_size_pt, ink="#0b1330", sub_ink=None, mark_tint=None, on_dark=False, gap_pt=10):
        Flowable.__init__(self)
        register_fonts()
        if on_dark:
            ink, sub_ink = "#ffffff", "#ffffff"
            mark_tint = "#ffffff"
        if sub_ink is None:
            sub_ink = ink
        self.name_size_pt = name_size_pt
        self.ink = hex_color(ink)
        self.sub_ink = hex_color(sub_ink)
        self.mark_tint = mark_tint
        self.gap_pt = effective_mark_text_gap(gap_pt)
        self.sub_pt, self.lock_w, self.name_cs, self.sub_cs = fit_sub_size_pt(name_size_pt)
        self.width, self.height = lockup_dimensions_pt(name_size_pt, horizontal=True, gap_pt=gap_pt)
        self.mark_w = (self.name_size_pt * 1.05 + 2 + self.sub_pt * 1.05) / MARK_RATIO

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        text_h = self.name_size_pt * 1.05 + 2 + self.sub_pt * 1.05
        tx = self.mark_w + self.gap_pt
        lock_w = self.lock_w
        draw_text_line(c, tx, 0, SUB_LINE, FONT_SUB, self.sub_pt, self.sub_ink, self.sub_cs, "right", lock_w)
        draw_text_line(c, tx, self.sub_pt * 1.05 + 2, NAME_LINE, FONT_NAME, self.name_size_pt, self.ink, self.name_cs, "left", lock_w)
        mark_h = text_h
        if self.mark_tint and os.path.isfile(LOGO_MARK):
            path = ensure_tinted_logo(self.mark_tint)
            c.drawImage(ImageReader(path), 0, 0, width=self.mark_w, height=mark_h, mask="auto", preserveAspectRatio=True)


def ensure_tinted_logo(hex_rgb):
    if os.path.isfile(LOGO_BLUE_CACHE) and hex_rgb.lower() == BRAND_BLUE.lower():
        return LOGO_BLUE_CACHE
    try:
        from PIL import Image
    except ImportError:
        return LOGO_MARK
    im = Image.open(LOGO_MARK).convert("RGBA")
    r = int(hex_rgb[1:3], 16)
    g = int(hex_rgb[3:5], 16)
    b = int(hex_rgb[5:7], 16)
    px = []
    for item in im.getdata():
        if item[3] > 8:
            px.append((r, g, b, item[3]))
        else:
            px.append((0, 0, 0, 0))
    im.putdata(px)
    out = LOGO_BLUE_CACHE if hex_rgb.lower() == BRAND_BLUE.lower() else os.path.join(BASE, f"ao-nav-logo-{hex_rgb[1:]}.png")
    im.save(out)
    return out


def logo_img(w_inch, tint=None):
    path = LOGO_MARK
    if tint:
        path = ensure_tinted_logo(tint)
    if not os.path.isfile(path):
        return ""
    return RLImage(path, width=w_inch, height=w_inch * MARK_RATIO)


def lockup_stacked(name_size_pt=22, **kwargs):
    return AoStackedLockupFlowable(name_size_pt=name_size_pt, **kwargs)


def lockup_horizontal(name_size_pt=22, gap_pt=10, **kwargs):
    return AoHorizontalLockupFlowable(name_size_pt=name_size_pt, gap_pt=gap_pt, **kwargs)


def lockup_dimensions_pt(name_size_pt, horizontal=False, gap_pt=10):
    """Return (width, height) in PDF points for a lockup at the given name size."""
    register_fonts()
    sub_pt, lock_w_pt, _, _ = fit_sub_size_pt(name_size_pt)
    text_h_pt = name_size_pt * 1.05 + 2 + sub_pt * 1.05
    gap = effective_mark_text_gap(gap_pt) if horizontal else MARK_TEXT_GAP_MIN
    if horizontal:
        mark_w_pt = text_h_pt / MARK_RATIO
        return mark_w_pt + gap + lock_w_pt, text_h_pt
    mark_h_pt = lock_w_pt * MARK_RATIO
    return lock_w_pt, mark_h_pt + gap + text_h_pt


def choose_name_size_pt(max_w_pt, max_h_pt, horizontal=False, gap_pt=10, max_start=28, inset_pt=None):
    """Largest name size (pt) that fits inside max_w × max_h; never below MIN_NAME_PT."""
    inset = LOCKUP_BOX_INSET_PT if inset_pt is None else inset_pt
    max_w_pt = max(max_w_pt - inset, MIN_NAME_PT * 4)
    max_h_pt = max(max_h_pt - inset, MIN_NAME_PT * 4)
    pt = max_start
    while pt >= MIN_NAME_PT:
        w, h = lockup_dimensions_pt(pt, horizontal=horizontal, gap_pt=gap_pt)
        if w <= max_w_pt and h <= max_h_pt:
            return max(pt, MIN_NAME_PT)
        pt -= 0.25
    return MIN_NAME_PT


class CoverPageSpacer(Flowable):
    """Reserve the first page for canvas-drawn cover art."""

    def wrap(self, availWidth, availHeight):
        return availWidth, max(availHeight - 1, 1)

    def draw(self):
        pass


class ClearSpaceGuideFlowable(Flowable):
    """Dashed 5 mm clear-space guide around a lockup."""

    def __init__(self, lockup, clear=CLEAR_SPACE):
        Flowable.__init__(self)
        self.lockup = lockup
        self.clear = clear
        self.width = lockup.width + 2 * clear
        self.height = lockup.height + 2 * clear

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setStrokeColor(hex_color("#7ea7ff"))
        c.setDash(3, 2)
        c.setLineWidth(0.6)
        c.rect(0, 0, self.width, self.height, stroke=1, fill=0)
        self.lockup.drawOn(c, self.clear, self.clear)
        c.restoreState()


def lockup_box(lockup_flowable, box_w, box_h, padding=0.08 * inch):
    """Center a lockup inside a fixed-size frame; expand inner cell if guide needs more room."""
    inner_w = max(box_w - 2 * padding, 1)
    inner_h = max(box_h - 2 * padding, 1)
    aw, ah = lockup_flowable.wrap(inner_w, inner_h)
    inner_w = max(inner_w, aw)
    inner_h = max(inner_h, ah)
    if inner_w > box_w - 2 * padding:
        inner_w = max(box_w - 2 * padding, 1)
    inner = Table([[lockup_flowable]], colWidths=[inner_w], rowHeights=[inner_h])
    inner.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    outer = Table([[inner]], colWidths=[box_w], rowHeights=[box_h])
    outer.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), padding),
                ("RIGHTPADDING", (0, 0), (-1, -1), padding),
                ("TOPPADDING", (0, 0), (-1, -1), padding),
                ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
            ]
        )
    )
    return outer


def lockup_stacked_fitted(box_w, box_h, padding=0.14 * inch, show_clear=False, **kwargs):
    clear_extra = 2 * CLEAR_SPACE if show_clear else 0
    inner_w = box_w - 2 * padding - clear_extra - LOCKUP_BOX_INSET_PT
    inner_h = box_h - 2 * padding - clear_extra - LOCKUP_BOX_INSET_PT
    pt = choose_name_size_pt(inner_w, inner_h, horizontal=False)
    flow = lockup_stacked(name_size_pt=pt, **kwargs)
    if show_clear:
        flow = ClearSpaceGuideFlowable(flow)
    return lockup_box(flow, box_w, box_h, padding)


def lockup_horizontal_fitted(box_w, box_h, padding=0.14 * inch, gap_pt=10, show_clear=False, **kwargs):
    inner_w = box_w - 2 * padding - 2 * CLEAR_SPACE - LOCKUP_BOX_INSET_PT
    inner_h = box_h - 2 * padding - 2 * CLEAR_SPACE - LOCKUP_BOX_INSET_PT
    pt = choose_name_size_pt(inner_w, inner_h, horizontal=True, gap_pt=gap_pt)
    flow = lockup_horizontal(name_size_pt=pt, gap_pt=gap_pt, **kwargs)
    if show_clear:
        flow = ClearSpaceGuideFlowable(flow)
    return lockup_box(flow, box_w, box_h, padding)


def minimum_size_specs_table():
    register_fonts()
    sub_pt, lock_w, _, _ = fit_sub_size_pt(MIN_NAME_PT)
    mark_h_pt = lock_w * MARK_RATIO
    rows = [
        ["Element", "Print minimum", "Digital minimum (website)"],
        ["“Automation One”", f"{MIN_NAME_PT} pt", f"{MIN_NAME_PX} px"],
        ["“Business Systems”", f"{sub_pt:.1f} pt (~53% of name)", "Scales with name (JS lockup)"],
        ["Mark width (stacked)", f"{pt_to_mm(lock_w):.1f} mm", "Matches name width"],
        ["Mark height (horizontal nav)", f"{pt_to_mm(mark_h_pt):.1f} mm at min", f"{MIN_MARK_HEIGHT_PX} px"],
        ["Clear space (all sides)", "5 mm", "5 mm"],
        [
            "Mark ↔ wordmark gap",
            f"{pt_to_mm(MARK_TEXT_GAP_MIN):.0f} mm minimum",
            f"{pt_to_mm(MARK_TEXT_GAP_MIN):.0f} mm minimum",
        ],
    ]
    return premium_table(rows, table_cols_fixed(1.45, 1.85), font_size=9)


def minimum_size_example_panel():
    """Visual reference: lockup at minimum print size (MIN_NAME_PT name)."""
    register_fonts()
    sub_pt, lock_w, _, _ = fit_sub_size_pt(MIN_NAME_PT)
    cap = brand_styles()["label"]
    sw, sh = lockup_dimensions_pt(MIN_NAME_PT, horizontal=False)
    hw, hh = lockup_dimensions_pt(MIN_NAME_PT, horizontal=True, gap_pt=10)
    pad = 16
    cell_st_w = sw + pad + LOCKUP_BOX_INSET_PT
    cell_h_w = hw + pad + LOCKUP_BOX_INSET_PT
    cell_h = sh + pad + LOCKUP_BOX_INSET_PT
    total_w = cell_st_w + cell_h_w
    if total_w > SAFE_W:
        scale = SAFE_W / total_w
        cell_st_w *= scale
        cell_h_w *= scale
    lbl = (
        f"<b>Minimum size example</b> — “Automation One” <b>{MIN_NAME_PT} pt</b>, "
        f"“Business Systems” <b>{sub_pt:.1f} pt</b>, mark width <b>{pt_to_mm(lock_w):.1f} mm</b>. "
        "All other lockups in this document are this size or larger."
    )
    row = Table(
        [
            [Paragraph("Stacked · minimum", cap), Paragraph("Horizontal · minimum", cap)],
            [
                lockup_box(
                    lockup_stacked(name_size_pt=MIN_NAME_PT, **LOCKUP_KW_PRIMARY),
                    cell_st_w,
                    cell_h,
                    padding=8,
                ),
                lockup_box(
                    lockup_horizontal(name_size_pt=MIN_NAME_PT, gap_pt=10, **LOCKUP_KW_PRIMARY),
                    cell_h_w,
                    cell_h,
                    padding=8,
                ),
            ],
        ],
        colWidths=[cell_st_w, cell_h_w],
        rowHeights=[0.22 * inch, cell_h + 0.06 * inch],
    )
    row.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 1), (-1, 1), hex_color("#ffffff")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 1, hex_color("#7ea7ff")),
                ("BOX", (0, 1), (-1, 1), 0.5, hex_color("#d9e6ff")),
            ]
        )
    )
    wrap = Table([[Paragraph(lbl, cap)], [row]], colWidths=[SAFE_W])
    wrap.setStyle(TableStyle([("BOTTOMPADDING", (0, 0), (-1, 0), 8)]))
    return wrap_to_safe_width(wrap)


LOCKUP_KW_PRIMARY = dict(ink=BRAND_BLUE, sub_ink=BRAND_BLUE, mark_tint=BRAND_BLUE)
LOCKUP_KW_SECONDARY = dict(ink="#ffffff", sub_ink="#ffffff", mark_tint="#ffffff")
LOCKUP_KW_ALT_BLACK = dict(ink=INK_BLACK, sub_ink=INK_BLACK, mark_tint=INK_BLACK)
LOCKUP_KW_ALT_DARK_BLUE = dict(ink=BLUE_DARK, sub_ink=BLUE_DARK, mark_tint=BLUE_DARK)
LOCKUP_KW_ALT_WHITE = dict(ink="#ffffff", sub_ink="#ffffff", mark_tint="#ffffff")
INK_BLACK_BG = "#000000"

SPEC_PAIR_W = 2.65 * inch
SPEC_PAIR_H = 1.55 * inch
SPEC_PAIR_PAD = 0.14 * inch


def lockup_pair_table(cell_w, cell_h, pad, bg_hex, lockup_kw, border_hex="#d9e6ff"):
    """Stacked + horizontal lockups side by side on one background."""
    lbl = brand_styles()["label"]
    cell_w = min(cell_w, (SAFE_W - PAIR_COL_GAP) / 2.0)
    t = Table(
        [
            [Paragraph("<b>Stacked</b>", lbl), Paragraph("<b>Horizontal</b>", lbl)],
            [
                lockup_stacked_fitted(cell_w, cell_h, padding=pad, **lockup_kw),
                lockup_horizontal_fitted(cell_w, cell_h, padding=pad, gap_pt=10, **lockup_kw),
            ],
        ],
        colWidths=[cell_w, cell_w],
        rowHeights=[0.2 * inch, cell_h + 0.08 * inch],
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 1), (-1, 1), hex_color(bg_hex)),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("TOPPADDING", (0, 1), (-1, 1), 10),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
                ("LEFTPADDING", (0, 1), (-1, 1), 8),
                ("RIGHTPADDING", (0, 1), (-1, 1), 8),
                ("BOX", (0, 1), (-1, 1), 0.5, hex_color(border_hex)),
            ]
        )
    )
    return wrap_to_safe_width(t)


def lockup_primary_blue_panel():
    """Approved Primary — Blue 500 on white with 5 mm clear-space guide."""
    panel_w = SAFE_W
    panel_h = 2.55 * inch
    inner = lockup_stacked_fitted(
        panel_w,
        panel_h,
        padding=0.18 * inch,
        show_clear=True,
        **LOCKUP_KW_PRIMARY,
    )
    panel = Table([[inner]], colWidths=[panel_w], rowHeights=[panel_h])
    panel.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), hex_color("#ffffff")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.5, hex_color("#d9e6ff")),
            ]
        )
    )
    return wrap_to_safe_width(panel)


def approval_tier_table():
    """Summary: Primary / Secondary / Alternate definitions."""
    rows = [
        ["Tier", "Mark & wordmark", "Background", "When to use"],
        [
            "Approved Primary",
            "#1F5CF5",
            "White / paper",
            "Default — all marketing, print, and web on light fields",
        ],
        [
            "Approved Secondary",
            "White",
            f"Blue 500 ({BLUE_PRIMARY.upper()})",
            "Brand-blue fields only — same blue as the logo colour",
        ],
        [
            "Approved Alternate",
            "Black, Blue 800, or white",
            "Paired: blue/white fields; black/white fields",
            "Only when Primary or Secondary cannot be used",
        ],
    ]
    return premium_table(rows, table_cols_fixed(1.05, 0.95, 0.95), font_size=8.5)


ALT_GROUP_W = 2.65 * inch  # may be widened in build_pdf via layout_minimums()


def layout_minimums():
    """Container sizes (points) so fitted lockups can render at MIN_NAME_PT or larger."""
    register_fonts()
    pad = 24 + LOCKUP_BOX_INSET_PT
    sw, sh = lockup_dimensions_pt(MIN_NAME_PT, horizontal=False)
    hw, hh = lockup_dimensions_pt(MIN_NAME_PT, horizontal=True, gap_pt=10)
    half_w, _ = two_col_widths()
    cell_inner = half_w - 0.28 * inch - LOCKUP_BOX_INSET_PT
    return {
        "spec_pair_h": max(SPEC_PAIR_H, sh + pad + 10),
        "spec_pair_w": min(half_w, max(sw + pad + 10, hw + pad + 10, SPEC_PAIR_W)),
        "alt_variant_h": max(1.55 * inch, sh + pad + 12),
        "alt_group_w": half_w,
        "biz_lockup_h": max(0.85 * inch, hh + pad),
        "letter_lockup_h": max(0.6 * inch, hh + pad),
        "horiz_primary_h": max(0.95 * inch, hh + pad),
    }


def alternate_group_panel(group_title, variants, group_w=ALT_GROUP_W, variant_h=None):
    """Pair of alternate treatments in one grouped panel (e.g. blue on white + white on blue)."""
    st = brand_styles()
    grp_h = ParagraphStyle(
        "grpH",
        parent=st["label"],
        fontName=FONT_NAME,
        fontSize=8,
        textColor=hex_color("#1547d1"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    alt_lbl = st["label"]
    half_w = (group_w - 0.06 * inch) / 2
    alt_h = variant_h if variant_h is not None else 0.95 * inch
    alt_pad = 0.14 * inch
    inner_rows = [[Paragraph(f"<b>{group_title}</b>", grp_h)]]
    inner_heights = [0.2 * inch]
    lockup_row_indices = []
    for label, kw, bg, border in variants:
        inner_rows.append([Paragraph(f"<i>{label}</i>", alt_lbl), Paragraph(f"<i>{label}</i>", alt_lbl)])
        inner_rows.append(
            [
                lockup_stacked_fitted(half_w, alt_h, padding=alt_pad, **kw),
                lockup_horizontal_fitted(half_w, alt_h, padding=alt_pad, gap_pt=10, **kw),
            ]
        )
        inner_heights.extend([0.14 * inch, alt_h + 0.1 * inch])
        lockup_row_indices.append((len(inner_rows) - 1, bg, border))
    inner = Table(inner_rows, colWidths=[half_w, half_w], rowHeights=inner_heights)
    style = [
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), hex_color("#eef4ff")),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
    ]
    for r, bg, border in lockup_row_indices:
        style.append(("BACKGROUND", (0, r), (-1, r), hex_color(bg)))
        style.append(("BOX", (0, r), (-1, r), 0.5, hex_color(border)))
        style.append(("TOPPADDING", (0, r), (-1, r), 10))
        style.append(("BOTTOMPADDING", (0, r), (-1, r), 10))
        style.append(("LEFTPADDING", (0, r), (-1, r), 8))
        style.append(("RIGHTPADDING", (0, r), (-1, r), 8))
    inner.setStyle(TableStyle(style))
    outer = Table([[inner]], colWidths=[group_w])
    outer.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, hex_color("#b3ccff")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return outer


def alternate_lockups_grid(alt_group_w=ALT_GROUP_W, alt_variant_h=None):
    """Alternate lockups in two paired groups side by side."""
    blue_panel = alternate_group_panel(
        "Blue 800 pair",
        [
            (f"Blue 800 on white", LOCKUP_KW_ALT_DARK_BLUE, "#ffffff", "#b3ccff"),
            (f"White on Blue 800", LOCKUP_KW_ALT_WHITE, BLUE_DARK, "#061a4a"),
        ],
        group_w=alt_group_w,
        variant_h=alt_variant_h,
    )
    mono_panel = alternate_group_panel(
        "Monochrome pair",
        [
            ("Black on white", LOCKUP_KW_ALT_BLACK, "#ffffff", "#d9e6ff"),
            ("White on black", LOCKUP_KW_ALT_WHITE, INK_BLACK_BG, "#333333"),
        ],
        group_w=alt_group_w,
        variant_h=alt_variant_h,
    )
    gap = PAIR_COL_GAP
    half = (SAFE_W - gap) / 2.0
    t = Table([[blue_panel, "", mono_panel]], colWidths=[half, gap, half], rowHeights=[None])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (2, 0), (2, 0), "CENTER"),
            ]
        )
    )
    return wrap_to_safe_width(t)


def approved_fonts_section():
    """Approved typefaces table + usage (matches website fonts-jeton.css)."""
    register_fonts()
    rows = [
        ["Role", "Typeface", "Weight / file", "Use on site & print"],
        [
            "Primary (all text)",
            "Sequel Sans Display",
            "400 — SequelSans-Display",
            "Body copy, UI, default sans-serif",
        ],
        [
            "Primary",
            "Sequel Sans Display Book",
            "450 — SequelSans-DisplayBook",
            "Optional book weight",
        ],
        [
            "Logo subline · UI emphasis",
            "Sequel Sans Display Medium",
            "500 — SequelSans-DisplayMedium",
            "“Business Systems”, buttons, subheads",
        ],
        [
            "Logo name · headings",
            "Sequel Sans Display Semi",
            "600 — SequelSans-DisplaySemi",
            "“Automation One”, headings, logo name line",
        ],
        [
            "Fallback stack (web only)",
            "Inter, Montserrat",
            "—",
            "If Sequel Sans fails to load",
        ],
        [
            "Fallback (system)",
            "system-ui, sans-serif",
            "—",
            "Final web fallback",
        ],
    ]
    return premium_table(rows, table_cols_fixed(0.95, 1.5, 1.35), font_size=8.5)


def swatch_card(name, hex_val, card_w):
    chip = Table([[""]], colWidths=[0.38 * inch], rowHeights=[0.38 * inch])
    chip.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), hex_color(hex_val)),
                ("BOX", (0, 0), (-1, -1), 0.25, hex_color("#d9e6ff")),
            ]
        )
    )
    st = brand_styles()
    meta = Table(
        [
            [Paragraph(f"<b>{name}</b>", st["principle_title"])],
            [Paragraph(hex_val.upper(), st["caption"])],
        ],
        colWidths=[max(card_w - 0.48 * inch, 0.9 * inch)],
    )
    meta.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    row = Table([[chip, meta]], colWidths=[0.42 * inch, max(card_w - 0.42 * inch, 0.85 * inch)])
    row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), hex_color("#ffffff")),
                ("BOX", (0, 0), (-1, -1), 0.35, hex_color("#e8efff")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return row


def swatch_grid():
    items = list(COLORS.items())
    col_w = SAFE_W / 3.0
    rows = []
    for i in range(0, len(items), 3):
        chunk = items[i : i + 3]
        cells = [swatch_card(n, h, col_w) for n, h in chunk]
        while len(cells) < 3:
            cells.append("")
        rows.append(cells)
    t = Table(rows, colWidths=[SAFE_W / 3.0] * 3)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return wrap_to_safe_width(t)


def gradient_strip(stops, width=None, height=0.45 * inch):
    if width is None:
        width = SAFE_W
    d = Drawing(width, height)
    w = width / len(stops)
    for i, h in enumerate(stops):
        d.add(Rect(i * w, 0, w, height, fillColor=hex_color(h), strokeColor=None))
    return d


def mockup_panel(title, content_table, caption_text, bg="#f8faff", pad=20):
    st = brand_styles()
    inner = Table(
        [[Paragraph(title, st["panel_title"])], [content_table]],
        colWidths=[SAFE_W - 2 * pad],
    )
    inner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), hex_color(bg)),
                ("TOPPADDING", (0, 0), (-1, -1), pad),
                ("BOTTOMPADDING", (0, 0), (-1, -1), pad - 4),
                ("LEFTPADDING", (0, 0), (-1, -1), pad),
                ("RIGHTPADDING", (0, 0), (-1, -1), pad),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return [elevated_frame(inner), Paragraph(caption_text, st["caption"]), Spacer(1, 0.2 * inch)]


def business_card_mockup(lockup_h=0.85 * inch):
    st = brand_styles()
    card_w, _ = two_col_widths(0.12 * inch)
    card_w = min(card_w, 2.65 * inch)
    card_h = 1.55 * inch
    contact = ParagraphStyle("cardContact", fontName=FONT_BODY, fontSize=7.5, textColor=hex_color("#1547d1"), leading=10)
    front = Table(
        [
            [
                lockup_horizontal_fitted(
                    card_w - 0.32 * inch,
                    lockup_h,
                    padding=0.06 * inch,
                    gap_pt=7,
                    **LOCKUP_KW_PRIMARY,
                )
            ],
            [
                Paragraph("604-255-6622 · automationone.ca", contact),
            ],
        ],
        colWidths=[card_w],
        rowHeights=[lockup_h + 0.08 * inch, card_h - lockup_h - 0.08 * inch],
    )
    front.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 18),
                ("RIGHTPADDING", (0, 0), (-1, -1), 18),
                ("TOPPADDING", (0, 0), (0, 0), 14),
                ("TOPPADDING", (0, 1), (0, 1), 2),
                ("BACKGROUND", (0, 0), (-1, -1), hex_color("#ffffff")),
                ("BOX", (0, 0), (-1, -1), 0.5, hex_color("#d9e6ff")),
            ]
        )
    )

    tagline = ParagraphStyle("cardTag", fontName=FONT_NAME, fontSize=10, leading=13, textColor=hex_color("#ffffff"), alignment=TA_CENTER)
    back = Table(
        [[Paragraph("Business solutions<br/>made simple.", tagline)]],
        colWidths=[card_w],
        rowHeights=[card_h],
    )
    back.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), hex_color(BRAND_BLUE)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 0.5, hex_color("#1547d1")),
            ]
        )
    )

    lbl = st["label"]
    cards = Table(
        [
            [Paragraph("Front", lbl), Paragraph("Back", lbl)],
            [front, back],
        ],
        colWidths=[card_w, card_w],
    )
    cards.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ]
        )
    )
    cards_wrap = Table([[cards]], colWidths=[SAFE_W])
    cards_wrap.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    return cards_wrap


def signage_mockup():
    panel_w = SAFE_W
    panel_h = 1.65 * inch
    panel = Table(
        [[lockup_horizontal_fitted(panel_w, panel_h, padding=0.12 * inch, gap_pt=10, **LOCKUP_KW_SECONDARY)]],
        colWidths=[panel_w],
        rowHeights=[panel_h],
    )
    panel.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), hex_color(BLUE_PRIMARY)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    return panel


def folder_mockup():
    tab = Table(
        [
            [
                Paragraph(
                    "Automation One",
                    ParagraphStyle("tab", fontName=FONT_SUB, fontSize=7, textColor=hex_color("#ffffff")),
                )
            ]
        ],
        colWidths=[1.35 * inch],
    )
    tab.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), hex_color("#1f5cf5")), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    body = Table(
        [[lockup_stacked_fitted(3.35 * inch, 2.55 * inch, padding=0.18 * inch, **LOCKUP_KW_PRIMARY)]],
        colWidths=[3.35 * inch],
        rowHeights=[2.55 * inch],
    )
    body.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), hex_color("#ffffff")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 1, hex_color("#b3ccff")),
            ]
        )
    )
    wrap = Table([[tab], [body]], colWidths=[SAFE_W])
    wrap.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "LEFT"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return wrap


def letterhead_mockup(lockup_h=0.6 * inch):
    st = brand_styles()
    meta = ParagraphStyle("lhMeta", fontName=FONT_BODY, fontSize=7.5, textColor=hex_color("#7ea7ff"))
    header = Table(
        [
            [lockup_horizontal_fitted(SAFE_W, lockup_h, padding=0.06 * inch, gap_pt=8, **LOCKUP_KW_PRIMARY)],
            [Paragraph("Metro Vancouver · Est. 1981", meta)],
        ],
        colWidths=[SAFE_W],
        rowHeights=[lockup_h + 0.04 * inch, 0.24 * inch],
    )
    header.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "LEFT"), ("VALIGN", (0, 0), (0, 0), "MIDDLE"), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    rule = Table([[""]], colWidths=[SAFE_W], rowHeights=[3])
    rule.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 1.5, hex_color("#1f5cf5"))]))
    body_lines = Table(
        [[Paragraph("Letter content area", ParagraphStyle("lhBody", parent=st["caption"], fontSize=9, textColor=hex_color("#b3ccff"), alignment=TA_LEFT))]],
        colWidths=[SAFE_W],
        rowHeights=[2.35 * inch],
    )
    sheet = Table([[header], [rule], [body_lines]], colWidths=[SAFE_W])
    sheet.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), hex_color("#ffffff")),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return sheet


def email_signature_mockup():
    """Approved email signature — contact, website, Automation One lockup, dealer bar."""
    st = brand_styles()
    sig_w = SAFE_W * 0.9
    lockup_h = 0.48 * inch
    dealer_scale = 0.58

    name_st = ParagraphStyle(
        "sigName", fontName=FONT_NAME, fontSize=11, textColor=hex_color("#0b1330"), spaceAfter=2, leading=13
    )
    role_st = ParagraphStyle(
        "sigRole", fontName=FONT_SUB, fontSize=9, textColor=hex_color("#1547d1"), spaceAfter=3, leading=11
    )
    line_st = ParagraphStyle(
        "sigLine", fontName=FONT_BOOK, fontSize=8.5, textColor=hex_color("#1a2347"), leading=12, spaceAfter=1
    )

    contact = Table(
        [
            [Paragraph("First Last", name_st)],
            [Paragraph("Title · Automation One Business Systems", role_st)],
            [Paragraph("604-255-6622", line_st)],
            [Paragraph("first.last@automationone.ca", line_st)],
            [Paragraph("automationone.ca · Metro Vancouver, BC", line_st)],
        ],
        colWidths=[sig_w],
    )
    contact.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))

    lockup = lockup_horizontal_fitted(sig_w, lockup_h, padding=0.08 * inch, gap_pt=8, **LOCKUP_KW_PRIMARY)
    rows = [[contact], [lockup]]
    if os.path.isfile(AUTHORIZED_DEALER_IMG):
        try:
            from PIL import Image

            iw, ih = Image.open(AUTHORIZED_DEALER_IMG).size
            dealer_w = sig_w * dealer_scale
            dealer_h = dealer_w * (ih / iw)
            dealer_img = RLImage(AUTHORIZED_DEALER_IMG, width=dealer_w, height=dealer_h)
            dealer_wrap = Table([[dealer_img]], colWidths=[dealer_w])
            dealer_wrap.setStyle(
                TableStyle(
                    [
                        ("TOPPADDING", (0, 0), (-1, -1), 14),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ]
                )
            )
            rows.append([dealer_wrap])
        except Exception:
            rows.append(
                [
                    Paragraph(
                        "Authorized dealer — Canon · IDEAL.MBM · Lexmark · FP · Xerox",
                        st["caption"],
                    )
                ]
            )

    sig = Table(rows, colWidths=[sig_w])
    sig.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 1), (0, 1), 12),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]
        )
    )

    frame = Table([[sig]], colWidths=[SAFE_W])
    frame.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), hex_color("#ffffff")),
                ("BOX", (0, 0), (-1, -1), 0.5, hex_color("#d9e6ff")),
                ("TOPPADDING", (0, 0), (-1, -1), 18),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
                ("LEFTPADDING", (0, 0), (-1, -1), 20),
                ("RIGHTPADDING", (0, 0), (-1, -1), 20),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]
        )
    )
    return frame


def vehicle_magnet_mockup():
    t = Table(
        [[lockup_horizontal_fitted(SAFE_W * 0.72, 1.0 * inch, padding=0.1 * inch, gap_pt=8, **LOCKUP_KW_PRIMARY)]],
        colWidths=[SAFE_W],
        rowHeights=[1.1 * inch],
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), hex_color("#ffffff")),
                ("BOX", (0, 0), (-1, -1), 2, hex_color("#1f5cf5")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    return t


def build_pdf():
    register_fonts()
    ensure_tinted_logo(BRAND_BLUE)
    mins = layout_minimums()
    global SPEC_PAIR_H, SPEC_PAIR_W, ALT_GROUP_W  # noqa: PLW0603
    SPEC_PAIR_H = mins["spec_pair_h"]
    SPEC_PAIR_W = mins["spec_pair_w"]
    ALT_GROUP_W = mins["alt_group_w"]
    alt_variant_h = mins["alt_variant_h"]
    biz_lockup_h = mins["biz_lockup_h"]
    letter_lockup_h = mins["letter_lockup_h"]
    horiz_primary_h = mins["horiz_primary_h"]

    doc = SimpleDocTemplate(
        OUTPUT_SITE,
        pagesize=letter,
        rightMargin=PAGE_MARGIN,
        leftMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN,
        bottomMargin=PAGE_MARGIN,
        title="Automation One Brand Guidelines",
    )
    sync_frame(doc)
    st = brand_styles()
    h2, h3, body, caption = st["h2"], st["h3"], st["body"], st["caption"]
    story = []

    story.append(CoverPageSpacer())
    story.append(PageBreak())

    story.extend(section_band(None, "Contents"))
    story.append(table_of_contents())
    story.append(PageBreak())

    story.extend(section_band("1", "Brand overview", "Identity standards for every touchpoint."))
    story.append(brand_principles_row())
    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            "<b>Automation One Business Systems</b> has served Metro Vancouver since 1981. "
            "The visual system is intentionally restrained: a single blue palette, one type family, "
            "and lockups engineered for print, signage, and digital at any scale.",
            body,
        )
    )
    story.append(PageBreak())

    story.extend(section_band("2", "Logo &amp; lockups", "Primary, secondary, and alternate treatments."))
    story.append(
        Paragraph(
            "Lockup width equals the width of “Automation One.” When stacked, the mark matches that width. "
            "“Business Systems” aligns with <b>B</b> under <b>m</b>; subline size is ~53.5% of the name. "
            f"Maintain at least <b>{pt_to_mm(MARK_TEXT_GAP_MIN):.0f} mm</b> between mark and wordmark.",
            body,
        )
    )
    story.append(approval_tier_table())
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Approved Primary", h3))
    story.append(
        Paragraph(
            "<b>Blue 500 (#1F5CF5) on white.</b> Default lockup for all materials on light backgrounds. "
            "Dashed outline = <b>5 mm</b> minimum clear space.",
            body,
        )
    )
    story.append(lockup_primary_blue_panel())
    story.append(Spacer(1, 0.12 * inch))
    story.append(lockup_pair_table(SPEC_PAIR_W, SPEC_PAIR_H, SPEC_PAIR_PAD, "#ffffff", LOCKUP_KW_PRIMARY))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Approved Secondary", h3))
    story.append(
        Paragraph(
            "<b>White on Blue 500 (#1F5CF5).</b> Use only when the background is the same brand blue as the "
            "primary logo colour — not lighter tints, not darker blues.",
            body,
        )
    )
    story.append(
        lockup_pair_table(SPEC_PAIR_W, SPEC_PAIR_H, SPEC_PAIR_PAD, BLUE_PRIMARY, LOCKUP_KW_SECONDARY, border_hex="#1547d1")
    )
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Approved Alternate", h3))
    story.append(
        Paragraph(
            "Use only when Approved Primary or Secondary cannot be applied. "
            f"<b>Blue 800 pair:</b> dark blue on white and white on Blue 800 ({BLUE_DARK.upper()}). "
            "<b>Monochrome pair:</b> black on white and white on black.",
            body,
        )
    )
    story.append(alternate_lockups_grid(ALT_GROUP_W, alt_variant_h))
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Minimum size &amp; clear space", h3))
    story.append(
        Paragraph(
            "Never set the name or mark smaller than the minimums below. Every lockup shown in §2–§5 "
            f"is rendered at <b>{MIN_NAME_PT} pt</b> name size or larger. Keep at least <b>5 mm</b> clear space "
            f"around the full lockup and at least <b>{pt_to_mm(MARK_TEXT_GAP_MIN):.0f} mm</b> between the mark and the wordmark.",
            body,
        )
    )
    story.append(minimum_size_example_panel())
    story.append(Spacer(1, 0.12 * inch))
    story.append(minimum_size_specs_table())
    story.append(Spacer(1, 0.12 * inch))
    story.append(
        Paragraph(
            "Application mockups are scaled to fit each format; clear space is still required in final production files.",
            caption,
        )
    )
    story.append(PageBreak())

    story.append(Paragraph("Mark asset", h3))
    story.append(
        Paragraph(
            "Source: ao-nav-logo.png · Primary: #1F5CF5 · Secondary: white on Blue 500 · "
            "Alternate: black, Blue 800, or white per field.",
            caption,
        )
    )
    if os.path.isfile(LOGO_BLUE_CACHE):
        story.append(logo_img(1.5 * inch, tint=BRAND_BLUE))
    story.append(PageBreak())

    story.extend(section_band("3", "Colour system", "Blue 500 is the anchor. Ink tones support type on light fields."))
    story.append(swatch_grid())
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Digital gradients (blue only)", h3))
    for label, stops in GRADIENTS:
        story.append(Paragraph(label, caption))
        story.append(gradient_strip(stops))
        story.append(Spacer(1, 0.08 * inch))
    story.append(PageBreak())

    story.extend(section_band("4", "Typography", "Sequel Sans Display — the only approved family."))
    embed_note = (
        "All typography in this document uses embedded Sequel Sans Display (Book, Medium, Semi, and Regular) "
        "from the approved <i>fonts/</i> library."
        if FONT_NAME.startswith("Sequel")
        else "Warning: Sequel Sans files missing — rebuild after adding approved fonts to <i>fonts/</i>."
    )
    story.append(
        Paragraph(
            "Use Sequel Sans Display across brand and product UI. Inter and Montserrat are web fallbacks only — "
            "never Arial, Roboto, or system substitutes in brand materials.",
            body,
        )
    )
    story.append(approved_fonts_section())
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(embed_note, caption))
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph("Type samples", h3))
    sample_st = ParagraphStyle(
        "fontSample",
        fontName=FONT_NAME,
        fontSize=22,
        leading=26,
        textColor=hex_color("#0b1330"),
        spaceAfter=6,
    )
    story.append(Paragraph("Automation One", sample_st))
    story.append(
        Paragraph(
            "Business Systems",
            ParagraphStyle("fontSub", fontName=FONT_SUB, fontSize=11, textColor=hex_color("#1547d1"), spaceAfter=8),
        )
    )
    story.append(
        Paragraph(
            "Business solutions made simple.",
            ParagraphStyle("fontBody", fontName=FONT_BOOK, fontSize=11, leading=16, textColor=hex_color("#1a2347")),
        )
    )
    story.append(PageBreak())

    story.extend(section_band("5", "Applications", "Production-ready mockups at or above minimum size."))

    story.extend(
        mockup_panel(
            "Approved email signature",
            email_signature_mockup(),
            "Contact block · website · Approved Primary lockup · authorized dealer bar (58% width). "
            "Do not alter partner logos.",
        )
    )
    story.extend(
        mockup_panel(
            "Business cards (3.5″ × 2″)",
            business_card_mockup(biz_lockup_h),
            "Approved Primary — front (≥ minimum size) · Blue 500 back",
        )
    )
    story.extend(mockup_panel("Exterior signage", signage_mockup(), "Approved Secondary — white on Blue 500"))
    story.extend(mockup_panel("Presentation pocket folder", folder_mockup(), "Approved Primary — stacked on white"))
    story.extend(
        mockup_panel(
            "Letterhead",
            letterhead_mockup(letter_lockup_h),
            "Approved Primary — horizontal on white (≥ minimum size)",
        )
    )
    story.extend(mockup_panel("Vehicle magnet / decal", vehicle_magnet_mockup(), "Approved Primary — horizontal on white"))

    story.append(PageBreak())
    story.extend(section_band("6", "Usage standards"))
    dos = [
        "Use Approved Primary (#1F5CF5 on white) whenever possible",
        "Secondary (white on Blue 500) only on that exact blue field",
        "Alternate only when Primary/Secondary cannot be used",
        f"Lockup width = “Automation One” width; B under m; 5 mm clear / {pt_to_mm(MARK_TEXT_GAP_MIN):.0f} mm mark gap",
    ]
    donts = [
        "Do not use Secondary on any blue except Blue 500 (#1F5CF5)",
        "Do not use Alternate when Primary or Secondary fits",
        "No green, pink, or off-palette accents; do not stretch the mark",
        "Do not break “Automation One” across lines or misalign the subline",
    ]
    do_hdr = ParagraphStyle("doHdr", fontName=FONT_NAME, fontSize=11, textColor=hex_color("#ffffff"))
    dt = Table(
        [
            [Paragraph("Do", do_hdr), Paragraph("Don’t", do_hdr)],
            [Paragraph("<br/>".join("• " + x for x in dos), body), Paragraph("<br/>".join("• " + x for x in donts), body)],
        ],
        colWidths=[SAFE_W / 2.0, SAFE_W / 2.0],
    )
    dt.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, 0), hex_color("#0a2870")),
                ("BACKGROUND", (1, 0), (1, 0), hex_color("#1547d1")),
                ("BACKGROUND", (0, 1), (0, 1), hex_color("#f8faff")),
                ("BACKGROUND", (1, 1), (1, 1), hex_color("#ffffff")),
                ("TOPPADDING", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ("TOPPADDING", (0, 1), (-1, 1), 14),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 14),
                ("BOX", (0, 0), (-1, -1), 0.5, hex_color("#d9e6ff")),
            ]
        )
    )
    story.append(dt)
    story.append(Spacer(1, 0.35 * inch))
    story.append(
        Paragraph(
            f"Automation One Business Systems · Brand Guidelines · Version {DOC_VERSION} · May 2026",
            ParagraphStyle("end", parent=caption, alignment=TA_CENTER, textColor=hex_color("#7ea7ff")),
        )
    )

    doc.build(story, onFirstPage=draw_premium_cover, onLaterPages=draw_page_chrome)
    shutil.copy2(OUTPUT_SITE, OUTPUT_DL)
    print("Wrote:", OUTPUT_SITE)
    print("Copied:", OUTPUT_DL)


def draw_faded_mark(c, x, y, width_pt, tint="#ffffff", opacity=0.18):
    """Mark only (no wordmark), tinted and faded for cover panel."""
    if not os.path.isfile(LOGO_MARK):
        return
    mark_h = width_pt * MARK_RATIO
    path = ensure_tinted_logo(tint)
    try:
        from PIL import Image

        im = Image.open(path).convert("RGBA")
        px = []
        for r, g, b, a in im.getdata():
            if a > 8:
                px.append((r, g, b, int(a * opacity)))
            else:
                px.append((0, 0, 0, 0))
        im.putdata(px)
        cache = os.path.join(BASE, f"ao-cover-mark-fade-{int(opacity * 100)}.png")
        im.save(cache)
        path = cache
    except Exception:
        pass
    c.drawImage(ImageReader(path), x, y, width=width_pt, height=mark_h, mask="auto")


def _cover_spaced_caps(c, x, y, text, font, size, color, tracking=3.2):
    """Draw uppercase label with manual letter-spacing."""
    c.setFont(font, size)
    c.setFillColor(color)
    cx = x
    for ch in text:
        c.drawString(cx, y, ch)
        cx += pdfmetrics.stringWidth(ch, font, size) + tracking


def draw_premium_cover(c, doc):
    """Full-bleed editorial cover — lockup only (no duplicate wordmark type)."""
    register_fonts()
    w, h = letter
    ink = hex_color("#0b1330")
    c.saveState()

    # Paper field + soft wash
    c.setFillColor(hex_color("#f8faff"))
    c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setFillColor(hex_color("#eef4ff"))
    c.circle(w * 0.22, h * 0.78, 2.4 * inch, fill=1, stroke=0)
    c.setFillColor(hex_color("#f8faff"))
    c.circle(w * 0.18, h * 0.22, 1.1 * inch, fill=1, stroke=0)

    panel_x = w * 0.54
    # Blue panel with stepped gradient
    steps = [
        ("#061a4a", 0.0),
        ("#0a2870", 0.22),
        ("#1547d1", 0.55),
        ("#1f5cf5", 1.0),
    ]
    panel_w = w - panel_x
    band_h = h / len(steps)
    for i, (hex_c, _) in enumerate(steps):
        c.setFillColor(hex_color(hex_c))
        c.rect(panel_x, i * band_h, panel_w, band_h + 1, fill=1, stroke=0)

    # Fine rules on paper side
    c.setStrokeColor(hex_color("#d9e6ff"))
    c.setLineWidth(0.5)
    c.line(PAGE_MARGIN, h * 0.28, panel_x - 0.35 * inch, h * 0.28)
    c.setStrokeColor(hex_color(BRAND_BLUE))
    c.setLineWidth(2)
    c.line(PAGE_MARGIN, h * 0.28, PAGE_MARGIN + 1.15 * inch, h * 0.28)

    # Primary lockup — compact on the left
    lockup_pt = 24
    _, lock_h = lockup_dimensions_pt(lockup_pt, horizontal=False)
    lock_y = h * 0.62
    lockup = AoStackedLockupFlowable(lockup_pt, **LOCKUP_KW_PRIMARY)
    lockup.drawOn(c, PAGE_MARGIN, lock_y)

    # Kicker + title block (below lockup)
    text_y = lock_y - 0.28 * inch
    _cover_spaced_caps(c, PAGE_MARGIN, text_y, "BRAND GUIDELINES", FONT_NAME, 8, hex_color("#1f5cf5"), tracking=4)

    c.setFont(FONT_BODY, 8)
    c.setFillColor(hex_color("#7ea7ff"))
    c.drawString(PAGE_MARGIN, text_y - 0.2 * inch, "Metro Vancouver · Est. 1981")

    # Black identity line — lower on page
    c.setFont(FONT_BOOK, 10.5)
    c.setFillColor(ink)
    c.drawString(PAGE_MARGIN, h * 0.22, "Identity standards for print, signage, and digital")

    # Large faded mark only on blue panel (no wordmark)
    mark_w = min(panel_w * 0.94, 4.5 * inch)
    mark_h = mark_w * MARK_RATIO
    mark_x = panel_x + (panel_w - mark_w) / 2
    mark_y = (h - mark_h) / 2
    draw_faded_mark(c, mark_x, mark_y, mark_w, tint="#ffffff", opacity=0.2)

    # Footer rule + meta
    c.setStrokeColor(hex_color("#d9e6ff"))
    c.setLineWidth(0.5)
    c.line(PAGE_MARGIN, 0.72 * inch, w - PAGE_MARGIN, 0.72 * inch)
    c.setFont(FONT_BODY, 8)
    c.setFillColor(hex_color("#7ea7ff"))
    c.drawString(PAGE_MARGIN, 0.52 * inch, f"Version {DOC_VERSION} · May 2026 · Confidential")
    c.drawRightString(w - PAGE_MARGIN, 0.52 * inch, "automationone.ca")
    c.restoreState()


def draw_page_chrome(c, doc):
    """Header rule + footer on content pages (not cover)."""
    register_fonts()
    w, h = letter
    if c.getPageNumber() <= 1:
        return
    c.saveState()
    c.setStrokeColor(hex_color("#d9e6ff"))
    c.setLineWidth(0.5)
    c.line(PAGE_MARGIN, h - PAGE_MARGIN + 6, w - PAGE_MARGIN, h - PAGE_MARGIN + 6)
    c.setFont(FONT_BODY, 8)
    c.setFillColor(hex_color("#7ea7ff"))
    c.drawString(PAGE_MARGIN, 0.48 * inch, "Automation One · Brand Guidelines")
    c.drawRightString(w - PAGE_MARGIN, 0.48 * inch, str(c.getPageNumber()))
    c.restoreState()


if __name__ == "__main__":
    sys.path.insert(0, os.path.join(BASE, ".pydeps"))
    build_pdf()
