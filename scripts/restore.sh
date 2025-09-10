#!/usr/bin/env bash
set -euo pipefail
FILE=${1:-}
test -f "$FILE" || { echo "Usage: $0 path/to/db-*.sql"; exit 1; }
cat "$FILE" | docker exec -i postgres psql -U spooky spooky
echo "Restore complete."
