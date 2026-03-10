# Push Branch to GitHub

## Current state (after preparation)

- **Branch:** `feature/portfolioQbackup`
- **Remote:** `origin` → `https://github.com/toshak1852000/AI-AGENTS-repo.git`
- **Status:** All changes committed; working tree clean. Branch is ready to push.

## One-time: push from your machine

Authentication is required. Run from the **repository root** (parent of `portfolioq`):

```bash
cd /path/to/portfolioQ   # or wherever this repo lives

# Push to GitHub (use your credentials when prompted)
git push origin feature/portfolioQbackup
```

To set upstream so future pushes use `git push`:

```bash
git push -u origin feature/portfolioQbackup
```

If you use SSH and your remote is SSH-based:

```bash
git remote set-url origin git@github.com:toshak1852000/AI-AGENTS-repo.git
git push -u origin feature/portfolioQbackup
```

## Post-push: verify from a fresh clone

Another developer (or you on another machine) can verify the branch is runnable:

```bash
git clone https://github.com/toshak1852000/AI-AGENTS-repo.git portfolioQ-clone
cd portfolioQ-clone
git checkout feature/portfolioQbackup
cd portfolioq
cp .env.example .env   # then edit .env with POSTGRES_PASSWORD, SECRET_KEY, etc.
docker compose up -d
# Optional: bash scripts/validate-system-e2e.sh
```

## What was committed

- ML platform (factor/risk/opportunity models, MLflow, pipelines, validation scripts)
- Docs (ML platform technical doc, validation reports, architecture)
- API/config fixes (ReportFormat, create_tables, pyrightconfig)
- Scripts: validate-system-e2e, validate-all-apis, start_mlflow, verify_imports

No `.env`, `venv/`, `__pycache__/`, or other ignored files were committed.
