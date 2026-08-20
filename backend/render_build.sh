#!/usr/bin/env bash
set -e

export PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH:-/data/playwright}
mkdir -p /data 2>/dev/null || true

echo "=== Installing Python dependencies ==="
pip install -r backend/requirements.txt

echo "=== Installing Playwright Chromium ==="
# Try to install OS dependencies (needs root; ok to skip on Render)
if command -v apt-get >/dev/null 2>&1 && [ "$(id -u)" = "0" ]; then
    python -m playwright install-deps chromium || echo "  (install-deps skipped)"
fi
python -m playwright install chromium || echo "  (chromium install skipped - app runs without browser features)"

echo "=== Building frontend (static export) ==="
cd frontend
npm install
npm run build

echo "=== Build complete ==="