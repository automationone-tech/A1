#!/usr/bin/env python3
"""Apply short public URLs: netlify.toml, internal links, sitemap, SEO canonicals."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from url_paths import ROOT, build_path_map

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

# WordPress-era paths on automationone.ca (301 when .ca points to Netlify)
WP_LEGACY_301 = [
    ("/faqs", "/faq"),
    ("/faqs/", "/faq"),
    ("/what-we-do-for-you", "/what-we-do"),
    ("/what-we-do-for-you/", "/what-we-do"),
    ("/idealmbm", "/ideal-mbm"),
    ("/idealmbm/", "/ideal-mbm"),
    ("/solutions", "/digital-solutions"),
    ("/solutions/", "/digital-solutions"),
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

    for alias_from, alias_to in EXTRA_REWRITES:
        lines += [
            "",
            "[[redirects]]",
            f'  from = "{alias_from}"',
            f'  to = "{alias_to}"',
            "  status = 200",
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


def replace_internal_links(path_map: dict[str, str]) -> int:
    """Replace href=\"file.html\" with href=\"/short/path\" across all HTML."""
    # Longest filenames first to avoid partial replacements
    file_to_path = sorted(path_map.items(), key=lambda x: -len(x[0]))
    legacy_home = [
        ("automation-one-homepage-6.html", "/"),
        ("index.html", "/"),
    ]

    def sub_href(match: re.Match) -> str:
        quote = match.group(1)
        target = match.group(2)
        fragment = match.group(3) or ""
        new = None
        for fname, p in file_to_path:
            if target == fname:
                new = p
                break
        if new is None:
            for fname, p in legacy_home:
                if target == fname:
                    new = p
                    break
        if new is None:
            return match.group(0)
        return f"href={quote}{new}{fragment}{quote}"

    pattern = re.compile(
        r'href=(["\'])([^"\']+\.html)(#[^"\']*)?\1',
        re.I,
    )
    changed = 0
    for html_path in sorted(ROOT.glob("*.html")):
        text = html_path.read_text(encoding="utf-8")
        new_text = pattern.sub(sub_href, text)
        if new_text != text:
            html_path.write_text(new_text, encoding="utf-8")
            changed += 1
            print(f"  links: {html_path.name}")
    return changed


def main() -> int:
    path_map = build_path_map()
    print(f"Public paths: {len(path_map)}")
    write_netlify_toml(path_map)
    n = replace_internal_links(path_map)
    print(f"Updated links in {n} HTML files")
    seo_script = ROOT / "scripts" / "apply-seo-fixes.py"
    r = subprocess.run([sys.executable, str(seo_script)], cwd=str(ROOT))
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
