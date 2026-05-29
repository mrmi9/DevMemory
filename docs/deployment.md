# DevMemory Private Deployment Guide

This guide describes the v1.0 private deployment path for a single machine or an internal server.

## Minimum Environment

- Docker Desktop or Docker Engine with Docker Compose v2.
- 4 GB memory minimum, 8 GB recommended when OCR is enabled.
- 10 GB free disk minimum, plus space for uploaded documents and PostgreSQL data.
- Port `5173` available for the web UI.
- A DeepSeek API key is recommended for real AI answers. Without it, DevMemory runs in offline placeholder AI mode.

## Production Setup

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

```powershell
git pull
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
python scripts/smoke_test.py --base-url http://127.0.0.1:8000/api --username <username> --password <password>
```

The private deployment compose file does not publish the backend port. For smoke testing a production stack, run the script from inside the Docker network or temporarily use the development compose file on a trusted machine. The browser UI continues to call the backend through the frontend nginx `/api` proxy.

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
