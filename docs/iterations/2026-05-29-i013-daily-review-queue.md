# 2026-05-29 I-013 Daily Review Queue

## Goal

Turn review from manual mastery editing into a daily task users can start from the progress panel.

## Optimization Direction

Product UX and learning retention. This iteration makes the final part of the upload-to-review loop visible: after users create cards and wrong notes, DevMemory now tells them what to review today.

## Scope

Delivered:

- Extend progress overview with a daily review queue.
- Count today’s due cards, low-mastery cards, and mastered cards.
- Prioritize cards with mastery below 4, sorted by lowest mastery first.
- Show recent wrong notes alongside due cards.
- Add four review outcomes from the progress panel: `忘记`, `模糊`, `掌握`, and `简单`.
- Refresh progress through the existing store notification path after a review action.

Deferred:

- True spaced-repetition scheduling with persisted due dates.
- Per-course review goals and streaks.
- Modal cleanup for card editing, question editing, and destructive confirmations.

## Markdown Updates

- `README.md`
- `docs/user-guide.md`
- `docs/professional-release-roadmap.md`
- `docs/iterations/2026-05-29-i013-daily-review-queue.md`

## Acceptance Gates

- `cd backend && E:\DevMemory\.venv\Scripts\python.exe -m pytest tests\test_study_routes.py`
- `cd frontend && npm.cmd test -- ProgressPanel.test.ts`
- `cd backend && E:\DevMemory\.venv\Scripts\python.exe -m pytest tests`
- `cd frontend && npm.cmd test`
- `cd frontend && npm.cmd run build`

## Follow-Up

Next recommended iteration: I-014 App Modal Interaction Cleanup. The remaining major experience gap is replacing browser-native `prompt` and `confirm` with consistent in-app modals for editing and destructive actions.
