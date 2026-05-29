# AI Personal Study Knowledge Base

This project is a runnable first version of an AI-powered personal study platform. It includes a Vue workspace, FastAPI backend, PostgreSQL/pgvector schema, document ingestion worker, DeepSeek API adapter, and pluggable embedding provider.

## Features

- Upload PDF, Word, Markdown, and image notes by course.
- Parse, clean, chunk, embed, and store document content through a database-backed worker.
- Ask course-scoped questions with cited source chunks.
- Generate review cards, exam questions, wrong-note analysis, and Markmap mind maps.
- Track learning progress with a schema that can grow from single-user to multi-user.

## Docker Start

1. Edit `.env` and set at least `STUDY_ACCESS_TOKEN_SECRET`.
2. Add `STUDY_DEEPSEEK_API_KEY` if you want real AI generation instead of offline placeholder responses.
3. Start the stack:

```powershell
docker compose up --build
```

4. Open `http://localhost:5173`.

Default credentials come from `.env`:

- `STUDY_DEFAULT_USERNAME`
- `STUDY_DEFAULT_PASSWORD`

## Local Development

Core backend dependencies, without the optional OCR stack:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Optional image OCR dependencies:

```powershell
.venv\Scripts\python.exe -m pip install -r backend\requirements-ocr.txt
```

PaddleOCR is heavy and is most reliable in the Docker image, which uses Python 3.12. On local Python 3.14, OCR dependencies may not install cleanly.

Frontend dependencies:

```powershell
cd frontend
npm.cmd install
npm.cmd run build
```

## Structure

- `backend/app/services`: parsing, chunking, embedding, RAG prompt, and DeepSeek calls.
- `backend/app/api/routes.py`: first-version REST API.
- `backend/app/worker.py`: database job worker for parsing and embedding.
- `frontend/src/components`: course, upload, chat, study generation, mind map, and progress UI.
- `infra/postgres/init.sql`: enables the pgvector extension.

## Notes

- The default `HashEmbeddingProvider` is a lightweight local development implementation. Replace it with BGE-M3 or a cloud embedding provider by implementing `EmbeddingProvider.embed(texts)`.
- If `STUDY_DEEPSEEK_API_KEY` is empty, the backend returns offline placeholder text so upload, parsing, and retrieval flows can be tested first.
- The embedding provider is selected with `STUDY_EMBEDDING_PROVIDER`. The default `hash` mode is local and deterministic. To use an OpenAI-compatible embedding endpoint, set:
  - `STUDY_EMBEDDING_PROVIDER=openai`
  - `STUDY_EMBEDDING_API_KEY=<your key>`
  - `STUDY_EMBEDDING_BASE_URL=https://api.openai.com/v1` or another compatible `/v1` endpoint
  - `STUDY_EMBEDDING_MODEL=text-embedding-3-small` or a model with the same vector dimension as `STUDY_EMBEDDING_DIMENSIONS`
- Production mode is enabled with `STUDY_ENVIRONMENT=production`. In production, startup refuses unsafe defaults for `STUDY_ACCESS_TOKEN_SECRET`, `STUDY_DEFAULT_PASSWORD`, and wildcard `STUDY_CORS_ORIGINS`.
- Configure browser origins with `STUDY_CORS_ORIGINS`, for example `["https://study.example.com"]`.
- The backend exposes `GET /health` for container and load-balancer health checks.
- Docker Desktop and the Docker CLI are required for `docker compose up --build`.
