# Backup and Restore

Back up both PostgreSQL data and uploaded files. A database backup without the upload volume is incomplete because document records point to uploaded files.

## Create a Backup Directory

```powershell
New-Item -ItemType Directory -Force backups
```

## Back Up PostgreSQL

Development stack:

```powershell
docker compose exec -T postgres pg_dump -U study -d study > backups\devmemory-db.sql
```

Production stack:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T postgres pg_dump -U study -d study > backups\devmemory-db.sql
```

## Back Up Uploads

For the default Compose project name, the upload volume is usually `devmemory_uploads`.

```powershell
docker run --rm -v devmemory_uploads:/data -v ${PWD}\backups:/backup busybox tar czf /backup/devmemory-uploads.tgz -C /data .
```

If the volume name is different, find it with:

```powershell
docker volume ls
```

## Restore Database

Start PostgreSQL first, then restore:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up -d postgres
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T postgres psql -U study -d study < backups\devmemory-db.sql
```

## Restore Uploads

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
