# 2026-05-29 I-011 Document Library Power User Mode

## Goal

Make the course document library manageable for users who upload many materials before asking questions or generating review assets.

## Optimization Direction

Product UX. This iteration improves the upload-to-retrieval part of the main learning loop so heavy users can find, inspect, and repair document ingestion state without leaving the workspace.

## Scope

Delivered:

- Add document search by title, original filename, file type, and parsed preview text.
- Add status filters for all, searchable, parsing, and failed documents.
- Add sorting by newest upload, oldest upload, file type, and parsing status.
- Add a batch retry action for all failed documents in the active course.
- Warn on duplicate filenames before upload so users do not accidentally add the same material twice.
- Keep document selection, deletion, detail preview, chunk preview, job history, and single-document retry behavior intact.

Deferred:

- Persistent tags and chapter grouping need database schema and API changes, so they are deferred to a later feature iteration.
- Application-level modal replacements for destructive confirmations remain part of a later UX iteration.

## Markdown Updates

- `README.md`
- `docs/user-guide.md`
- `docs/professional-release-roadmap.md`
- `docs/iterations/2026-05-29-i011-document-library-power-user-mode.md`

## Acceptance Gates

- `cd frontend && npm.cmd test -- UploadPanel.test.ts`
- `cd frontend && npm.cmd test`
- `cd frontend && npm.cmd run build`
- `cd backend && ..\.venv\Scripts\python.exe -m pytest tests`

## Follow-Up

Next recommended iteration: I-012 Answer-to-Study Asset Pipeline. The next product step is to let cited Q&A answers become cards, practice questions, and wrong-note material without manual copying.
