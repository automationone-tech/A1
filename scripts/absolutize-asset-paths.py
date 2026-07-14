#!/usr/bin/env python3
"""Rewrite relative asset/page references in root HTML files to root-absolute.

Pages are served at pretty URLs like /products AND /products/ (Netlify treats
them identically), so relative refs break under the trailing-slash variant.
Root-absolute paths work in both cases.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Schemes/prefixes that must never be touched
SKIP = re.compile(r'^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//|/|#|\?|$)')

ATTR_RE = re.compile(
    r'\b(src|href|poster|data-src|data-bg)=(["\'])(.*?)\2', re.DOTALL)
SRCSET_RE = re.compile(r'\b(srcset)=(["\'])(.*?)\2', re.DOTALL)
CSS_URL_RE = re.compile(r'url\(\s*(["\']?)([^)"\']+)\1\s*\)')


def absolutize(url: str) -> str:
    if SKIP.match(url.strip()):
        return url
    return '/' + url.strip()


def fix_attr(m):
    name, q, val = m.group(1), m.group(2), m.group(3)
    return f'{name}={q}{absolutize(val)}{q}'


def fix_srcset(m):
    name, q, val = m.group(1), m.group(2), m.group(3)
    parts = []
    for cand in val.split(','):
        cand = cand.strip()
        if not cand:
            continue
        bits = cand.split(None, 1)
        url = absolutize(bits[0])
        parts.append(url + (' ' + bits[1] if len(bits) > 1 else ''))
    return f'{name}={q}{", ".join(parts)}{q}'


def fix_css_url(m):
    q, val = m.group(1), m.group(2)
    return f'url({q}{absolutize(val)}{q})'


def main():
    changed_files = 0
    total_subs = 0
    for path in sorted(ROOT.glob('*.html')):
        text = path.read_text(encoding='utf-8', errors='surrogateescape')
        orig = text
        text, n1 = ATTR_RE.subn(fix_attr, text)
        text, n2 = SRCSET_RE.subn(fix_srcset, text)
        text, n3 = CSS_URL_RE.subn(fix_css_url, text)
        if text != orig:
            path.write_text(text, encoding='utf-8', errors='surrogateescape')
            changed_files += 1
            # count only refs actually rewritten
            diff = sum(a != b for a, b in [(orig, text)])
        total_subs += n1 + n2 + n3
    print(f'processed files with changes: {changed_files}')
    print(f'attribute/srcset/css-url matches scanned: {total_subs}')


if __name__ == '__main__':
    sys.exit(main())
