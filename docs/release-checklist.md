# Release Checklist

Use this checklist before tagging or distributing a private deployment release.

## Configuration

- `.env.production.example` contains every required production setting.
- Real `.env.production` is not committed.
- `STUDY_ENVIRONMENT=production` is set for release testing.
- `STUDY_ACCESS_TOKEN_SECRET` is strong and at least 32 characters.
- `STUDY_ACCESS_TOKEN_TTL_MINUTES` is appropriate for the deployment environment.
- `STUDY_DEFAULT_PASSWORD` is not empty and not `changeme`.
- `STUDY_CORS_ORIGINS` does not contain `*`.
- `STUDY_MAX_UPLOAD_BYTES` matches expected document sizes and storage capacity.
- `STUDY_LOGIN_RATE_LIMIT_PER_MINUTE` and `STUDY_AI_RATE_LIMIT_PER_MINUTE` are positive.
- `STUDY_POSTGRES_PASSWORD` and `STUDY_DATABASE_URL` match.

## Security

- Review [security-hardening.md](security-hardening.md).
- Confirm logout removes the browser token and clears local study state.
- Confirm oversized uploads return HTTP `413` and do not leave partial files behind.
- Confirm repeated login attempts return HTTP `429`.
- Confirm repeated AI generation requests return HTTP `429`.
- Document the access token secret rotation process for the target operator.

## Iteration Governance

- The active iteration has a record under `docs/iterations/`.
- The iteration record includes goal, optimization direction, scope, Markdown updates, acceptance gates, and follow-up.
- Behavior, deployment, or operations changes update the relevant `.md` files.
- [professional-release-roadmap.md](professional-release-roadmap.md) reflects completed and next iterations.

## Product UX

- First-run state explains that the user should create the first course.
- A course with no searchable documents explains that materials must be uploaded and parsed before Q&A.
- Failed document parsing shows the failure reason, retry action, and troubleshooting guidance.
- Answers without citations tell the user to upload or choose more relevant materials.

## AI Quality

- Review [ai-quality.md](ai-quality.md).
- Run `..\.venv\Scripts\python.exe -m pytest tests\test_ai_quality.py tests\test_rag_prompt.py tests\test_rag_retrieval.py`.
- Confirm representative answers show `retrieval_confidence` and quality notes.
- Confirm weak or missing context asks users to upload or choose more relevant materials.
- Manually compare at least three answers against their cited document previews before release.

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

## Release Rehearsal

```powershell
powershell -ExecutionPolicy Bypass -File scripts\release-rehearsal.ps1
```

or:

```powershell
python scripts\release_rehearsal.py
```

The generated report is written under `release-evidence/` and must show all automated gates passing before a release tag is created. Use `--allow-dirty` only while developing an iteration, never for final release evidence.

## Release Notes and Tagging

- Review [release-notes/v1.0.0.md](release-notes/v1.0.0.md).
- Review [release-tagging.md](release-tagging.md).
- Confirm release notes include deployment notes, verification evidence, known risks, and deferred v1.1 items.
- Confirm the release rehearsal report has been archived outside Git.
- Confirm clean-environment restore evidence has been recorded at `release-evidence/restore-drill.md`.

```powershell
python scripts\restore_drill_report.py --output release-evidence\restore-drill.md
```

```powershell
python scripts\release_tag_check.py --version v1.0.0
```

Only after the readiness check passes on a clean, pushed `main` commit:

```powershell
git tag -a v1.0.0 -m "DevMemory v1.0.0"
git push origin v1.0.0
```

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
- Run `python scripts\ops.py backup-db --output backups\devmemory-db.sql`.
- Run `python scripts\ops.py backup-uploads --output backups\devmemory-uploads.tgz`.
- Confirm restore commands require `--yes` before running destructive operations.
- Restore to a clean environment at least once before the first v1.0 release.
- Verify restored courses, documents, and question answering.
- Archive `release-evidence/restore-drill.md` outside Git.

## Upgrade and Rollback

- Run `python scripts\ops.py upgrade --smoke` or document why smoke must run from another network context.
- Confirm a previous known-good Git ref is available for rollback.
- Run `python scripts\ops.py rollback --ref <previous-good-ref> --smoke` during release rehearsal when practical.

## GitHub

- GitHub Actions `backend`, `frontend`, `release-tools`, and `docker` jobs pass.
- `main` is clean after release verification.
