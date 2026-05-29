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

## Upload Materials

1. Select a course.
2. Use the course library upload area.
3. Upload PDF, Word, Markdown, or image notes.
4. Wait for the ingestion job to finish.

When the worker completes, the document status becomes ready and chunks become available for retrieval.

## Ask Questions

Use the knowledge-base Q&A panel after documents are ready.

Good questions:

- Summarize this chapter.
- What are the exam points for SNMP?
- Compare two concepts from the uploaded notes.

Answers include source citations when relevant chunks are found.

## Generate Learning Materials

Use the study materials panel to generate:

- Review cards.
- Practice questions.
- Wrong-note analysis.

Cards can be edited, deleted, and marked with mastery progress.

## Generate Mind Maps

Enter a topic in the mind map panel. DevMemory stores generated mind maps under the active course so they can be reopened or deleted later.

## Track Progress

The progress panel summarizes courses, tracked records, and average mastery. Updating card mastery refreshes progress.

## Delete Data

Course, document, chat, card, question, wrong-note, and mind-map deletion controls are destructive. Confirm prompts should be read carefully. Deleting a course also deletes its documents and learning records.
