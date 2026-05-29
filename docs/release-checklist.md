# Release Checklist

Use this checklist before tagging or distributing a private deployment release.

## Configuration

- `.env.production.example` contains every required production setting.
- Real `.env.production` is not committed.
- `STUDY_ENVIRONMENT=production` is set for release testing.
- `STUDY_ACCESS_TOKEN_SECRET` is strong and at least 32 characters.
- `STUDY_DEFAULT_PASSWORD` is not empty and not `changeme`.
- `STUDY_CORS_ORIGINS` does not contain `*`.
- `STUDY_POSTGRES_PASSWORD` and `STUDY_DATABASE_URL` match.

## Iteration Governance

- The active iteration has a record under `docs/iterations/`.
- The iteration record includes goal, optimization direction, scope, Markdown updates, acceptance gates, and follow-up.
- Behavior, deployment, or operations changes update the relevant `.md` files.
- [professional-release-roadmap.md](professional-release-roadmap.md) reflects completed and next iterations.

## Build and Tests

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest tests
```

```powershell
cd frontend
npm.cmd test
npm.cmd run build
```

## Docker

```powershell
docker compose up --build -d
docker compose ps
```

Validate the private deployment compose file:

```powershell
$env:DEVMEMORY_ENV_FILE=".env.production.example"
docker compose --env-file .env.production.example -f docker-compose.prod.yml config
Remove-Item Env:\DEVMEMORY_ENV_FILE
```

Expected services:

- `frontend` up.
- `backend` up.
- `worker` up.
- `postgres` healthy.

## Health and Readiness

```powershell
Invoke-WebRequest http://127.0.0.1:5173 -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/api/system/status -UseBasicParsing
```

## API Smoke

```powershell
powershell -ExecutionPolicy Bypass -File scripts\smoke-test.ps1
```

or:

```powershell
python scripts\smoke_test.py
```

The smoke test must complete login, temporary course creation, Markdown upload, worker ingestion, question answering with citations, learning generation, mind map generation, and cleanup.

## Backup and Restore

- Create a database backup.
- Create an upload volume backup.
- Restore to a clean environment at least once before the first v1.0 release.
- Verify restored courses, documents, and question answering.

## GitHub

- GitHub Actions `backend`, `frontend`, and `docker` jobs pass.
- `main` is clean after release verification.
