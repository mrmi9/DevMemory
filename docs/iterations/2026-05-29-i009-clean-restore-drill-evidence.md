# I-009 Clean Restore Drill Evidence

Date: 2026-05-29

Status: completed.

## Iteration Goal

Make clean-environment backup and restore evidence explicit before a v1.0 release tag is created.

## Optimization Direction

- Data Safety: prove restored database and uploaded files can support the product after recovery.
- Quality: make release tag readiness depend on restore evidence.
- Documentation: keep the restore evidence workflow visible in release notes and checklists.

## Scope

Included:

- Add a restore drill evidence report generator.
- Require restore drill evidence in the release tag readiness check.
- Document the restore evidence workflow in backup, release checklist, release notes, and tagging docs.
- Shift the next roadmap priority from release operations to user-facing product functionality.

Deferred:

- Automatically executing destructive restore commands.
- Creating the `v1.0.0` tag.
- Publishing GitHub Release artifacts.

## Markdown Updates

- Updated [backup-restore.md](../backup-restore.md).
- Updated [release-checklist.md](../release-checklist.md).
- Updated [release-notes/v1.0.0.md](../release-notes/v1.0.0.md).
- Updated [release-tagging.md](../release-tagging.md).
- Updated [professional-release-roadmap.md](../professional-release-roadmap.md).
- Updated [README.md](../../README.md).

## Implementation Notes

- `scripts/restore_drill_report.py` writes `release-evidence/restore-drill.md`.
- `scripts/release_tag_check.py` now requires restore evidence with operator, environment, start time, restore result, and smoke result fields.
- The restore evidence tool records the release evidence structure and commands only; operators still run destructive restore commands deliberately.
- `release-evidence/` remains ignored and must be archived outside Git.

## Acceptance Gates

- [x] Restore drill report tests pass.
- [x] Release tag readiness tests cover missing, incomplete, and complete restore evidence.
- [x] Release tag readiness passes after generated restore evidence exists.
- [x] Release documentation explains the evidence workflow.

## Follow-up

The next recommended iteration is I-010 Guided First-Run Checklist and Learning Workflow Polish. The release-engineering baseline is now strong enough that the next work should prioritize user-facing product functionality unless a v1.0 blocking issue appears.
