# I-008 Release Notes and Tagging Preparation

Date: 2026-05-29

Status: completed.

## Iteration Goal

Prepare DevMemory for an auditable v1.0 release tag by adding release notes, tag readiness checks, and explicit deferred-scope documentation.

## Optimization Direction

- Quality: make tag readiness machine-checkable.
- Documentation: preserve release notes, risks, deferred work, and tagging instructions in Markdown.
- Operations: keep release evidence separate from committed source files.

## Scope

Included:

- Add a release notes template and `v1.0.0` draft notes.
- Add a release tag readiness checker.
- Add tests for release readiness rules.
- Document the release tagging process.
- Update README, release checklist, and roadmap links.

Deferred:

- Creating the actual `v1.0.0` tag.
- Publishing a GitHub Release artifact.
- Automating destructive restore drills.

## Markdown Updates

- Added [release-notes/template.md](../release-notes/template.md).
- Added [release-notes/v1.0.0.md](../release-notes/v1.0.0.md).
- Added [release-tagging.md](../release-tagging.md).
- Updated [professional-release-roadmap.md](../professional-release-roadmap.md).
- Updated [release-checklist.md](../release-checklist.md).
- Updated [README.md](../../README.md).

## Implementation Notes

- `scripts/release_tag_check.py` checks version format, clean Git state, required release note sections, checklist references, roadmap completion, and the I-008 iteration record.
- `scripts/test_release_tag_check.py` covers successful readiness, missing release-note sections, dirty worktree rejection, and invalid version rejection.
- The checker intentionally refuses dirty worktrees so final tags are created only after reviewed commits.

## Acceptance Gates

- [x] Release tag readiness tests pass.
- [x] Release notes contain deployment notes, verification evidence, known risks, and deferred v1.1 work.
- [x] Release checklist references `docs/release-notes/v1.0.0.md`.
- [x] Roadmap marks I-008 completed and identifies the next iteration.

## Follow-up

The next recommended iteration is I-009 Clean Restore Drill Evidence, which should capture an actual clean-machine backup/restore rehearsal and archive the evidence before tagging v1.0.0.
