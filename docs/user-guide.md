# DevMemory User Guide

DevMemory is a private AI study knowledge base. It organizes courses, uploaded notes, retrieval-based Q&A, review cards, generated questions, wrong notes, mind maps, and progress.

## Log In

Open:

```text
http://localhost:5173
```

Use the username and password from `.env` or `.env.production`.

The login bar shows the current AI mode:

- Online AI mode: DeepSeek is configured.
- Offline placeholder AI mode: DeepSeek is not configured, so AI responses are placeholders.

## Create a Course

1. Enter a course name.
2. Add a short description.
3. Click the create course button.

The new course becomes the active course.

If this is the first time using DevMemory, the course panel explains that the first step is creating a course. All later materials, Q&A, study assets, mind maps, and progress are grouped under the active course.

## Follow the Learning Loop

The workspace shows a course-level learning loop so you always know the next useful action:

1. Create a course.
2. Upload materials.
3. Wait for parsing to complete.
4. Ask the first knowledge-base question.
5. Generate review cards or practice questions.
6. Complete one review by adjusting card mastery.
7. Review weak areas from low-mastery cards and recent wrong notes.

The loop updates as documents become searchable, chat sessions are created, and study cards are reviewed.

## Upload Materials

1. Select a course.
2. Use the course library upload area.
3. Upload PDF, Word, Markdown, or image notes.
4. Wait for the ingestion job to finish.

When the worker completes, the document status becomes ready and chunks become available for retrieval.

If parsing fails, open the document detail view. DevMemory shows the worker error, a retry action, and troubleshooting guidance. Start with retry; if it fails again, check whether the source file is damaged, scanned too poorly for OCR, or better replaced with a clean PDF, Word, Markdown, or image note.

For larger courses, use the document library controls to keep the material set manageable:

- Search by filename, file type, or parsed preview text.
- Filter by all documents, searchable documents, parsing documents, or failed documents.
- Sort by newest upload, oldest upload, file type, or parsing status.
- Retry all failed documents in one batch after fixing worker or source-file issues.
- Watch for duplicate filename warnings before uploading another copy of the same material.
- Open a document and save a chapter name plus tags such as `重点`, `真题`, or `实验`; these labels are searchable and stay with the document after refresh or deployment restart.

## Ask Questions

Use the knowledge-base Q&A panel after documents are ready.

The ask button is available after a course is selected and at least one uploaded document has searchable chunks. If the panel says there are no searchable materials yet, upload a document and wait for parsing to finish.

Good questions:

- Summarize this chapter.
- What are the exam points for SNMP?
- Compare two concepts from the uploaded notes.

Answers include source citations when relevant chunks are found.

If an answer has no citations, treat it as a signal that the selected materials are insufficient. Upload more relevant notes or narrow the document filter before asking again.

Assistant answers also show retrieval confidence:

- `high`: the answer has multiple relevant chunks.
- `medium`: context exists but should be checked against the citations.
- `weak` or `none`: upload or choose more relevant materials before trusting the answer.

When an answer has citations, use the answer actions to continue the learning loop:

- Save the answer as a review card.
- Generate five practice questions from the answer.
- Add the answer to wrong notes or key points.
- Start a follow-up question from that answer.
- Switch the question scope to only the cited documents before asking again.

Answers without citations do not show study-asset actions, so low-context output is not silently added to the review set.

## Generate Learning Materials

Use the study materials panel to generate:

- Review cards.
- Practice questions.
- Wrong-note analysis.

Cards can be edited, deleted, and marked with mastery progress.

## Generate Mind Maps

Enter a topic in the mind map panel. DevMemory stores generated mind maps under the active course so they can be reopened or deleted later.

## Track Progress

The progress panel summarizes courses, tracked records, and average mastery. It also shows a daily review queue:

- Today’s due cards.
- Low-mastery card count.
- Mastered card count.
- Recent wrong notes.

Use the four review outcomes on each due card:

- `忘记`: set mastery low and keep it in review.
- `模糊`: mark partial recall.
- `掌握`: mark the card as learned.
- `简单`: mark the card as easy.

Updating a review card refreshes progress and the learning loop.

Use the learning loop and progress panel together: the loop tells you what to do next, while progress shows whether your review activity is producing mastery records.

## Delete Data

Course, document, chat, card, question, wrong-note, and mind-map deletion controls are destructive. DevMemory shows an in-app confirmation modal before these actions, with the affected item and the impact of deletion. Deleting a course also deletes its documents and learning records.

Editing chat session titles, review cards, and generated questions also happens in app modals so changes can be reviewed before saving.
