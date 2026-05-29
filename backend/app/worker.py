import time
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import SessionLocal, create_all
from app.models import Document, DocumentChunk, IngestionJob
from app.services.chunking import chunk_text
from app.services.document_parser import parse_document_text
from app.services.embeddings import HashEmbeddingProvider


def process_next_job(db: Session) -> bool:
    job = (
        db.query(IngestionJob)
        .filter(IngestionJob.status.in_(["queued", "failed"]))
        .order_by(IngestionJob.created_at.asc())
        .first()
    )
    if not job:
        return False

    document = db.get(Document, job.document_id)
    if not document:
        job.status = "failed"
        job.error_message = "Document not found"
        db.commit()
        return True

    try:
        job.status = "processing"
        job.progress = 10
        document.status = "processing"
        db.commit()

        text = parse_document_text(Path(document.file_path), document.kind)
        document.extracted_text = text
        job.progress = 45
        db.commit()

        chunks = chunk_text(text)
        provider = HashEmbeddingProvider()
        vectors = provider.embed([chunk.text for chunk in chunks])
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()
        for chunk, vector in zip(chunks, vectors):
            db.add(
                DocumentChunk(
                    user_id=document.user_id,
                    course_id=document.course_id,
                    document_id=document.id,
                    chunk_index=chunk.index,
                    text=chunk.text,
                    token_count=len(chunk.text),
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                    embedding=vector,
                )
            )
        document.status = "ready"
        job.status = "succeeded"
        job.progress = 100
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.get(IngestionJob, job.id)
        document = db.get(Document, document.id)
        if job:
            job.status = "failed"
            job.retry_count += 1
            job.error_message = str(exc)
        if document:
            document.status = "failed"
            document.error_message = str(exc)
        db.commit()
    return True


def run_forever(poll_seconds: int = 3) -> None:
    create_all()
    while True:
        with SessionLocal() as db:
            worked = process_next_job(db)
        if not worked:
            time.sleep(poll_seconds)


if __name__ == "__main__":
    run_forever()
