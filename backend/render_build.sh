#!/usr/bin/env bash
set -e

export PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH:-/opt/playwright}

echo "=== Installing Python dependencies ==="
pip install -r backend/requirements.txt

echo "=== Installing Playwright Chromium ==="
python -m playwright install --with-deps chromium

echo "=== Build complete ==="