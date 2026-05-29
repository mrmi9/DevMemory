# Security Hardening

DevMemory v1.0 is designed for local or intranet private deployment. These controls reduce common private-network risks without turning the product into a public SaaS security stack.

## Configuration

Set these values in `.env.production` before starting the production compose stack:

| Setting | Default | Production guidance |
| --- | --- | --- |
| `STUDY_ACCESS_TOKEN_SECRET` | unsafe placeholder | Use at least 32 random characters. Rotate when an operator leaves or a host is compromised. |
| `STUDY_ACCESS_TOKEN_TTL_MINUTES` | `1440` | Default is 24 hours. Use a shorter value for shared machines. |
| `STUDY_DEFAULT_PASSWORD` | unsafe placeholder | Use a private strong password. Empty passwords are rejected in production. |
| `STUDY_CORS_ORIGINS` | `["*"]` in development | Must name trusted origins in production. `*` is rejected. |
| `STUDY_MAX_UPLOAD_BYTES` | `52428800` | Default is 50 MB per file. Increase only when storage and parsing capacity are planned. |
| `STUDY_LOGIN_RATE_LIMIT_PER_MINUTE` | `5` | Limits repeated login attempts per client IP and username. |
| `STUDY_AI_RATE_LIMIT_PER_MINUTE` | `30` | Limits AI generation requests per authenticated user. |

Production startup refuses unsafe defaults, incompatible embedding dimensions, and unwritable upload directories.

## Authentication

DevMemory uses the configured default account for v1.0 private deployments. Passwords are stored with PBKDF2 hashes, and legacy SHA-256 hashes are only accepted for backward compatibility.

Access tokens are signed with `STUDY_ACCESS_TOKEN_SECRET` and expire after `STUDY_ACCESS_TOKEN_TTL_MINUTES`. Logout is client-side: it removes the browser token and clears local course state. Because tokens are stateless, rotating `STUDY_ACCESS_TOKEN_SECRET` invalidates existing sessions.

## Rate Limiting

The backend includes in-memory rate limits:

- Login attempts: keyed by client IP and username.
- AI generation: keyed by authenticated user id.

These limits are best-effort for the single-node Docker Compose deployment. They reset when the backend container restarts and are not shared across multiple backend replicas. A distributed limiter can be added later if v1.1 introduces multi-node deployment.

## Upload Protection

Uploads are streamed to disk and rejected with HTTP `413` when they exceed `STUDY_MAX_UPLOAD_BYTES`. Oversized partial files are removed before the API returns the error.

Uploaded file deletion remains constrained to `STUDY_UPLOAD_DIR`. The backend resolves the target path and removes it only when it is inside the upload root and is a file.

## Secret Rotation

To rotate the access token secret:

1. Stop the stack.
2. Update `STUDY_ACCESS_TOKEN_SECRET` in `.env.production`.
3. Start the stack again.
4. Ask users to log in again.

To rotate the default password:

1. Change `STUDY_DEFAULT_PASSWORD` in `.env.production`.
2. Restart the stack.
3. If the user already exists, update the password through a maintenance script or recreate the private deployment user after backup. v1.0 does not yet include a password-change UI.

## Security Acceptance Gates

Run these before tagging a private release:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest tests\test_security_config.py tests\test_security_hardening.py
```

```powershell
cd frontend
npm.cmd test -- LoginBar.test.ts
```

Then run the full backend, frontend, build, Docker, and smoke gates from [release-checklist.md](release-checklist.md).
