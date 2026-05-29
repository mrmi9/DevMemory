# AI Quality and Retrieval Confidence

DevMemory answers are retrieval-augmented: the backend retrieves document chunks, builds a RAG prompt, calls DeepSeek, and returns citations. I-006 adds an explicit retrieval-confidence signal so operators and users can tell whether an answer is well grounded before trusting it.

## Confidence Levels

| Level | Meaning | User action |
| --- | --- | --- |
| `high` | Multiple relevant chunks were retrieved and the strongest match is high. | Review citations and use the answer as a study aid. |
| `medium` | The strongest match is useful but context is limited or only one strong chunk was found. | Check the cited text before relying on the conclusion. |
| `weak` | Retrieved context is low similarity. | Upload or select more relevant documents, then ask again. |
| `none` | No chunks were retrieved. | Upload materials and wait for parsing before asking. |

The confidence score is not a truth score for the model output. It only describes retrieval grounding.

## Release Evaluation Fixtures

Deterministic fixture cases live in:

```text
backend/tests/fixtures/ai_quality_cases.json
```

They cover:

- No retrieved context.
- Weak single-context retrieval.
- Grounded multi-context retrieval.

Run the quality checks with:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest tests\test_ai_quality.py tests\test_rag_prompt.py tests\test_rag_retrieval.py
```

## Operator Acceptance

Before a private release, validate at least one representative course:

1. Upload a small known document set.
2. Ask three questions whose answers are present in the documents.
3. Confirm each answer shows citations and `high` or `medium` retrieval confidence.
4. Ask one question that is not covered by the documents.
5. Confirm the answer or UI makes the missing-context state clear.
6. Check that cited previews actually support the answer.

If confidence is repeatedly `weak` or `none`, improve the source documents, chunking, or embedding provider before distributing the release.

## Limits

- Confidence uses retrieved chunk count and similarity, not a separate model judge.
- Hash embeddings are acceptable for local development, but production operators should evaluate a real embedding provider before relying on answer quality.
- The model can still make mistakes. Citations and confidence are review aids, not a guarantee.
