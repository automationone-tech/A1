#!/usr/bin/env python3
"""Convert heavy referenced PNG/JPG images to WebP and update HTML references.

Rules:
- Only converts images actually referenced from root *.html files.
- Only converts when the WebP comes out at least 25% smaller.
- Keeps the original file in place (old direct URLs keep working).
- Never rewrites og:image / twitter:image / favicon references (social
  scrapers and some crawlers are unreliable with WebP).
"""
import glob
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

MIN_SIZE = 150_000          # only bother with images >= 150 KB
MIN_SAVING = 0.25           # require at least 25% reduction
QUALITY = 85                # visually lossless for photos/renders

META_LINE = re.compile(r'og:image|twitter:image|rel="icon"|rel="apple-touch-icon"|rel="preload"')

def collect_refs():
    refs = {}
    for f in sorted(glob.glob('*.html')):
        t = open(f, encoding='utf-8', errors='surrogateescape').read()
        for m in re.findall(r'["\'(,\s]/([A-Za-z0-9_./-]+\.(?:png|jpe?g))', t):
            refs.setdefault(m, set()).add(f)
    return refs

def convert(path):
    img = Image.open(path)
    out = os.path.splitext(path)[0] + '.webp'
    if img.mode == 'P':
        img = img.convert('RGBA')
    img.save(out, 'WEBP', quality=QUALITY, method=6)
    return out

def main():
    refs = collect_refs()
    converted = {}   # old rel path -> new rel path
    total_before = total_after = 0
    for rel in sorted(refs):
        if not os.path.exists(rel):
            continue
        size = os.path.getsize(rel)
        if size < MIN_SIZE:
            continue
        try:
            out = convert(rel)
        except Exception as e:
            print(f'SKIP {rel}: {e}', file=sys.stderr)
            continue
        new_size = os.path.getsize(out)
        if new_size > size * (1 - MIN_SAVING):
            os.remove(out)
            continue
        converted[rel] = os.path.splitext(rel)[0] + '.webp'
        total_before += size
        total_after += new_size
        print(f'{size/1e6:6.2f} -> {new_size/1e6:5.2f} MB  {rel}')

    # rewrite references line by line, skipping social-meta / icon lines
    n_pages = n_swaps = 0
    for f in sorted(glob.glob('*.html')):
        lines = open(f, encoding='utf-8', errors='surrogateescape').read().split('\n')
        changed = False
        for i, line in enumerate(lines):
            if META_LINE.search(line):
                continue
            new_line = line
            for old, new in converted.items():
                if '/' + old in new_line:
                    new_line = new_line.replace('/' + old, '/' + new)
            if new_line != line:
                lines[i] = new_line
                changed = True
                n_swaps += 1
        if changed:
            open(f, 'w', encoding='utf-8', errors='surrogateescape').write('\n'.join(lines))
            n_pages += 1

    print(f'\nconverted {len(converted)} images: {total_before/1e6:.1f} MB -> {total_after/1e6:.1f} MB '
          f'(saved {(total_before-total_after)/1e6:.1f} MB)')
    print(f'rewrote {n_swaps} reference lines across {n_pages} pages')


if __name__ == '__main__':
    main()
