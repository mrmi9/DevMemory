# DevMemory Private Deployment Guide

This guide describes the v1.0 private deployment path for a single machine or an internal server.

## Minimum Environment

- Docker Desktop or Docker Engine with Docker Compose v2.
- 4 GB memory minimum, 8 GB recommended when OCR is enabled.
- 10 GB free disk minimum, plus space for uploaded documents and PostgreSQL data.
- Port `5173` available for the web UI.
- A DeepSeek API key is recommended for real AI answers. Without it, DevMemory runs in offline placeholder AI mode.

## Production Setup

For daily use on Windows, the project root includes shortcut scripts:

```powershell
.\Start-DevMemory.bat
```

This starts the private Docker Compose stack, waits for the web entry to respond, and opens `http://127.0.0.1:5173`.

To stop the stack:

```powershell
.\Stop-DevMemory.bat
```

You can also run the PowerShell scripts directly:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-devmemory.ps1
powershell -ExecutionPolicy Bypass -File scripts\stop-devmemory.ps1
```

1. Copy the production environment template:

```powershell
copy .env.production.example .env.production
```

2. Edit `.env.production` and set strong values:

```env
STUDY_ENVIRONMENT=production
STUDY_DEFAULT_USERNAME=admin
STUDY_DEFAULT_PASSWORD=<private password>
STUDY_ACCESS_TOKEN_SECRET=<at least 32 random characters>
STUDY_CORS_ORIGINS=["http://localhost:5173"]
STUDY_POSTGRES_PASSWORD=<private database password>
STUDY_DATABASE_URL=postgresql+psycopg://study:<private database password>@postgres:5432/study
```

3. Start the private deployment stack:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

To validate the production compose file against the example values without creating `.env.production`, use:

```powershell
$env:DEVMEMORY_ENV_FILE=".env.production.example"
docker compose --env-file .env.production.example -f docker-compose.prod.yml config
Remove-Item Env:\DEVMEMORY_ENV_FILE
```

4. Open the product:

```text
http://localhost:5173
```

## Stop and Restart

Stop services:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml down
```

Restart services:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

## Update to a New Version

Recommended scripted upgrade:

```powershell
git pull
python scripts\ops.py upgrade --smoke
```

Manual upgrade:

```powershell
git pull
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
python scripts/smoke_test.py --base-url http://127.0.0.1:5173/api --username <username> --password <password>
```

The private deployment compose file does not publish the backend port. Smoke testing a production stack should use the frontend nginx `/api` proxy at `http://127.0.0.1:5173/api`.

## Release Candidate Rehearsal

Before tagging or distributing a release candidate, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\release-rehearsal.ps1
```

The rehearsal writes a Markdown report under `release-evidence/`. See [release-candidate-rehearsal.md](release-candidate-rehearsal.md) for the full process and restore drill.

## Roll Back a Failed Upgrade

Recommended scripted rollback:

```powershell
python scripts\ops.py rollback --ref <previous-good-git-ref> --smoke
```

Manual rollback:

```powershell
git checkout <previous-good-git-ref>
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
python scripts/smoke_test.py --base-url http://127.0.0.1:5173/api --username <username> --password <password>
```

After a successful rollback, decide whether to stay on the rollback ref, create a hotfix branch, or return to `main` after the issue is fixed.

## Port Conflicts

If port `5173` is already used, change the frontend mapping in `docker-compose.prod.yml`:

```yaml
frontend:
  ports:
    - "8080:80"
```

Then set:

```env
STUDY_CORS_ORIGINS=["http://localhost:8080"]
```

## Runtime Checks

Development stack checks:

```powershell
Invoke-WebRequest http://127.0.0.1:5173 -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/api/system/status -UseBasicParsing
```

Production stack checks:

```powershell
Invoke-WebRequest http://127.0.0.1:5173 -UseBasicParsing
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```
