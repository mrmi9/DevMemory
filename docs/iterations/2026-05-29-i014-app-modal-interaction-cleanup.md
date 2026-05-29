# 2026-05-29 I-014 App Modal Interaction Cleanup

## Goal

Replace browser-native prompt and confirm interactions with consistent in-app modals.

## Optimization Direction

Product UX and professional polish. This iteration removes the roughest remaining MVP interaction pattern from the main learning workflow: editing, renaming, and destructive actions now happen inside DevMemory's own UI.

## Scope

- Add a reusable `AppModal` component with confirm, cancel, loading, danger, and inline error states.
- Rename chat sessions in an app modal.
- Edit study cards in an app modal.
- Edit generated questions in an app modal.
- Confirm destructive deletes for courses, documents, chat sessions, study cards, generated questions, wrong notes, and mind maps in app modals.
- Keep existing API behavior unchanged.

Deferred:

- Full keyboard focus trapping and escape-key handling.
- A global modal manager.
- Bulk editing flows for tags, chapters, or study assets.

## Markdown Updates

- `docs/iterations/2026-05-29-i014-app-modal-interaction-cleanup.md`
- `docs/professional-release-roadmap.md`
- `docs/user-guide.md`

## Acceptance Gates

- `cd frontend && npm.cmd test`
- `cd frontend && npm.cmd run build`
- `cd backend && ..\.venv\Scripts\python.exe -m pytest tests`
- `rg -n "window\.prompt|window\.confirm|prompt\(|confirm\(" frontend\src --glob "!*.test.ts"` returns no production hits.
- Mojibake scan on production frontend/docs returns no hits.
- `git diff --check`

## Follow-up

Next recommended iteration: I-015 Spaced Review Engine. The next product step is to make review scheduling smarter by adding next-review dates and review history instead of treating mastery as a simple manual score.
