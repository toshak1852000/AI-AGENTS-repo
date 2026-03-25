#!/usr/bin/env bash
# Safe push to https://github.com/aistradit/portfolioq
# Run from repo root: cd /home/ubuntu/portfolioQ && bash portfolioq/scripts/push-to-github-aistradit.sh
# Requires: GitHub auth (SSH key or HTTPS with PAT)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$REPO_ROOT" ]; then
  REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd -P)"
fi
cd "$REPO_ROOT"

BRANCH="feature/portfolioQbackup1branch"
REMOTE="portfolioq"

echo ">>> 1. Verify no secrets staged"
if git ls-files --cached | grep -qE '\.env$|/venv/|node_modules/'; then
  echo "ERROR: .env, venv, or node_modules would be pushed. Fix .gitignore and unstage."
  exit 1
fi
echo "  OK"

echo ">>> 2. Fetch and set upstream"
git fetch "$REMOTE" 2>/dev/null || true

echo ">>> 3. Push (will prompt for credentials if HTTPS)"
git push -u "$REMOTE" "$BRANCH"

echo ""
echo ">>> 4. Verify"
git status -sb
echo ""
echo "Branch URL: https://github.com/aistradit/portfolioq/tree/$BRANCH"
