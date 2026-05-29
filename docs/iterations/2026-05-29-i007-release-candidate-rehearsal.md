# 2026-05-29 I-007 Release Candidate Rehearsal

## Iteration

- ID: I-007
- Date: 2026-05-29
- Status: completed
- Owner: Codex

## Goal

Turn release-candidate rehearsal into a repeatable command that runs release gates and writes a Markdown evidence report.

## Optimization Direction

Deployment, Quality, and Documentation.

## Scope

Included:

- `scripts/release_rehearsal.py` for backend tests, frontend tests, frontend build, production compose config, Docker rebuild, service status, and smoke verification.
- `scripts/release-rehearsal.ps1` Windows wrapper.
- Unit tests for rehearsal plan construction, Docker skipping, report rendering, and smoke retry configuration.
- `release-evidence/` ignored by Git for generated rehearsal reports.
- Documentation for automated rehearsal and manual clean-environment restore drill.

Deferred:

- Automated destructive restore execution.
- Separate clean Docker project orchestration.
- Release artifact packaging and GitHub release creation.

## Markdown Updates

- Added [release-candidate-rehearsal.md](../release-candidate-rehearsal.md).
- Updated [professional-release-roadmap.md](../professional-release-roadmap.md).
- Updated [release-checklist.md](../release-checklist.md).
- Updated [deployment.md](../deployment.md).
- Updated [README.md](../../README.md).
- Added this iteration record.

## Implementation Notes

- Real release rehearsal fails on dirty worktrees by default.
- `--allow-dirty` is available for iteration-time validation only.
- Generated reports go under `release-evidence/`, which is intentionally ignored.
- The smoke gate retries to handle the short startup window after Docker rebuilds.
- Restore commands are documented in the generated report but must be run deliberately in a clean environment.

## Acceptance Gates

- [x] Rehearsal unit tests pass: `3 passed`.
- [x] Development rehearsal without Docker passes.
- [x] Full Docker rehearsal passes after smoke retry: backend tests, frontend tests, frontend build, compose config, Docker rebuild, service status, and API smoke.
- [x] Documentation links and commands match the implementation.

## Result

I-007 is ready to commit after final verification. The next recommended iteration is I-008 Release Notes and Tagging Preparation.
