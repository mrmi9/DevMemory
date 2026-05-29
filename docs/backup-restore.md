# Backup and Restore

Back up both PostgreSQL data and uploaded files. A database backup without the upload volume is incomplete because document records point to uploaded files.

## Scripted Backup Directory

```powershell
New-Item -ItemType Directory -Force backups
```

## Scripted PostgreSQL Backup

Recommended:

```powershell
python scripts\ops.py backup-db --output backups\devmemory-db.sql
```

Windows wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\ops.ps1 backup-db --output backups\devmemory-db.sql
```

The helper uses the production compose file by default:

```text
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T postgres pg_dump -U study -d study
```

## Manual PostgreSQL Backup

Development stack:

```powershell
docker compose exec -T postgres pg_dump -U study -d study > backups\devmemory-db.sql
```

Production stack:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T postgres pg_dump -U study -d study > backups\devmemory-db.sql
```

## Scripted Upload Backup

Recommended:

```powershell
python scripts\ops.py backup-uploads --output backups\devmemory-uploads.tgz
```

Windows wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\ops.ps1 backup-uploads --output backups\devmemory-uploads.tgz
```

## Manual Upload Backup

For the default Compose project name, the upload volume is usually `devmemory_uploads`.

```powershell
docker run --rm -v devmemory_uploads:/data -v ${PWD}\backups:/backup busybox tar czf /backup/devmemory-uploads.tgz -C /data .
```

If the volume name is different, find it with:

```powershell
docker volume ls
```

## Scripted Database Restore

Restore is destructive and requires `--yes`:

```powershell
python scripts\ops.py restore-db --input backups\devmemory-db.sql --yes
```

Without `--yes`, the helper refuses to run.

## Manual Database Restore

Start PostgreSQL first, then restore:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up -d postgres
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T postgres psql -U study -d study < backups\devmemory-db.sql
```

## Scripted Upload Restore

Restore is destructive because it clears the uploads volume before extracting the backup:

```powershell
python scripts\ops.py restore-uploads --input backups\devmemory-uploads.tgz --yes
```

Without `--yes`, the helper refuses to run.

## Manual Upload Restore

```powershell
docker run --rm -v devmemory_uploads:/data -v ${PWD}\backups:/backup busybox sh -c "rm -rf /data/* && tar xzf /backup/devmemory-uploads.tgz -C /data"
```

## Verify Restore

1. Start the full stack:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

2. Open `http://localhost:5173`.
3. Log in.
4. Confirm courses and documents appear.
5. Open at least one uploaded document preview or run a knowledge-base question against an existing course.

## Clean Restore Drill Evidence

Before tagging `v1.0.0`, record restore evidence in an ignored report:

```powershell
python scripts\restore_drill_report.py --output release-evidence\restore-drill.md
```

Then run the recorded backup, restore, startup, and smoke commands in a clean Docker context or clean machine. Update the generated report if the operator, environment, start time, restore result, or smoke result differs from the defaults.

The release tag readiness check requires this report:

```powershell
python scripts\release_tag_check.py --version v1.0.0
```

`release-evidence/` is intentionally ignored by Git. Archive `release-evidence/restore-drill.md` with the release evidence instead of committing it.
