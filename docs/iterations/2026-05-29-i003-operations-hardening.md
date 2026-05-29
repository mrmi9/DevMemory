# I-003 Operations Hardening

## Iteration

- ID: I-003
- Date: 2026-05-29
- Status: completed
- Owner: Codex

## Goal

Turn backup, restore, upgrade, and rollback from documentation-only instructions into repeatable helper commands for private deployments.

## Optimization Direction

Primary direction: Data Safety.

Secondary directions: Deployment, Quality, Documentation.

## Scope

Included:

- Add `scripts/ops.py` as a cross-platform operations helper.
- Add `scripts/ops.ps1` as a Windows-friendly wrapper.
- Add unit tests for command construction and destructive restore safety.
- Require explicit `--yes` for restore operations.
- Document scripted database backup, upload backup, restore, upgrade, rollback, and smoke verification.

Deferred:

- Full restore drill against a separate clean Docker project.
- Scheduled backup automation.
- Remote backup storage.
- Encrypted backup archives.

## Markdown Updates

- [professional-release-roadmap.md](../professional-release-roadmap.md)
- [backup-restore.md](../backup-restore.md)
- [deployment.md](../deployment.md)
- [release-checklist.md](../release-checklist.md)
- [2026-05-29-i003-operations-hardening.md](2026-05-29-i003-operations-hardening.md)

## Implementation Notes

- `backup-db` writes a PostgreSQL dump to a host file.
- `backup-uploads` archives the Docker uploads volume as a `tgz` file.
- `restore-db` and `restore-uploads` refuse to run unless `--yes` is supplied.
- `upgrade --smoke` restarts the private deployment stack and then runs the API smoke test.
- `rollback --ref <git-ref>` checks out a target ref, rebuilds the private deployment stack, and can run smoke verification.

## Acceptance Gates

- [x] Operations helper unit tests pass.
- [x] Restore commands require explicit `--yes`.
- [x] Backup and restore docs reference the helper commands.
- [x] Deployment docs describe upgrade and rollback with smoke verification.
- [x] Release checklist includes scripted operations checks.
- [x] Roadmap marks I-003 as completed and points to this record.

## Result

Commit: the commit that adds the operations helper, tests, and this iteration record.

Follow-up iteration: I-004 Security Hardening.
