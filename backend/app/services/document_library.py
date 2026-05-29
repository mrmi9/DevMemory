from typing import Any


def serialize_document_card(document: Any, latest_job: Any | None, chunk_count: int) -> dict[str, Any]:
    return {
        "id": document.id,
        "course_id": document.course_id,
        "title": document.title,
        "original_filename": document.original_filename,
        "kind": document.kind,
        "status": document.status,
        "error_message": document.error_message or "",
        "text_preview": _preview_text(getattr(document, "extracted_text", "") or ""),
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat(),
        "chunk_count": chunk_count,
        "latest_job": _serialize_job(latest_job) if latest_job else None,
    }


def serialize_chunk_row(chunk: Any) -> dict[str, Any]:
    return {
        "id": chunk.id,
        "chunk_index": chunk.chunk_index,
        "text": chunk.text,
        "token_count": chunk.token_count,
        "page_number": chunk.page_number,
        "char_start": chunk.char_start,
        "char_end": chunk.char_end,
    }


def _serialize_job(job: Any) -> dict[str, Any]:
    return {
        "id": job.id,
        "status": job.status,
        "progress": job.progress,
        "error_message": job.error_message or "",
    }


def _preview_text(text: str, limit: int = 500) -> str:
    compact = text.strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."
