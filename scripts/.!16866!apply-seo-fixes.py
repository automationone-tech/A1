#!/usr/bin/env python3
"""Apply SEO/AEO fixes across Automation One static site (idempotent)."""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://automationone.org"
OG_IMAGE = f"{SITE}/og-image.png"
SEO_MARKER_START = "<!-- ao-seo-start -->"
SEO_MARKER_END = "<!-- ao-seo-end -->"

HOME_DESC = (
    "Automation One is Vancouver's authorized dealer for Canon, Lexmark, Xerox and more - "
    "office printers, toner, service and managed print for BC businesses."
)


PRETTY_CANONICAL: dict[str, str] = {
    "index.html": "/",
    "automation-one-about.html": "/about",
    "automation-one-canon.html": "/canon",
    "automation-one-contact.html": "/contact",
    "automation-one-faq.html": "/faq",
    "automation-one-digital-solutions.html": "/digital-solutions",
    "automation-one-fp.html": "/fp",
    "automation-one-ideal-mbm.html": "/ideal-mbm",
    "automation-one-lexmark.html": "/lexmark",
    "automation-one-products.html": "/products",
    "automation-one-resources.html": "/resources",
    "automation-one-service-support.html": "/service",
    "automation-one-testimonials.html": "/testimonials",
    "automation-one-toner.html": "/toner",
    "automation-one-what-we-do.html": "/what-we-do",
    "automation-one-xerox.html": "/xerox",
}

SITEMAP_PRETTY = sorted(set(PRETTY_CANONICAL.values()))

GENERIC_CANON_TITLE = "Canon Products | Authorized Dealer in Vancouver | Automation One"
GENERIC_CANON_DESC_PREFIX = "Explore Canon imageFORCE"

ORG_JSON = {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "name": "Automation One Business Systems Inc.",
    "alternateName": "Automation One",
    "url": SITE,
    "logo": f"{SITE}/ao-nav-logo.png",
    "image": OG_IMAGE,
    "telephone": "+1-604-255-6622",
    "email": "info@automationone.ca",
    "address": [
        {
            "@type": "PostalAddress",
            "streetAddress": "1365 Boundary Rd.",
            "addressLocality": "Vancouver",
            "addressRegion": "BC",
            "postalCode": "V5K 4T9",
            "addressCountry": "CA",
        },
        {
            "@type": "PostalAddress",
            "streetAddress": "1440 Ingleton Ave.",
            "addressLocality": "Burnaby",
            "addressRegion": "BC",
            "postalCode": "V5C 4L7",
            "addressCountry": "CA",
        },
    ],
    "areaServed": {"@type": "AdministrativeArea", "name": "British Columbia"},
    "description": HOME_DESC,
}


def canonical_url(filename: str) -> str:
    path = PRETTY_CANONICAL.get(filename)
    if path:
        return f"{SITE}{path if path != '/' else '/'}"
    return f"{SITE}/{filename}"


def strip_tags(fragment: str) -> str:
    t = re.sub(r"<[^>]+>", "", fragment)
    t = html.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def first_h1_plain(page_html: str) -> str | None:
    m = re.search(r"<h1\b[^>]*>(.*?)</h1>", page_html, re.I | re.S)
    return strip_tags(m.group(1)) if m else None


def get_title(page_html: str) -> str | None:
    m = re.search(r"<title>([^<]+)</title>", page_html, re.I)
    return m.group(1).strip() if m else None


def get_description(page_html: str) -> str | None:
    m = re.search(
        r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']',
        page_html,
        re.I,
    )
    return html.unescape(m.group(1).strip()) if m else None


def set_title(page_html: str, title: str) -> str:
    return re.sub(r"<title>[^<]*</title>", f"<title>{html.escape(title)}</title>", page_html, count=1, flags=re.I)


def set_or_insert_description(page_html: str, desc: str) -> str:
    esc = html.escape(desc, quote=True)
    tag = f'<meta name="description" content="{esc}" />'
    if re.search(r'<meta\s+name=["\']description["\']', page_html, re.I):
        return re.sub(
            r'<meta\s+name=["\']description["\']\s+content=["\'][^"\']*["\']\s*/?>',
            tag,
            page_html,
            count=1,
            flags=re.I,
        )
    return re.sub(r"(</title>)", rf"\1\n{tag}", page_html, count=1, flags=re.I)


def remove_seo_block(page_html: str) -> str:
    return re.sub(
        re.escape(SEO_MARKER_START) + r".*?" + re.escape(SEO_MARKER_END) + r"\s*",
        "",
        page_html,
        flags=re.S,
    )


def build_og_twitter(canonical: str, title: str, description: str) -> str:
    t = html.escape(title, quote=True)
    d = html.escape(description, quote=True)
    c = html.escape(canonical, quote=True)
    return f"""{SEO_MARKER_START}
<link rel="canonical" href="{c}" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Automation One" />
<meta property="og:url" content="{c}" />
<meta property="og:title" content="{t}" />
<meta property="og:description" content="{d}" />
<meta property="og:image" content="{OG_IMAGE}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{t}" />
<meta name="twitter:description" content="{d}" />
<meta name="twitter:image" content="{OG_IMAGE}" />
{SEO_MARKER_END}"""


def insert_after_description(page_html: str, block: str) -> str:
    if SEO_MARKER_START in page_html:
        return remove_seo_block(page_html)
    m = re.search(
        r'(<meta\s+name=["\']description["\'][^>]+>)',
        page_html,
        re.I,
    )
    if m:
        return page_html.replace(m.group(1), m.group(1) + "\n" + block, 1)
    m = re.search(r"(</title>)", page_html, re.I)
    if m:
        return page_html.replace(m.group(1), m.group(1) + "\n" + block, 1)
    return page_html


def canon_product_description(name: str) -> str:
    plain = name.rstrip(".")
    return (
        f"{plain} from Automation One, authorized Canon dealer in Vancouver: "
        f"specs, leasing options, and local install and service for BC businesses."
    )[:320]


def fix_canon_product_page(page_html: str, filename: str) -> str:
    title = get_title(page_html) or ""
    desc = get_description(page_html) or ""
    if title != GENERIC_CANON_TITLE and not desc.startswith(GENERIC_CANON_DESC_PREFIX):
        return page_html
    h1 = first_h1_plain(page_html)
    if not h1:
        return page_html
    product = h1.rstrip(".")
    new_title = f"{product} | Automation One Vancouver"
    new_desc = canon_product_description(product)
    page_html = set_title(page_html, new_title)
    page_html = set_or_insert_description(page_html, new_desc)
    return page_html


def extract_faq_entities(page_html: str) -> list[dict]:
    entities = []
    for m in re.finditer(
        r'<details class="faq-item">\s*<summary>(.*?)</summary>\s*<div class="faq-answer">\s*(.*?)</div>\s*</details>',
        page_html,
        re.S | re.I,
    ):
        q = strip_tags(m.group(1))
        a = strip_tags(m.group(2))
        if q and a:
            entities.append(
                {
                    "@type": "Question",
                    "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": a},
                }
            )
    return entities


def build_faq_json_ld(entities: list[dict]) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities,
    }
    return (
        f'\n<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'
    )


def build_org_json_ld() -> str:
    return (
        f'\n<script type="application/ld+json">{json.dumps(ORG_JSON, ensure_ascii=False)}</script>'
    )


def fix_theme_color(page_html: str) -> str:
    return re.sub(
        r'(<meta\s+name=["\']theme-color["\']\s+content=["\'])#1547d1(["\'])',
        r"\1#1f5cf5\2",
        page_html,
        flags=re.I,
    )


def ensure_favicon_head(page_html: str) -> str:
    block = """<link rel="icon" href="favicon.ico" sizes="any" />
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32x32.png" />
<link rel="icon" type="image/png" sizes="16x16" href="favicon-16x16.png" />
<link rel="apple-touch-icon" href="apple-touch-icon.png" />
<link rel="manifest" href="site.webmanifest" />"""
    if 'rel="icon"' in page_html or "rel='icon'" in page_html:
        return page_html
    return re.sub(
        r"(<meta\s+name=[\"']viewport[^>]+>)",
        r"\1\n" + block,
        page_html,
        count=1,
        flags=re.I,
    )


def fix_smash_double_h1(page_html: str) -> str:
    return page_html.replace(
        '<h1 class="smash-intro-title" data-text="PRINTER BASH">PRINTER BASH</h1>',
        '<p class="smash-intro-title" data-text="PRINTER BASH" aria-hidden="true">PRINTER BASH</p>',
        1,
    )


def defer_homepage_script(page_html: str, filename: str) -> str:
    if filename not in ("index.html", "automation-one-homepage-6.html"):
        return page_html
    return re.sub(
        r'<script\s+src="automation-one-homepage-videos\.js"></script>',
        '<script src="automation-one-homepage-videos.js" defer></script>',
        page_html,
        count=1,
    )


def add_lazy_loading_products(page_html: str, filename: str) -> str:
    if filename != "automation-one-products.html":
        return page_html

    def repl(match: re.Match) -> str:
        tag = match.group(0)
        if re.search(r"\bloading\s*=", tag, re.I):
            return tag
        return tag.replace("<img ", '<img loading="lazy" ', 1)

    return re.sub(r"<img\s", repl, page_html)


def add_robots_noindex(page_html: str) -> str:
    tag = '<meta name="robots" content="noindex, follow" />'
    if "noindex" in page_html:
        return page_html
    return re.sub(r"(</title>)", rf"\1\n{tag}", page_html, count=1, flags=re.I)


def process_html(path: Path) -> bool:
    name = path.name
    text = path.read_text(encoding="utf-8")
    original = text

    text = fix_theme_color(text)
    text = ensure_favicon_head(text)

    if name == "automation-one-smash-it.html":
        text = fix_smash_double_h1(text)

    if name.startswith("automation-one-canon-") and name != "automation-one-canon.html":
        text = fix_canon_product_page(text, name)

    if name in ("index.html", "automation-one-homepage-6.html"):
        text = set_or_insert_description(text, HOME_DESC)

    if name == "automation-one-homepage-6.html":
        text = add_robots_noindex(text)

    title = get_title(text) or "Automation One"
    desc = get_description(text) or HOME_DESC
    canonical = canonical_url(name)

    og_block = build_og_twitter(canonical, title, desc)
    text = remove_seo_block(text)
    text = insert_after_description(text, og_block)

    if name in ("index.html", "automation-one-contact.html"):
        text = re.sub(
            r'\n<script type="application/ld\+json">\s*\{[^<]*"@type":\s*"LocalBusiness"[^<]*</script>',
            "",
            text,
        )
        if '"@type": "LocalBusiness"' not in text:
            text = text.replace(SEO_MARKER_END, SEO_MARKER_END + build_org_json_ld(), 1)

    if name == "automation-one-faq.html":
        text = re.sub(
            r'\n<script type="application/ld\+json">\s*\{[^<]*"@type":\s*"FAQPage"[^<]*</script>',
            "",
            text,
        )
        entities = extract_faq_entities(text)
        if entities and '"@type": "FAQPage"' not in text:
            text = text.replace(SEO_MARKER_END, SEO_MARKER_END + build_faq_json_ld(entities), 1)

    text = defer_homepage_script(text, name)
    text = add_lazy_loading_products(text, name)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def write_robots() -> None:
    (ROOT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: https://automationone.org/sitemap.xml\n",
        encoding="utf-8",
    )


def write_llms() -> None:
    lines = [
        "# Automation One (automationone.org)",
        "",
        "Vancouver-based authorized dealer for office printers, MFPs, production print,",
        "postage meters, and managed print. Brands: Canon, Lexmark, Xerox, Francotyp-Postalia, Ideal MBM.",
        "",
        "## Key pages",
        f"- Home: {SITE}/",
        f"- Products: {SITE}/products",
        f"- FAQ: {SITE}/faq",
        f"- Contact: {SITE}/contact",
        f"- Service: {SITE}/service",
        f"- About: {SITE}/about",
        "",
        "## Contact",
        "Phone: 604-255-6622",
        "Email: info@automationone.ca",
        "Vancouver: 1365 Boundary Rd., Vancouver, BC V5K 4T9",
        "Burnaby: 1440 Ingleton Ave., Burnaby, BC V5C 4L7",
        "",
    ]
    (ROOT / "llms.txt").write_text("\n".join(lines), encoding="utf-8")


def write_sitemap() -> None:
    urls: list[str] = []
    for p in sorted(PRETTY_CANONICAL.values()):
        urls.append(f"{SITE}{p if p != '/' else '/'}")
    skip = {"automation-one-homepage-6.html"}
    for path in sorted(ROOT.glob("*.html")):
        if path.name in skip or path.name in PRETTY_CANONICAL:
            continue
        urls.append(f"{SITE}/{path.name}")

    # stable unique order
    seen = set()
    unique = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)

    items = "\n".join(
        f"  <url><loc>{html.escape(u)}</loc></url>" for u in unique
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{items}\n"
        "</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")


def generate_og_image() -> None:
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Pillow not installed; skip og-image.png (use ao-nav-logo in OG tags)", file=sys.stderr)
        return

    out = ROOT / "og-image.png"
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), "#1f5cf5")
    draw = ImageDraw.Draw(img)
    logo_path = ROOT / "ao-nav-logo.png"
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        scale = 280
        ratio = scale / max(logo.size)
        logo = logo.resize((int(logo.size[0] * ratio), int(logo.size[1] * ratio)), Image.Resampling.LANCZOS)
        lx = (w - logo.size[0]) // 2
        ly = 120
        img.paste(logo, (lx, ly), logo)
    draw.text((80, 430), "Automation One", fill="white")
