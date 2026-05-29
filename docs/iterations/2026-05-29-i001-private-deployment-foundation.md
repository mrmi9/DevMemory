# I-001 Private Deployment Foundation

## Iteration

- ID: I-001
- Date: 2026-05-29
- Status: completed
- Owner: Codex

## Goal

Turn DevMemory from a runnable MVP into a private-deployment release candidate with production configuration, status checks, CI, smoke testing, and release documentation.

## Optimization Direction

Primary direction: Deployment.

Secondary directions: Quality, Observability, Documentation.

## Scope

Included:

- Production/private Docker Compose file.
- Production environment template.
- Readiness endpoint at `/api/system/status`.
- Safer production startup validation.
- Request ID logging.
- AI mode indicator in the login bar.
- GitHub Actions for backend, frontend, and Docker build validation.
- API-based smoke test scripts.
- Deployment, backup/restore, release checklist, and user guide documentation.

Deferred:

- Scripted backup and restore helpers.
- Worker heartbeat table or persistent runtime metrics.
- Upload size limits and rate limiting.
- Multi-user or team permission model.

## Markdown Updates

- [README.md](../../README.md)
- [deployment.md](../deployment.md)
- [backup-restore.md](../backup-restore.md)
- [release-checklist.md](../release-checklist.md)
- [user-guide.md](../user-guide.md)

## Implementation Notes

- Private deployment keeps backend and database inside the Docker network by default.
- Development deployment still exposes backend and database ports for debugging.
- DeepSeek can remain unconfigured; the system exposes offline placeholder AI mode.
- Smoke testing uses HTTP/API and does not depend on browser automation.

## Acceptance Gates

- [x] Backend tests pass.
- [x] Frontend tests pass.
- [x] Frontend build passes.
- [x] Production compose config parses.
- [x] Docker development stack starts.
- [x] `/health` returns 200.
- [x] `/api/system/status` returns 200.
- [x] Smoke test creates and deletes a temporary course successfully.
- [x] Documentation explains deployment, backup/restore, release checks, and user workflow.

## Result

Commit: `32f668d Prepare private deployment release`

Verification evidence recorded in the completion summary:

- Backend tests: 55 passed.
- Frontend tests: 6 files / 13 tests passed.
- Frontend build: success.
- Smoke test: `{"ok": true, "base_url": "http://127.0.0.1:8000/api", "ai_mode": "online"}`.

Follow-up iteration: I-002 Release Governance and Iteration Discipline.
