#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

PORT=${1:-8080}
echo "Frontend: http://$(hostname -I | awk '{print $1}'):${PORT}"
echo "API backend must be running on port 8000 (./run.sh)"
echo ""

python3 -m http.server "$PORT" --directory frontend
