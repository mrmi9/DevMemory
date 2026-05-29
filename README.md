# DevMemory

DevMemory is a private AI study knowledge base for course notes, document retrieval, AI-assisted Q&A, review cards, generated questions, wrong notes, mind maps, and progress tracking.

The v1.0 target is a local or intranet private deployment. It is not a public SaaS product and does not include billing, multi-tenant administration, or organization roles.

## Features

- Course-based document libraries for PDF, Word, Markdown, and image notes.
- Background parsing, chunking, embedding, and pgvector storage.
- Course-scoped Q&A with cited source chunks.
- Review cards, exam questions, wrong-note analysis, and Markmap mind maps.
- Progress tracking for study cards and course review.
- DeepSeek integration with offline placeholder mode when no API key is configured.
- Private deployment health/readiness status at `/api/system/status`.
- Private deployment hardening: configurable token lifetime, upload size limits, login/AI rate limits, and logout.

## Private Deployment

1. Copy the production environment template:

```powershell
copy .env.production.example .env.production
```

2. Edit `.env.production` and set strong values for:

- `STUDY_ACCESS_TOKEN_SECRET`
- `STUDY_DEFAULT_PASSWORD`
- `STUDY_ACCESS_TOKEN_TTL_MINUTES`
- `STUDY_MAX_UPLOAD_BYTES`
- `STUDY_LOGIN_RATE_LIMIT_PER_MINUTE`
- `STUDY_AI_RATE_LIMIT_PER_MINUTE`
- `STUDY_POSTGRES_PASSWORD`
- `STUDY_DATABASE_URL`
- `STUDY_CORS_ORIGINS`
- `STUDY_DEEPSEEK_API_KEY` if real AI output is required

3. Start the private deployment stack:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

4. Open:

```text
http://localhost:5173
```

Production/private deployment details are in [docs/deployment.md](docs/deployment.md).

## Development Start

Development mode exposes the frontend, backend, and PostgreSQL ports for local debugging.

1. Edit `.env` and set at least `STUDY_ACCESS_TOKEN_SECRET`.
2. Add `STUDY_DEEPSEEK_API_KEY` if you want real AI generation instead of offline placeholder responses.
3. Start the stack:

```powershell
docker compose up --build
```

4. Open:

```text
http://localhost:5173
```

Default development credentials come from `.env`:

- `STUDY_DEFAULT_USERNAME`
- `STUDY_DEFAULT_PASSWORD`

## Local Development

Core backend dependencies, without the optional OCR stack:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Optional image OCR dependencies:

```powershell
.venv\Scripts\python.exe -m pip install -r backend\requirements-ocr.txt
```

PaddleOCR is heavy and is most reliable in the Docker image, which uses Python 3.12. On local Python 3.14, OCR dependencies may not install cleanly.

Frontend dependencies:

```powershell
cd frontend
npm.cmd install
npm.cmd test
npm.cmd run build
```

## Verification

Backend:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest tests
```

Frontend:

```powershell
cd frontend
npm.cmd test
npm.cmd run build
```

Smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\smoke-test.ps1
```

or:

```powershell
python scripts\smoke_test.py
```

Release checks are listed in [docs/release-checklist.md](docs/release-checklist.md).

## Security

Private deployment security controls and rotation steps are documented in [docs/security-hardening.md](docs/security-hardening.md).

## Professional Release Iterations

DevMemory is iterated toward a professional private-deployment release through explicit release iterations. Each iteration records its goal, optimization direction, scope, documentation updates, and acceptance gates.

- Roadmap: [docs/professional-release-roadmap.md](docs/professional-release-roadmap.md)
- Iteration template: [docs/iteration-template.md](docs/iteration-template.md)
- Iteration records: [docs/iterations](docs/iterations)

## Backup and Restore

Back up both PostgreSQL and uploaded files. See [docs/backup-restore.md](docs/backup-restore.md).

## User Guide

End-user workflow documentation is in [docs/user-guide.md](docs/user-guide.md).

## Structure

- `backend/app/services`: parsing, chunking, embedding, RAG prompt, and DeepSeek calls.
- `backend/app/api/routes.py`: REST API.
- `backend/app/worker.py`: database-backed ingestion worker.
- `frontend/src/components`: course, upload, chat, study generation, mind map, and progress UI.
- `infra/postgres/init.sql`: enables the pgvector extension.
- `scripts/smoke_test.py`: API-based end-to-end smoke test.

## Notes

- The default `HashEmbeddingProvider` is a lightweight local development implementation.
- The embedding provider is selected with `STUDY_EMBEDDING_PROVIDER`.
- Production mode is enabled with `STUDY_ENVIRONMENT=production`.
- In production, startup refuses unsafe defaults for `STUDY_ACCESS_TOKEN_SECRET`, `STUDY_DEFAULT_PASSWORD`, wildcard CORS origins, incompatible embedding dimensions, and unwritable upload directories.
- Login and AI generation rate limits are in-memory for the single-node v1.0 deployment and reset when the backend restarts.
