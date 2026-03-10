# Push to GitHub and Post-Push Verification

This document describes how to push the current branch to **https://github.com/aistradit/portfolioq** and verify the repository from a fresh clone.

---

## Prerequisites

- Git configured (user.name, user.email).
- Access to **aistradit/portfolioq**: either SSH key added to GitHub, or use HTTPS with a personal access token.

---

## Step 0 — Backup branch and pre-push validation

**Create a safety backup** (from repo root):

```bash
git branch backup-before-safe-push
```

**Run automated pre-push checks** (from repo root or from `portfolioq`):

```bash
# From repo root (parent of portfolioq):
bash portfolioq/scripts/pre-push-validation.sh

# Or from portfolioq:
bash scripts/pre-push-validation.sh
```

This script checks: git health, no tracked venv/.env/artifacts, dependency files, import verification (Docker), and tests. Fix any failures before pushing.

---

## Step 1 — Push from repo root

**Repository root:** The Git root is the **parent** of `portfolioq` (e.g. `~/portfolioQ`). All commands below are from that root.

### Option A: SSH (if your key is added to GitHub)

```bash
cd /home/ubuntu/portfolioQ   # or your repo root
git fetch portfolioq
git status                  # confirm branch and "ahead of" count
git push portfolioq feature/portfolioQbackup
```

### Option B: HTTPS (if SSH fails with "Permission denied")

```bash
cd /home/ubuntu/portfolioQ
# Use HTTPS remote for push (one-time or permanent)
git remote set-url portfolioq https://github.com/aistradit/portfolioq.git
git fetch portfolioq
git push portfolioq feature/portfolioQbackup
# When prompted, use your GitHub username and a Personal Access Token (not password)
```

To switch back to SSH later:

```bash
git remote set-url portfolioq git@github.com:aistradit/portfolioq.git
```

---

## Step 2 — If remote has new commits (merge before push)

If `git fetch portfolioq` and `git status` show "your branch is behind", merge or rebase first:

```bash
git merge portfolioq/feature/portfolioQbackup   # merge
# OR
git rebase portfolioq/feature/portfolioQbackup  # rebase (cleaner history)
git push portfolioq feature/portfolioQbackup
```

Resolve any conflicts, then commit and push again.

---

## Step 3 — Post-push verification (fresh clone)

Simulate another developer pulling and running the project.

### 3.1 Clone

```bash
cd /tmp
git clone https://github.com/aistradit/portfolioq.git portfolioq-fresh
cd portfolioq-fresh
git checkout feature/portfolioQbackup   # if they need this branch
```

If the repo root on GitHub is the **portfolioq** app (not a parent folder), then clone gives you the app directly. If the GitHub repo contains a **portfolioq** subfolder only, adjust paths below (e.g. `cd portfolioq` if clone creates a wrapper repo).

### 3.2 Install dependencies (for local run)

```bash
cd portfolioq/backend
python3 -m venv venv
source venv/bin/activate   # or .venv
pip install -r requirements.txt
```

### 3.3 Run with Docker (recommended)

```bash
cd portfolioq
cp .env.example .env
# Edit .env and set POSTGRES_PASSWORD (and any API keys)
docker compose up -d
# Wait for health, then:
docker compose exec backend python scripts/verify_imports.py
docker compose exec backend python -m pytest tests/ -q
bash scripts/validate-system-e2e.sh
```

### 3.4 Confirm

- No merge conflicts, no broken imports, no failed tests.
- Services start; validation script passes (or only expected warnings).

---

## Branch and remote reference

| Item | Value |
|------|--------|
| **Branch** | `feature/portfolioQbackup` |
| **Remote (aistradit)** | `portfolioq` → `https://github.com/aistradit/portfolioq.git` or `git@github.com:aistradit/portfolioq.git` |
| **Tracked upstream** | `portfolioq/feature/portfolioQbackup` |

---

## Checklist before push

- [ ] Backup branch created: `git branch backup-before-safe-push`
- [ ] Pre-push validation passed: `bash portfolioq/scripts/pre-push-validation.sh`
- [ ] `git status` clean (or only intended changes committed)
- [ ] `git fetch portfolioq` and merge/rebase if behind
- [ ] Tests pass: `docker compose exec backend python -m pytest tests/ -q`
- [ ] No `.env` or `venv` committed (they are in `.gitignore`)
