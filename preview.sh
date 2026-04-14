#!/usr/bin/env bash
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

echo "Serving at http://localhost:8000"
echo "Press Ctrl+C to stop"
(sleep 1 && open "http://localhost:8000" 2>/dev/null) &

export FLASK_APP=app.py
export FLASK_DEBUG=1
python3 -m flask run --host=0.0.0.0 --port=8000
