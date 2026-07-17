#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local dev server with Netlify _redirects support for pretty URLs."""
from __future__ import annotations

import argparse
import http.server
import socketserver
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent


def parse_redirects(redirects_path: Path) -> list:
    rules = []
    for raw in redirects_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        from_path, to_path = parts[0], parts[1]
        status_token = parts[2]
        forced = status_token.endswith("!")
        status = int(status_token.rstrip("!"))
        rules.append((from_path, to_path, status, forced))
    return rules


class NetlifyDevHandler(http.server.SimpleHTTPRequestHandler):
    rules: list = []

    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".webp": "image/webp",
        ".woff2": "font/woff2",
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".webmanifest": "application/manifest+json",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _request_path(self) -> str:
        return unquote(urlsplit(self.path).path or "/")

    def _query_suffix(self) -> str:
        query = urlsplit(self.path).query
        return f"?{query}" if query else ""

    def _match_rule(self, path: str):
        """Exact-match rules only; the /* catch-all is handled in do_GET."""
        for from_path, to_path, status, forced in self.rules:
            if from_path == "/*":
                continue
            if path == from_path:
                return to_path, status, forced
        return None

    def _catch_all(self):
        for from_path, to_path, status, _forced in self.rules:
            if from_path == "/*":
                return to_path, status
        return None

    def _resolve_file(self, path: str):
        rel = path.lstrip("/")
        if not rel:
            candidates = [ROOT / "index.html"]
        else:
            candidates = [ROOT / rel, ROOT / f"{rel}.html"]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None

    def do_GET(self) -> None:
        path = self._request_path()
        suffix = self._query_suffix()
        match = self._match_rule(path)

        if match:
            target, status, _forced = match
            if status == 200:
                file_path = self._resolve_file(target)
                if file_path is None:
                    self.send_error(404, f"Rewrite target not found: {target}")
                    return
                self.path = "/" + file_path.relative_to(ROOT).as_posix() + suffix
                return super().do_GET()
            if status in (301, 302, 303, 307, 308):
                self.send_response(status)
                self.send_header("Location", target + suffix)
                self.end_headers()
                return

        # Netlify serves real files before the /* catch-all, so only paths
        # that resolve to nothing fall through -- and never asset requests.
        file_path = self._resolve_file(path)
        if file_path is not None:
            self.path = "/" + file_path.relative_to(ROOT).as_posix() + suffix
            return super().do_GET()

        fallback = self._catch_all()
        if fallback and path != "/":
            target, status = fallback
            if status in (301, 302, 303, 307, 308):
                self.send_response(status)
                self.send_header("Location", target)
                self.end_headers()
                return

        return super().do_GET()


def main() -> int:
    parser = argparse.ArgumentParser(description="Automation One local dev server")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    redirects = ROOT / "_redirects"
    if not redirects.is_file():
        print(f"Missing {redirects}", file=sys.stderr)
        return 1

    NetlifyDevHandler.rules = parse_redirects(redirects)
    print(f"Serving {ROOT} on http://localhost:{args.port}/")
    print(f"Loaded {len(NetlifyDevHandler.rules)} redirect rules from _redirects")

    class ReusableServer(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    with ReusableServer(("", args.port), NetlifyDevHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
