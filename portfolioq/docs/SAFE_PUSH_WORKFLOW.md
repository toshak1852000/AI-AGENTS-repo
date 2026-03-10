# Production-Grade Safe Push Workflow

This document defines the **12-step DevOps workflow** for safely pushing the current branch to GitHub so that any developer can pull and run the repository without conflicts, broken dependencies, or runtime failures.

**Target remote:** https://github.com/aistradit/portfolioq  
**Branch:** `feature/portfolioQbackup` (or your current branch)

---

## Step 1 — Verify Git repository health

- Confirm **current branch** and that you are not in detached HEAD state.
- Confirm **remote** `portfolioq` points to `https://github.com/aistradit/portfolioq.git` (or `git@github.com:aistradit/portfolioq.git`).
- Ensure **working directory is clean**. If not, stage and commit:

  ```bash
  git status
  git add <files>
  git commit -m "feat: description"   # or fix:, docs:, chore:
  ```

---

## Step 2 — Create a safety backup branch

Before pushing, create a local backup so you can recover if needed:

```bash
git branch backup-before-safe-push
```

To restore later: `git checkout backup-before-safe-push` or `git reset --hard backup-before-safe-push` (use with care).

---

## Step 3 — Fetch and sync with remote

Fetch the latest from the remote and compare with your branch:

```bash
git fetch portfolioq
git status   # "ahead", "behind", or "diverged"
```

- If **ahead only:** Safe to push (Step 11).
- If **behind** or **diverged:** Merge or rebase, then push:

  ```bash
  git merge portfolioq/feature/portfolioQbackup
  # Resolve conflicts if any, then:
  git add . && git commit -m "merge: remote feature/portfolioQbackup"
  git push portfolioq feature/portfolioQbackup
  ```

---

## Step 4 — Verify project structure

Ensure only valid files are tracked. The following must **not** be committed:

- Virtual environments (`venv/`, `.venv/`, `env/`)
- Build artifacts (`__pycache__/`, `*.pyc`, `dist/`, `build/`)
- Logs and caches (`*.log`, `logs/`, `.cache/`)
- OS/IDE files (`.DS_Store`, `.idea/`, `.vscode/`)
- Secrets (`.env`, `.env.local`)

Check:

```bash
git ls-files | grep -E '\.env$|/venv/|__pycache__|\.pyc' || echo "OK"
```

Validate that `.gitignore` (root and `portfolioq/.gitignore`) includes the above. Fix and commit if anything sensitive was ever added.

---

## Step 5 — Verify dependency files

- **backend/requirements.txt** must exist and list all Python dependencies with versions.
- **.env.example** must exist in `portfolioq` with documented variables (no real secrets).

Another developer should be able to:

- `pip install -r backend/requirements.txt` (or use Docker).
- Copy `.env.example` to `.env` and set values.

---

## Step 6 — Static code validation

- **Imports:** Run `docker compose exec backend python scripts/verify_imports.py` — all modules must import successfully.
- **Linting:** Resolve any critical linter/IDE errors in the codebase.
- No broken imports, missing modules, or syntax errors.

---

## Step 7 — Project execution validation

- Start services: `docker compose up -d` (from `portfolioq`).
- Confirm **application** starts: e.g. `curl http://localhost:8000/health`.
- Confirm **ML/APIs** respond: e.g. `curl http://localhost:8000/api/v1/ml/status`.
- Confirm **experiment tracking** (MLflow) is reachable if used: `http://localhost:5003`.

No runtime failures on startup or on key endpoints.

---

## Step 8 — Run tests

All tests must pass before pushing:

```bash
cd portfolioq
docker compose exec backend python -m pytest tests/ -q --tb=no
```

Fix any failing tests and commit the fixes.

---

## Step 9 — Commit cleanup

- Use **meaningful commit messages** (e.g. `feat:`, `fix:`, `docs:`, `chore:`).
- Avoid unnecessary or duplicate commits; squash only if you have a clear reason and no shared history.

---

## Step 10 — Pre-push validation

Run the automated pre-push script:

```bash
# From repo root:
bash portfolioq/scripts/pre-push-validation.sh

# Or from portfolioq:
bash scripts/pre-push-validation.sh
```

It checks: git health, no tracked artifacts, dependency files, import verification, and tests. All steps must pass (or be explicitly skipped with acceptable reason).

---

## Step 11 — Safe push to GitHub

- Do **not** use `--force` unless you have a documented reason and team agreement.
- Push the current branch and set upstream if needed (run from a machine with GitHub credentials):

  ```bash
  cd <repo_root>   # e.g. /home/ubuntu/portfolioQ
  git fetch portfolioq
  git merge portfolioq/feature/portfolioQbackup   # if behind
  git push portfolioq feature/portfolioQbackup
  # If first time pushing this branch:
  git push -u portfolioq feature/portfolioQbackup
  ```

- **HTTPS:** If push fails with "could not read Username", set `git remote set-url portfolioq https://github.com/aistradit/portfolioq.git` and use a Personal Access Token when prompted.
- **SSH:** Use `git@github.com:aistradit/portfolioq.git` and ensure your SSH key is added to GitHub.

Confirm the remote branch is updated (e.g. on GitHub in the browser).

---

## Step 12 — Post-push validation

Simulate a **fresh developer** workflow:

1. **Clone:** `git clone https://github.com/aistradit/portfolioq.git portfolioq-fresh && cd portfolioq-fresh`
2. **Checkout branch:** `git checkout feature/portfolioQbackup`
3. **Install dependencies:** Copy `.env.example` to `.env`, set `POSTGRES_PASSWORD`; run `docker compose up -d` (from `portfolioq` if repo structure has it), or `pip install -r backend/requirements.txt` in a venv.
4. **Run project:** `docker compose up -d` and confirm health; run `pytest tests/` or `scripts/validate-system-e2e.sh` if available.

Another developer should be able to clone, checkout, install, and run **without conflicts, missing dependencies, or runtime errors**.

---

## Summary checklist

| Step | Action | Status |
|------|--------|--------|
| 1 | Git health, clean working dir | ☐ |
| 2 | Backup branch `backup-before-safe-push` | ☐ |
| 3 | Fetch + merge/rebase if behind | ☐ |
| 4 | No venv/artifacts/secrets tracked | ☐ |
| 5 | requirements.txt + .env.example OK | ☐ |
| 6 | Imports and static checks OK | ☐ |
| 7 | Services and APIs start and respond | ☐ |
| 8 | All tests pass | ☐ |
| 9 | Commits clean and meaningful | ☐ |
| 10 | pre-push-validation.sh passed | ☐ |
| 11 | Push to portfolioq remote | ☐ |
| 12 | Post-push: clone + install + run OK | ☐ |

---

*For quick reference, see also [GIT_PUSH_AND_VERIFY.md](GIT_PUSH_AND_VERIFY.md).*
