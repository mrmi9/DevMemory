# I-010 Chinese UX Recovery and First-Run Workflow Polish

Date: 2026-05-29

Status: completed.

## Iteration Goal

Recover trustworthy Chinese UX copy and make the path from uploaded materials to review visible as a guided learning loop.

## Optimization Direction

- UX: turn the workspace from a collection of panels into a guided study workflow.
- Product Quality: remove mojibake from frontend source, tests, and rendered text.
- Documentation: update the user guide and roadmap to describe the new learning loop.

## Scope

Included:

- Repair user-facing Chinese copy in the main workspace, login, course, upload, chat, study tools, mind map, progress, and API error text.
- Add a `LearningWorkflowChecklist` panel with seven steps: course, upload, parsing, first question, generated assets, review, and weakness review.
- Add frontend tests that assert readable Chinese and guard against common mojibake characters.
- Update user and roadmap documentation.

Deferred:

- Document search, filters, batch retry, tags, and duplicate detection.
- Turning Q&A answers into cards, questions, or wrong notes.
- Replacing browser `prompt` and `confirm` with in-app modals.

## Markdown Updates

- Updated [user-guide.md](../user-guide.md).
- Updated [professional-release-roadmap.md](../professional-release-roadmap.md).
- Updated [README.md](../../README.md).
- Added [2026-05-29-i010-chinese-ux-workflow-polish.md](2026-05-29-i010-chinese-ux-workflow-polish.md).

## Implementation Notes

- `LearningWorkflowChecklist.vue` reads the current course, documents, chat sessions, generated cards, generated questions, and card mastery to show where the learner is in the loop.
- Main frontend panels now use readable UTF-8 Chinese text.
- Frontend tests cover the checklist and add no-mojibake assertions on high-traffic panels.

## Acceptance Gates

- [x] Frontend tests pass with readable Chinese expectations.
- [x] Source scan finds no mojibake in frontend production source.
- [x] Workspace shows a learning loop before the upload, Q&A, and study tools panels.
- [x] User guide explains how to use the learning loop.

## Follow-up

The next recommended iteration is I-011 Document Library Power User Mode: add search, status filters, sorting, batch retry, duplicate warning, and tags or chapters for heavy document libraries.
