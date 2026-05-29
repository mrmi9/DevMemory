# 2026-05-29 I-004 Security Hardening

## Iteration Goal

Reduce operational and data-exposure risk for DevMemory private deployments before the v1.0 release candidate.

## Optimization Direction

Security and product hardening:

- Make token lifetime, upload size, and rate limits explicit production settings.
- Prevent large uploads from being accepted silently.
- Slow down repeated login attempts and expensive AI generation requests.
- Give users a visible logout path that clears local state.
- Document the security model and its v1.0 limits.

## Scope

Included:

- `STUDY_ACCESS_TOKEN_TTL_MINUTES`
- `STUDY_MAX_UPLOAD_BYTES`
- `STUDY_LOGIN_RATE_LIMIT_PER_MINUTE`
- `STUDY_AI_RATE_LIMIT_PER_MINUTE`
- In-memory login and AI request rate limiting.
- Upload streaming with HTTP `413` for oversized files.
- Client-side logout.
- Security-focused backend and frontend tests.

Deferred:

- Password-change UI.
- Server-side token revocation list.
- Distributed rate limiting across multiple backend replicas.
- Multi-user roles and permissions.

## Markdown Updates

- Added [security-hardening.md](../security-hardening.md).
- Updated [professional-release-roadmap.md](../professional-release-roadmap.md).
- Updated [release-checklist.md](../release-checklist.md).
- Updated [README.md](../../README.md).
- Updated `.env.production.example`.

## Acceptance Gates

- Backend targeted security tests:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest tests\test_security_hardening.py tests\test_security_config.py::test_security_hardening_defaults_are_configurable
```

- Frontend targeted logout/status test:

```powershell
cd frontend
npm.cmd test -- LoginBar.test.ts
```

- Full release verification:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest tests
```

```powershell
cd frontend
npm.cmd test
npm.cmd run build
```

```powershell
python scripts\smoke_test.py --base-url http://127.0.0.1:5173/api
```

## Follow-Up

I-005 should improve onboarding and UX quality: first-run guidance, empty states, clearer offline AI messaging, and failed-ingestion troubleshooting.
