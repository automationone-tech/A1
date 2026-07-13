#!/usr/bin/env python3
"""Apply short public URLs: netlify.toml, internal links, sitemap, SEO canonicals."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from url_paths import ROOT, CATEGORY_PATHS, build_path_map

HEADERS_BLOCK = """
[[headers]]
  for = "/*.html"
  [headers.values]
    Cache-Control = "public, max-age=0, must-revalidate"

[[headers]]
  for = "/fonts/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/*.{png,jpg,jpeg,webp,svg,woff2,mp4,MP4}"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
"""

# Existing aliases (keep)
EXTRA_REWRITES = [
    ("/service-support", "/automation-one-service-support.html"),
    ("/francotyp-postalia", "/automation-one-fp.html"),
]

# Legacy paths -> current canonical short URLs
WP_LEGACY_301 = [
    ("/faq", "/faqs"),
    ("/faq/", "/faqs"),
    ("/what-we-do", "/what-we-do-for-you"),
    ("/what-we-do/", "/what-we-do-for-you"),
    ("/latest-news", "/news"),
    ("/latest-news/", "/news"),
    ("/latest-news/canon", "/news/canon"),
    ("/latest-news/canon/", "/news/canon"),
    ("/latest-news/xerox", "/news/xerox"),
    ("/latest-news/xerox/", "/news/xerox"),
    ("/latest-news/lexmark", "/news/lexmark"),
    ("/latest-news/lexmark/", "/news/lexmark"),
    ("/latest-news/fp", "/news/fp"),
    ("/latest-news/fp/", "/news/fp"),
    ("/latest-news/ideal-mbm", "/news/ideal-mbm"),
    ("/latest-news/ideal-mbm/", "/news/ideal-mbm"),
    ("/latest-news/industry", "/news/industry"),
    ("/latest-news/industry/", "/news/industry"),
    ("/digital-solutions", "/solutions"),
    ("/digital-solutions/", "/solutions"),
    ("/idealmbm", "/ideal-mbm"),
    ("/idealmbm/", "/ideal-mbm"),
    ("/ideal.mbm", "/ideal-mbm"),
    ("/ideal.mbm/", "/ideal-mbm"),
]

# Old query-string catalog links -> category pretty paths
CATEGORY_LINK_REPLACEMENTS = [
    ("automation-one-products.html?category=office-printers#catalog", "/office-printers"),
    ("automation-one-products.html?category=multifunction#catalog", "/multifunction-printers"),
    ("automation-one-products.html?category=production#catalog", "/production-printers"),
    ("automation-one-products.html?category=large-format#catalog", "/wide-format-printers"),
    ("automation-one-products.html?category=mailing#catalog", "/mailing-machines"),
    ("automation-one-products.html?category=document-management#catalog", "/document-scanners"),
    ("automation-one-products.html?category=more#catalog", "/products#catalog"),
    ("/automation-one-products.html?category=office-printers#catalog", "/office-printers"),
    ("/automation-one-products.html?category=multifunction#catalog", "/multifunction-printers"),
    ("/automation-one-products.html?category=production#catalog", "/production-printers"),
    ("/automation-one-products.html?category=large-format#catalog", "/wide-format-printers"),
    ("/automation-one-products.html?category=mailing#catalog", "/mailing-machines"),
    ("/automation-one-products.html?category=document-management#catalog", "/document-scanners"),
    ("/automation-one-products.html?category=more#catalog", "/products#catalog"),
    ("/products?category=office-printers#catalog", "/office-printers"),
    ("/products?category=multifunction#catalog", "/multifunction-printers"),
    ("/products?category=production#catalog", "/production-printers"),
    ("/products?category=large-format#catalog", "/wide-format-printers"),
    ("/products?category=mailing#catalog", "/mailing-machines"),
    ("/products?category=document-management#catalog", "/document-scanners"),
    ("/products?category=more#catalog", "/products#catalog"),
]


def write_netlify_toml(path_map: dict[str, str]) -> None:
    lines = [
        "[build]",
        '  publish = "."',
        "",
        "# --- Short URL rewrites (200) -> physical HTML files ---",
    ]

    # Product + utility pages: sort by path length descending (more specific first)
    product_entries = [
        (path, fname)
        for fname, path in path_map.items()
        if path.count("/") >= 2
    ]
    product_entries.sort(key=lambda x: -len(x[0]))

    for public_path, filename in product_entries:
        lines += [
            "",
            "[[redirects]]",
            f'  from = "{public_path}"',
            f'  to = "/{filename}"',
            "  status = 200",
        ]

    lines.append("")
    lines.append("# --- Main section pretty URLs (200) ---")
    main_entries = [
        (path, fname)
        for fname, path in sorted(path_map.items())
        if fname in path_map and path.count("/") == 1 and path != "/"
    ]
    for public_path, filename in main_entries:
        lines += [
            "",
            "[[redirects]]",
            f'  from = "{public_path}"',
            f'  to = "/{filename}"',
            "  status = 200",
        ]
        lines += [
            "",
            "[[redirects]]",
            f'  from = "{public_path}/"',
            f'  to = "{public_path}"',
            "  status = 301",
            "  force = true",
        ]

    for alias_from, alias_to in EXTRA_REWRITES:
        lines += [
            "",
            "[[redirects]]",
            f'  from = "{alias_from}"',
            f'  to = "{alias_to}"',
            "  status = 200",
        ]

    lines.append("")
    lines.append("# --- Catalog category pretty URLs (200) -> products page ---")
    for public_path in sorted(CATEGORY_PATHS.keys(), key=len, reverse=True):
        lines += [
            "",
            "[[redirects]]",
            f'  from = "{public_path}"',
            '  to = "/automation-one-products.html"',
            "  status = 200",
        ]
        lines += [
            "",
            "[[redirects]]",
            f'  from = "{public_path}/"',
            f'  to = "{public_path}"',
            "  status = 301",
            "  force = true",
        ]

    lines.append("")
    lines.append("# --- Legacy long .html paths (301) -> short public URLs ---")
    legacy = sorted(path_map.items(), key=lambda x: -len(x[0]))
    for filename, public_path in legacy:
        lines += [
            "",
            "[[redirects]]",
            f'  from = "/{filename}"',
            f'  to = "{public_path}"',
            "  status = 301",
            "  force = true",
        ]
        if public_path.count("/") >= 2:
            lines += [
                "",
                "[[redirects]]",
                f'  from = "{public_path}/"',
                f'  to = "{public_path}"',
                "  status = 301",
                "  force = true",
            ]

    lines.append("")
    lines.append("# --- WordPress slug legacy (301) for .ca cutover ---")
    for old, new in WP_LEGACY_301:
        lines += [
            "",
            "[[redirects]]",
            f'  from = "{old}"',
            f'  to = "{new}"',
            "  status = 301",
        ]

    lines += [
        "",
        "# Duplicate homepage variant",
        "",
        "[[redirects]]",
        '  from = "/automation-one-homepage-6.html"',
        '  to = "/"',
        "  status = 301",
        "  force = true",
        "",
        "[[redirects]]",
        '  from = "/index.html"',
        '  to = "/"',
        "  status = 301",
        "  force = true",
    ]

    lines.append(HEADERS_BLOCK.strip())
    (ROOT / "netlify.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote netlify.toml ({len(path_map)} short paths + legacy 301s)")


def replace_internal_links(path_map: dict[str, str], use_pretty_paths: bool = False) -> int:
    """Replace href targets with physical .html files (local-safe) or pretty paths (Netlify)."""
    # Longest filenames first to avoid partial replacements
    file_to_path = sorted(path_map.items(), key=lambda x: -len(x[0]))
    legacy_home = [
        ("automation-one-homepage-6.html", "/"),
        ("index.html", "/"),
    ]

    def sub_href(match: re.Match) -> str:
        quote = match.group(1)
        base = match.group(2)
        suffix = match.group(3) or ""
        new = None
        for fname, p in file_to_path:
            if base == fname:
                new = p
                break
        if new is None:
            for fname, p in legacy_home:
                if base == fname:
                    new = p
                    break
        if new is None:
            return match.group(0)
        dest = new if use_pretty_paths else base
        return f"href={quote}{dest}{suffix}{quote}"

    # Also rewrite pretty paths back to .html when fixing local preview
    pretty_to_file = {p: f for f, p in path_map.items() if p != "/"}
    pretty_sorted = sorted(pretty_to_file.items(), key=lambda x: -len(x[0]))

    def sub_pretty_href(match: re.Match) -> str:
        quote = match.group(1)
        path = match.group(2)
        suffix = match.group(3) or ""
        for pretty, fname in pretty_sorted:
            if path == pretty:
                dest = f"/{fname}" if use_pretty_paths else fname
                return f"href={quote}{dest}{suffix}{quote}"
        return match.group(0)

    pattern = re.compile(
        r'href=(["\'])([^"\']+\.html)((?:\?[^"\']*)?(?:#[^"\']*)?)\1',
        re.I,
    )
    pretty_pattern = re.compile(
        r'href=(["\'])(/[^"\']+?)((?:\?[^"\']*)?(?:#[^"\']*)?)\1',
        re.I,
    )
    changed = 0
    for html_path in sorted(ROOT.glob("*.html")):
        text = html_path.read_text(encoding="utf-8")
        new_text = pattern.sub(sub_href, text)
        if not use_pretty_paths:
            new_text = pretty_pattern.sub(sub_pretty_href, new_text)
        if new_text != text:
            html_path.write_text(new_text, encoding="utf-8")
            changed += 1
            print(f"  links: {html_path.name}")
    return changed


def write_redirects_file(path_map: dict[str, str]) -> None:
    """Netlify _redirects mirror (200 rewrites + 301 legacy .html)."""
    lines: list[str] = []
    for public_path in sorted(CATEGORY_PATHS.keys(), key=len, reverse=True):
        lines.append(f"{public_path}  /automation-one-products.html  200")
        lines.append(f"{public_path}/  {public_path}  301!")
    for filename, public_path in sorted(path_map.items(), key=lambda x: -len(x[1])):
        if public_path == "/":
            continue
        lines.append(f"{public_path}  /{filename}  200")
        # Trailing slash breaks relative img/src paths; send to canonical short URL.
        lines.append(f"{public_path}/  {public_path}  301!")
    for filename, public_path in sorted(path_map.items(), key=lambda x: -len(x[0])):
        if public_path == "/":
            continue
        lines.append(f"/{filename}  {public_path}  301!")
    lines.extend(
        [
            "/automation-one-homepage-6.html  /  301!",
            "/index.html  /  301!",
        ]
    )
    for old, new in WP_LEGACY_301:
        lines.append(f"{old}  {new}  301")
    (ROOT / "_redirects").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote _redirects ({len(lines)} rules)")


def _remove_local_path_stub(link_path: Path) -> None:
    """Remove old directory/index.html or symlink file at pretty URL path."""
    if not link_path.exists() and not link_path.is_symlink():
        return
    if link_path.is_dir():
        index = link_path / "index.html"
        if index.is_symlink():
            index.unlink()
        try:
            link_path.rmdir()
        except OSError:
            pass
    elif link_path.is_symlink() or link_path.is_file():
        link_path.unlink()


def setup_local_symlinks(path_map: dict[str, str]) -> int:
    """Extensionless file symlinks (no trailing slash) for local http.server."""
    created = 0
    skip_paths = {"/printer-bash"}  # root file printer-bash already serves this path
    for filename, public_path in sorted(path_map.items(), key=lambda x: -len(x[1])):
        if public_path in ("/",) or public_path in skip_paths:
            continue
        target = ROOT / filename
        if not target.is_file():
            continue
        link_path = ROOT / public_path.strip("/")
        _remove_local_path_stub(link_path)
        link_path.parent.mkdir(parents=True, exist_ok=True)
        rel_target = os.path.relpath(target, link_path.parent)
        if link_path.is_symlink():
            if link_path.resolve() == target.resolve():
                continue
            link_path.unlink()
        elif link_path.exists():
            continue
        link_path.symlink_to(rel_target)
        created += 1
    print(f"Created/updated {created} local path symlinks (extensionless files)")
    return created


def replace_category_links() -> int:
    changed = 0
    for html_path in sorted(ROOT.glob("*.html")):
        text = html_path.read_text(encoding="utf-8")
        new_text = text
        for old, new in CATEGORY_LINK_REPLACEMENTS:
            new_text = new_text.replace(f'href="{old}"', f'href="{new}"')
            new_text = new_text.replace(f"href='{old}'", f"href='{new}'")
        if new_text != text:
            html_path.write_text(new_text, encoding="utf-8")
            changed += 1
            print(f"  category links: {html_path.name}")
    return changed


def fix_sticky_nav_service_path() -> int:
    """Recognize pretty URLs in sticky bar current-page logic."""
    replacements = [
        (
            "file.indexOf('service-support') !== -1 || file.indexOf('toner') !== -1 "
            "|| file.indexOf('resources') !== -1 || file.indexOf('products') !== -1",
            "file === 'service' || file.indexOf('service-support') !== -1 "
            "|| file.indexOf('toner') !== -1 || file.indexOf('resources') !== -1 "
            "|| file.indexOf('products') !== -1",
        ),
        (
            "file.indexOf('about') !== -1 || file.indexOf('what-we-do') !== -1 "
            "|| file.indexOf('testimonials') !== -1 || file.indexOf('latest-news') !== -1 "
            "|| file.indexOf('faq') !== -1 || file.indexOf('contact') !== -1",
            "file.indexOf('about') !== -1 || file.indexOf('what-we-do') !== -1 "
            "|| file.indexOf('testimonials') !== -1 || file.indexOf('news') !== -1 "
            "|| file.indexOf('faqs') !== -1 || file.indexOf('faq') !== -1 "
            "|| file.indexOf('contact') !== -1",
        ),
        (
            "file.indexOf('digital-solutions') !== -1",
            "file.indexOf('solutions') !== -1 || file.indexOf('digital-solutions') !== -1",
        ),
    ]
    changed = 0
    for html_path in sorted(ROOT.glob("*.html")):
        text = html_path.read_text(encoding="utf-8")
        new_text = text
        for old, new in replacements:
            new_text = new_text.replace(old, new)
        if new_text != text:
            html_path.write_text(new_text, encoding="utf-8")
            changed += 1
            print(f"  nav: {html_path.name}")
    return changed


def main() -> int:
    path_map = build_path_map()
    print(f"Public paths: {len(path_map)}")
    write_netlify_toml(path_map)
    write_redirects_file(path_map)
    setup_local_symlinks(path_map)
    n = replace_internal_links(path_map, use_pretty_paths=True)
    print(f"Updated links in {n} HTML files")
    cat_n = replace_category_links()
    print(f"Updated category links in {cat_n} HTML files")
    nav_n = fix_sticky_nav_service_path()
    print(f"Updated sticky nav path checks in {nav_n} HTML files")
    seo_script = ROOT / "scripts" / "apply-seo-fixes.py"
    r = subprocess.run([sys.executable, str(seo_script)], cwd=str(ROOT))
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
