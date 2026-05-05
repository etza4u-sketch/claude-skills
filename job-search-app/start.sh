#!/usr/bin/env bash
# Start the AI Job Search web application
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "┌─────────────────────────────────────────────┐"
echo "│   AI Job Search — Bronze / Silver / Gold     │"
echo "│   http://localhost:5050                      │"
echo "└─────────────────────────────────────────────┘"
echo ""

python -m pip install -q -r requirements.txt
python webapp/server.py
