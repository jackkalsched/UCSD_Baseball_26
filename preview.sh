#!/usr/bin/env bash
cd "$(dirname "$0")"

echo "Serving at http://localhost:8000"
echo "Press Ctrl+C to stop"
(sleep 1 && open "http://localhost:8000/index.html" 2>/dev/null) &

python3 -m http.server 8000
