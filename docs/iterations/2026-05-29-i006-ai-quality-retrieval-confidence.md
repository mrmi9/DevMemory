# 2026-05-29 I-006 AI Quality and Retrieval Confidence

## Iteration

- ID: I-006
- Date: 2026-05-29
- Status: completed
- Owner: Codex

## Goal

Make answer quality easier to evaluate before a private release by exposing retrieval grounding and adding deterministic quality fixtures.

## Optimization Direction

AI Quality.

## Scope

Included:

- Retrieval confidence evaluation for chat answers.
- `retrieval_confidence` and `quality_notes` in chat responses.
- Frontend display of retrieval confidence and quality notes under assistant answers.
- Deterministic AI quality fixture cases for no-context, weak-context, and grounded-context scenarios.
- Documentation for DeepSeek/RAG release validation.

Deferred:

- LLM-as-judge scoring.
- Per-model benchmark dashboards.
- Embedding-provider migration or re-indexing workflow.
- Citation sentence-level verification.

## Markdown Updates

- Added [ai-quality.md](../ai-quality.md).
- Updated [professional-release-roadmap.md](../professional-release-roadmap.md).
- Updated [release-checklist.md](../release-checklist.md).
- Updated [user-guide.md](../user-guide.md).
- Updated [README.md](../../README.md).
- Added this iteration record.

## Implementation Notes

- Retrieval confidence is computed from retrieved chunk count and similarity.
- `none` means no chunks were found.
- `weak` means retrieved chunks are too low similarity to trust without more material.
- `medium` means context exists but should be checked carefully.
- `high` means multiple relevant chunks are available.

## Acceptance Gates

- [x] Backend tests pass: `63 passed`.
- [x] Frontend tests pass: `17 passed`.
- [x] Frontend build passes: `npm.cmd run build`.
- [x] Smoke test passes: `{"ok": true, "base_url": "http://127.0.0.1:5173/api", "ai_mode": "online"}`.
- [x] Documentation links and commands match the implementation.

## Result

I-006 is ready to commit after final git review. The next recommended iteration is I-007 Release Candidate Rehearsal.
