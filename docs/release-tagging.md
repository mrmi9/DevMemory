# Release Tagging

Use this guide after the release rehearsal and restore drill have produced current evidence.

## Readiness Check

Run the tag readiness check from the repository root:

```powershell
python scripts\release_tag_check.py --version v1.0.0
```

The check verifies:

- The version uses `vMAJOR.MINOR.PATCH`.
- The Git workspace is clean.
- `docs/release-notes/v1.0.0.md` exists.
- Release notes include deployment notes, verification evidence, known risks, and deferred v1.1 work.
- The release checklist references the release notes and version.
- The roadmap marks I-008 completed.
- The I-008 iteration record exists.
- `release-evidence/restore-drill.md` exists and records operator, environment, start time, restore result, and smoke result.

## Tag Command

Only create the tag after all checklist items pass and `main` has been pushed:

```powershell
git tag -a v1.0.0 -m "DevMemory v1.0.0"
git push origin v1.0.0
```

Do not tag from a dirty worktree or from a commit that has not passed GitHub Actions.

## Evidence To Archive

Keep these artifacts with the release record:

- `release-evidence/release-candidate-rehearsal.md`.
- `release-evidence/restore-drill.md`.
- GitHub Actions run URL.
- Clean-environment restore notes.
- Any manual AI quality review notes.
- The commit SHA used for the tag.
