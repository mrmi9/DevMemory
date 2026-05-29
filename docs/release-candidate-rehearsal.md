# Release Candidate Rehearsal

Use this guide when preparing a DevMemory private-deployment release candidate. The rehearsal proves that the current code can be tested, built, started, smoke-tested, and documented before tagging.

## Run the Rehearsal

Recommended Windows command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\release-rehearsal.ps1
```

Equivalent Python command:

```powershell
python scripts\release_rehearsal.py
```

The report is written to:

```text
release-evidence/release-candidate-rehearsal.md
```

`release-evidence/` is intentionally ignored by Git. Archive or attach the generated report to the release notes instead of committing it.

## What It Checks

The rehearsal runs these gates:

- Clean Git workspace check.
- Backend tests.
- Frontend tests.
- Frontend production build.
- Production compose configuration using `.env.production.example`.
- Docker stack rebuild.
- Docker service status.
- API smoke test through the frontend `/api` proxy.

The API smoke step retries because Docker may report containers as started before nginx and backend are fully ready.

## Development Mode

During implementation, allow dirty worktrees and skip Docker when needed:

```powershell
python scripts\release_rehearsal.py --allow-dirty --skip-docker --output release-evidence\dev-rehearsal.md
```

This is useful for validating the gate sequence while an iteration is still in progress. A real release candidate must run without `--allow-dirty`.

## Backup and Restore Drill

The rehearsal report includes the backup and restore commands, but it does not run destructive restore operations automatically. Before tagging v1.0, run the restore drill in a clean environment:

```powershell
python scripts\ops.py backup-db --output backups\devmemory-db.sql
python scripts\ops.py backup-uploads --output backups\devmemory-uploads.tgz
python scripts\ops.py restore-db --input backups\devmemory-db.sql --yes
python scripts\ops.py restore-uploads --input backups\devmemory-uploads.tgz --yes
python scripts\smoke_test.py --base-url http://127.0.0.1:5173/api
```

Record the restore result in the generated report or release notes.

## Release Rule

Do not tag a private release until:

- The rehearsal report shows all automated gates passing.
- Backup and restore have been verified on a clean environment.
- The GitHub Actions checks on `main` are green.
- The active iteration record and release checklist are up to date.
