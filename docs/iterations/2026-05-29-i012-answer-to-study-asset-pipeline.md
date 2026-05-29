# 2026-05-29 I-012 Answer-to-Study Asset Pipeline

## Goal

Let cited Q&A answers become durable study assets without manual copying.

## Optimization Direction

Product UX and learning workflow. This iteration connects the knowledge-base Q&A panel to review cards, generated questions, and wrong-note/key-point capture.

## Scope

Delivered:

- Add backend endpoints that convert a cited assistant message into:
  - a review card,
  - generated practice questions,
  - a wrong-note/key-point record.
- Include citation source titles in created assets where useful.
- Return the assistant message ID from Q&A so newly generated answers can be acted on immediately.
- Hide study-asset actions for answers without citations and reject no-citation asset creation at the API layer.
- Add frontend actions for saving a cited answer as a card, generating five practice questions, adding the answer to key points, starting a follow-up, and reusing cited documents as the next ask scope.

Deferred:

- A richer card-edit modal before saving remains part of the modal/interaction cleanup track.
- Automated quality scoring beyond citation presence and retrieval confidence remains part of later AI quality work.

## Markdown Updates

- `README.md`
- `docs/user-guide.md`
- `docs/professional-release-roadmap.md`
- `docs/iterations/2026-05-29-i012-answer-to-study-asset-pipeline.md`

## Acceptance Gates

- `cd backend && ..\.venv\Scripts\python.exe -m pytest tests\test_chat_routes.py`
- `cd frontend && npm.cmd test -- ChatPanel.test.ts`
- `cd backend && ..\.venv\Scripts\python.exe -m pytest tests`
- `cd frontend && npm.cmd test`
- `cd frontend && npm.cmd run build`

## Follow-Up

Next recommended iteration: I-013 Daily Review Queue. The next product step is to turn created cards and wrong notes into a daily review task instead of leaving review as manual mastery editing.
