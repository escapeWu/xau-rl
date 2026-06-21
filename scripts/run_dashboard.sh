#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -d dashboard/node_modules ]; then
  echo "Installing dashboard dependencies..."
  (cd dashboard && npm install)
fi

if [ ! -d dashboard/dist ]; then
  echo "Building dashboard..."
  (cd dashboard && npm run build)
fi

python scripts/dashboard_api.py "$@"
