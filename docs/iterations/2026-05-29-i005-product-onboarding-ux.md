# 2026-05-29 I-005 Product Onboarding and UX Quality

## Iteration

- ID: I-005
- Date: 2026-05-29
- Status: completed
- Owner: Codex

## Goal

Make first-run and common blocked states understandable without developer guidance.

## Optimization Direction

UX and documentation.

## Scope

Included:

- First-course empty state in the course panel.
- Knowledge-base Q&A guidance when no searchable documents are ready.
- Disabled ask action until a course and searchable document chunks exist.
- Clear "資料不足" citation fallback when an answer has no citations.
- Parsing failure troubleshooting guidance in the document detail view.
- Focused frontend tests for the new onboarding and blocked-state behavior.

Deferred:

- Full multi-step onboarding wizard.
- Browser-based visual tour.
- Per-user preference persistence for dismissed tips.
- Backend changes to document failure taxonomy.

## Markdown Updates

- Updated [user-guide.md](../user-guide.md).
- Updated [professional-release-roadmap.md](../professional-release-roadmap.md).
- Updated [release-checklist.md](../release-checklist.md).
- Added this iteration record.

## Implementation Notes

- The UI keeps the existing operational layout and adds contextual empty states instead of a separate landing screen.
- Q&A now requires at least one searchable document with chunks, which keeps retrieval-based answers aligned with the product promise.
- Failed ingestion details show the worker error and a practical retry/re-upload path.

## Acceptance Gates

- [x] Backend tests pass: `61 passed`.
- [x] Frontend tests pass: `17 passed`.
- [x] Frontend build passes: `npm.cmd run build`.
- [x] Smoke test passes: `{"ok": true, "base_url": "http://127.0.0.1:5173/api", "ai_mode": "online"}`.
- [x] Documentation links and commands match the implementation.

## Result

I-005 is ready to commit after final git review. The next recommended iteration is I-006 AI Quality and Retrieval Confidence.
