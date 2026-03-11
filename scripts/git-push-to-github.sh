#!/usr/bin/env bash
# PortfolioQ — Safe push to GitHub (run after run-project-e2e or initial commit).
# Usage: GITHUB_REPO_URL=https://github.com/YOUR_USERNAME/YOUR_REPO.git bash scripts/git-push-to-github.sh
# Or:   bash scripts/git-push-to-github.sh   (then enter URL when prompted)
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

if [ -z "$GITHUB_REPO_URL" ]; then
  echo "Enter your GitHub repository URL (e.g. https://github.com/username/portfolioQ.git):"
  read -r GITHUB_REPO_URL
fi
if [ -z "$GITHUB_REPO_URL" ]; then
  echo "No URL provided. Exiting."
  exit 1
fi

BRANCH="feature/portfolioQbackup"
if ! git rev-parse --verify "$BRANCH" &>/dev/null; then
  echo "Branch $BRANCH not found. Create it first."
  exit 1
fi

if ! git remote get-url origin &>/dev/null; then
  git remote add origin "$GITHUB_REPO_URL"
  echo "Added remote origin."
else
  echo "Remote origin already set: $(git remote get-url origin)"
  echo "To change: git remote set-url origin $GITHUB_REPO_URL"
fi

echo "Pushing $BRANCH to origin (no force)..."
git push -u origin "$BRANCH"
echo "Done. Branch URL: ${GITHUB_REPO_URL%.git}/tree/$BRANCH"
