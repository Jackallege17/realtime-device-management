#!/usr/bin/env bash
set -euo pipefail
URL=${1:-http://localhost:8000}
EVENTS=${EVENTS:-2000}
for c in 10 50 100 200; do
  echo "=== requests=$EVENTS concurrency=$c ==="
  python scripts/load_test.py --url "$URL" --events "$EVENTS" --concurrency "$c"
done
