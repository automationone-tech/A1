#!/usr/bin/env python3
"""Public URL paths for Automation One static site (filename -> path)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Main section pages (netlify pretty routes)
MAIN_PATHS: dict[str, str] = {
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
    "automation-one-network-installation-survey.html": "/network-survey",
    "automation-one-billable-confirmation.html": "/billable-confirmation",
    "automation-one-smash-it.html": "/printer-bash",
}

PRODUCT_BRANDS = ("canon", "lexmark", "xerox")
PRODUCT_RE = re.compile(
    r"^automation-one-(canon|lexmark|xerox)-(.+)\.html$", re.I
)


def build_path_map() -> dict[str, str]:
    """Map each HTML filename to its public path (starts with /)."""
    paths = dict(MAIN_PATHS)
    for html in ROOT.glob("*.html"):
        name = html.name
        if name in paths or name == "automation-one-homepage-6.html":
            continue
        m = PRODUCT_RE.match(name)
        if m:
            brand, slug = m.group(1).lower(), m.group(2)
            paths[name] = f"/{brand}/{slug}"
    return paths


def path_for_filename(filename: str) -> str | None:
    return build_path_map().get(filename)


def public_url(filename: str, site: str = "https://automationone.org") -> str:
    path = path_for_filename(filename)
    if not path:
        if filename == "automation-one-homepage-6.html":
            return f"{site}/"
        return f"{site}/{filename}"
    return f"{site}{path if path != '/' else '/'}"
