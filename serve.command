#!/bin/bash
cd "$(dirname "$0")"
PORT=8765
URL="http://127.0.0.1:${PORT}/"
echo "Preview: ${URL}"
echo "Use this server — do not open .html files directly from Finder."
open "$URL" 2>/dev/null || true
python3 -m http.server "$PORT"
