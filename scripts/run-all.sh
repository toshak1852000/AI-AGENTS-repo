#!/usr/bin/env bash
# Run from repo root (portfolioQ): delegates to portfolioq/scripts/run-all.sh.
# Usage: bash scripts/run-all.sh [BASE_URL]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PORTFOLIOQ_SCRIPTS="$ROOT_DIR/portfolioq/scripts/run-all.sh"
if [ ! -f "$PORTFOLIOQ_SCRIPTS" ]; then
  echo "Error: portfolioq/scripts/run-all.sh not found. Run from portfolioQ repo root or from portfolioq: bash scripts/run-all.sh"
  exit 1
fi
exec bash "$PORTFOLIOQ_SCRIPTS" "$@"
