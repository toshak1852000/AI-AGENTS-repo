#!/usr/bin/env bash
# Pre-push validation: run before pushing to ensure repository stability.
# Usage: from repo root (parent of portfolioq): bash portfolioq/scripts/pre-push-validation.sh
# Or from portfolioq: bash scripts/pre-push-validation.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORTFOLIOQ_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_ROOT="$PORTFOLIOQ_ROOT/backend"
FAILED=0

echo "=============================================="
echo "  Pre-push validation"
echo "  PortfolioQ root: $PORTFOLIOQ_ROOT"
echo "=============================================="

# 1. Git health (run from repo root; repo root may be parent of portfolioq)
echo ""
echo "[1/6] Git repository health..."
GIT_ROOT=$(cd "$PORTFOLIOQ_ROOT" && git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$GIT_ROOT" ]; then
  GIT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi
if ! (cd "$GIT_ROOT" && git rev-parse --git-dir >/dev/null 2>&1); then
  echo "  ERROR: Not a git repository (run from repo root containing .git)."
  exit 1
fi
BRANCH=$(cd "$GIT_ROOT" && git branch --show-current)
echo "  Branch: $BRANCH"
if [ -n "$(cd "$GIT_ROOT" && git status --porcelain)" ]; then
  echo "  WARN: Uncommitted changes present. Commit or stash before push."
  FAILED=1
else
  echo "  OK Working directory clean."
fi

# 2. No sensitive files tracked
echo ""
echo "[2/6] Checking no venv/.env/artifacts tracked..."
if (cd "$GIT_ROOT" && git ls-files) | grep -qE '\.env$|/venv/|/\.venv/|__pycache__|\.pyc$'; then
  echo "  ERROR: Sensitive or build artifacts are tracked. Update .gitignore."
  FAILED=1
else
  echo "  OK No sensitive/build files in index."
fi

# 3. Dependency file exists
echo ""
echo "[3/6] Dependency files..."
if [ ! -f "$BACKEND_ROOT/requirements.txt" ]; then
  echo "  ERROR: backend/requirements.txt not found."
  FAILED=1
else
  echo "  OK requirements.txt present."
fi
if [ ! -f "$PORTFOLIOQ_ROOT/.env.example" ]; then
  echo "  WARN: .env.example not found in portfolioq root."
else
  echo "  OK .env.example present."
fi

# 4. Import verification (Docker)
echo ""
echo "[4/6] Backend import verification (Docker)..."
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  cd "$PORTFOLIOQ_ROOT"
  if docker compose ps backend 2>/dev/null | grep -q Up; then
    if docker compose exec -T backend python scripts/verify_imports.py 2>/dev/null; then
      echo "  OK All imports succeeded."
    else
      echo "  ERROR: Import verification failed."
      FAILED=1
    fi
  else
    echo "  SKIP Backend container not running (start with: docker compose up -d)."
  fi
  cd - >/dev/null
else
  echo "  SKIP Docker not available."
fi

# 5. Tests (Docker)
echo ""
echo "[5/6] Running tests (Docker)..."
if command -v docker >/dev/null 2>&1; then
  cd "$PORTFOLIOQ_ROOT"
  if docker compose ps backend 2>/dev/null | grep -q Up; then
    if docker compose exec -T backend python -m pytest tests/ -q --tb=no 2>&1; then
      echo "  OK All tests passed."
    else
      echo "  ERROR: Some tests failed."
      FAILED=1
    fi
  else
    echo "  SKIP Backend container not running."
  fi
  cd - >/dev/null
else
  echo "  SKIP Docker not available."
fi

# 6. Summary
echo ""
echo "=============================================="
if [ $FAILED -eq 0 ]; then
  echo "  Pre-push validation PASSED."
  echo "  Safe to push after: git fetch portfolioq && git merge (or rebase) if needed."
  echo "=============================================="
  exit 0
else
  echo "  Pre-push validation FAILED. Fix issues before pushing."
  echo "=============================================="
  exit 1
fi
