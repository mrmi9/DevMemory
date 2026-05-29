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
| Deployment | Make private deployment repeatable | Production compose, ops scripts, release rehearsal, and restore evidence gate exist | Keep deployment docs aligned with product changes |
| Quality | Prevent regressions before release | Backend, frontend, Docker CI, smoke, rehearsal, and tag readiness gates exist | Keep release notes current for each tag |
| Observability | Make runtime state diagnosable | `/api/system/status` exists | Add worker heartbeat and clearer job metrics |
| Security | Reduce private deployment risk | Token TTL, upload limits, rate limits, and logout exist | Add password-change flow and token revocation strategy |
| Data Safety | Protect user documents and database | Backup/restore scripts and clean restore evidence gate exist | Preserve restore evidence during release tagging |
| UX | Make workflows self-explanatory | Chinese UX copy restored and guided learning loop exists | Add document-library power-user controls |
| AI Quality | Improve answer reliability | Retrieval confidence and quality fixtures exist | Add model-output evaluation reports |
| Documentation | Keep release knowledge current | Deployment, user, backup, checklist, tagging, restore evidence, and release notes docs exist | Keep docs current while product features evolve |

## Planned Iterations

### I-001 Private Deployment Foundation

Goal: make DevMemory deployable as a local/private release candidate.

Status: completed.

Record: [2026-05-29 I-001 Private Deployment Foundation](iterations/2026-05-29-i001-private-deployment-foundation.md)

### I-002 Release Governance and Iteration Discipline

Goal: make every future release iteration explicit, reviewable, and tied to Markdown updates.

Status: completed.

Record: [2026-05-29 I-002 Release Governance](iterations/2026-05-29-i002-release-governance.md)

### I-003 Operations Hardening

Goal: turn backup, restore, upgrade, and rollback from documentation-only flows into runnable scripts with smoke verification.

Status: completed.

Record: [2026-05-29 I-003 Operations Hardening](iterations/2026-05-29-i003-operations-hardening.md)

Delivered scope:

- Add backup and restore helper scripts.
- Add restore verification steps.
- Document rollback from a failed upgrade.
- Keep single-machine Docker Compose as the release target.

### I-004 Security Hardening

Goal: reduce risk for private-network deployments.

Status: completed.

Record: [2026-05-29 I-004 Security Hardening](iterations/2026-05-29-i004-security-hardening.md)

Delivered scope:

- Add upload size limits and clear `413` errors.
- Add login and AI request rate limiting.
- Add token expiry configuration and logout support.
- Document secret rotation and v1.0 security boundaries.

### I-005 Product Onboarding and UX Quality

Goal: make the first-run experience understandable without developer guidance.

Status: completed.

Record: [2026-05-29 I-005 Product Onboarding and UX Quality](iterations/2026-05-29-i005-product-onboarding-ux.md)

Delivered scope:

- Improve empty states and first-course guidance.
- Make Q&A explain when documents are not ready for retrieval.
- Add user-facing troubleshooting notes for failed ingestion.
- Add focused frontend tests for first-run flows.

### I-006 AI Quality and Retrieval Confidence

Goal: make answer quality easier to evaluate before a private release.

Status: completed.

Record: [2026-05-29 I-006 AI Quality and Retrieval Confidence](iterations/2026-05-29-i006-ai-quality-retrieval-confidence.md)

Delivered scope:

- Add prompt and citation evaluation fixtures.
- Add deterministic retrieval tests for weak/no context cases.
- Document how operators should validate DeepSeek output before release.

### I-007 Release Candidate Rehearsal

Goal: prove the private deployment can be installed, upgraded, backed up, restored, and smoke-tested from a clean environment.

Status: completed.

Record: [2026-05-29 I-007 Release Candidate Rehearsal](iterations/2026-05-29-i007-release-candidate-rehearsal.md)

Delivered scope:

- Add a repeatable release rehearsal command.
- Generate ignored Markdown evidence reports under `release-evidence/`.
- Rebuild Docker and smoke-test through the frontend proxy.
- Document the manual clean-environment backup/restore drill.

### I-008 Release Notes and Tagging Preparation

Goal: prepare the project for an auditable v1.0 release tag.

Status: completed.

Record: [2026-05-29 I-008 Release Notes and Tagging Preparation](iterations/2026-05-29-i008-release-notes-tagging.md)

Delivered scope:

- Add release notes template and v1.0 draft notes.
- Add tag readiness checks.
- Document remaining release risks and deferred v1.1 items.

### I-009 Clean Restore Drill Evidence

Goal: prove that a release backup can be restored in a clean environment before the v1.0 tag is created.

Status: completed.

Record: [2026-05-29 I-009 Clean Restore Drill Evidence](iterations/2026-05-29-i009-clean-restore-drill-evidence.md)

Delivered scope:

- Add a restore drill evidence report command.
- Require restore evidence during tag readiness checks.
- Document restore evidence archival outside Git.
- Update the v1.0 release notes with the restore evidence gate.

### I-010 Chinese UX Recovery and First-Run Workflow Polish

Goal: restore trustworthy Chinese UI text and improve the user-visible learning workflow now that v1.0 release operations are gated.

Status: completed.

Record: [2026-05-29 I-010 Chinese UX Recovery and First-Run Workflow Polish](iterations/2026-05-29-i010-chinese-ux-workflow-polish.md)

Delivered scope:

- Recover readable UTF-8 Chinese copy in the main frontend workspace.
- Add a guided learning loop for course creation, upload, parsing, first question, generated assets, review, and weakness review.
- Add frontend tests that guard against common mojibake in high-traffic panels.
- Update user-facing documentation.

### I-011 Document Library Power User Mode

Goal: make heavy document libraries manageable for users who upload many files.

Default scope:

- Add document search.
- Add status filters for parsing, failed, and searchable documents.
- Add sorting by type, status, and upload time.
- Add batch retry for failed documents.
- Add duplicate file warning and lightweight tags or chapter grouping.

## Release Gate

A release candidate can be tagged only when:

- The active iteration record marks all acceptance gates complete.
- [release-checklist.md](release-checklist.md) passes.
- A smoke test has created and deleted a temporary course successfully.
- Relevant Markdown files have been updated for the changed behavior.
- `main` is clean and pushed.
