# Professional Release Roadmap

This document defines how DevMemory moves from a runnable private MVP into a professional private-deployment release.

## Iteration Rule

Every professional-release iteration must record:

- Iteration goal: the concrete release capability being improved.
- Optimization direction: the product, engineering, security, operations, or documentation axis being advanced.
- Scope: what is included and what is intentionally deferred.
- Markdown updates: which `.md` files were created or changed.
- Acceptance gates: commands, smoke checks, or manual checks that prove the iteration is usable.
- Follow-up: the next most valuable iteration.

If an iteration changes behavior or release operations without updating the related Markdown files, it is incomplete.

## Release Target

DevMemory v1.0 targets local or intranet private deployment through Docker Compose. It is intended for personal use or small trusted teams.

Out of scope for v1.0:

- Public SaaS hosting.
- Billing and subscriptions.
- Multi-tenant administration.
- Organization roles and permissions.
- External object storage by default.

## Iteration Tracks

| Track | Goal | Current State | Next Direction |
| --- | --- | --- | --- |
| Deployment | Make private deployment repeatable | Production compose and env template exist | Validate upgrade and rollback flows |
| Quality | Prevent regressions before release | Backend, frontend, Docker CI exist | Add deeper E2E and migration checks |
| Observability | Make runtime state diagnosable | `/api/system/status` exists | Add worker heartbeat and clearer job metrics |
| Security | Reduce private deployment risk | Production defaults are rejected | Add rate limits, token rotation, upload size limits |
| Data Safety | Protect user documents and database | Backup/restore docs exist | Add scripted backup/restore helpers |
| UX | Make workflows self-explanatory | User guide and AI mode indicator exist | Improve empty/error states and onboarding |
| AI Quality | Improve answer reliability | RAG citations and model config exist | Add prompt/version evaluation cases |
| Documentation | Keep release knowledge current | Deployment, user, backup, checklist docs exist | Maintain iteration records and release notes |

## Planned Iterations

### I-001 Private Deployment Foundation

Goal: make DevMemory deployable as a local/private release candidate.

Status: completed.

Record: [2026-05-29 I-001 Private Deployment Foundation](iterations/2026-05-29-i001-private-deployment-foundation.md)

### I-002 Release Governance and Iteration Discipline

Goal: make every future release iteration explicit, reviewable, and tied to Markdown updates.

Status: current.

Record: [2026-05-29 I-002 Release Governance](iterations/2026-05-29-i002-release-governance.md)

### I-003 Operations Hardening

Goal: turn backup, restore, upgrade, and rollback from documentation-only flows into runnable scripts with smoke verification.

Default scope:

- Add backup and restore helper scripts.
- Add restore verification steps.
- Document rollback from a failed upgrade.
- Keep single-machine Docker Compose as the release target.

### I-004 Security Hardening

Goal: reduce risk for private-network deployments.

Default scope:

- Add upload size limits and clear errors.
- Add login and AI request rate limiting.
- Add token expiry configuration and logout support.
- Document secret rotation.

### I-005 Product Onboarding and UX Quality

Goal: make the first-run experience understandable without developer guidance.

Default scope:

- Improve empty states and first-course guidance.
- Add visible system status explanations.
- Add user-facing troubleshooting notes for offline AI mode and failed ingestion.
- Add focused frontend tests for first-run flows.

## Release Gate

A release candidate can be tagged only when:

- The active iteration record marks all acceptance gates complete.
- [release-checklist.md](release-checklist.md) passes.
- A smoke test has created and deleted a temporary course successfully.
- Relevant Markdown files have been updated for the changed behavior.
- `main` is clean and pushed.
