from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import create_token, ensure_default_user, get_current_user, verify_password
from app.config import get_settings
from app.database import get_db
from app.models import ChatMessage, ChatSession, Course, Document, DocumentChunk, GeneratedQuestion, IngestionJob, Mindmap, ProgressRecord, StudyCard, User, WrongNote
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ChatMessageOut,
    ChatSessionOut,
    ChatSessionUpdate,
    Citation,
    CourseCreate,
    CourseOut,
    CourseUpdate,
    DocumentCardOut,
    DocumentChunkOut,
    DocumentOut,
    DocumentUpdate,
    GeneratedQuestionOut,
    GeneratedQuestionUpdate,
    GenerateRequest,
    GeneratedTextResponse,
    JobOut,
    LoginRequest,
    LoginResponse,
    MindmapOut,
    ProgressUpdate,
    StudyCardMasteryUpdate,
    StudyCardUpdate,
    StudyCardOut,
    WrongNoteRequest,
    WrongNoteOut,
)
from app.services.document_parser import detect_document_kind
from app.services.document_library import serialize_chunk_row, serialize_document_card
from app.services.embeddings import cosine_similarity, get_embedding_provider, vector_values
from app.services.llm import DeepSeekClient
from app.rate_limit import InMemoryRateLimiter
from app.services.rag import RetrievedChunk, build_rag_prompt, evaluate_retrieval_quality
from app.services.study_library import build_wrong_note_from_question, parse_generated_cards, parse_generated_questions, serialize_generated_question_row, serialize_study_card_row, serialize_wrong_note_row
from app.services.study_generation import analyze_wrong_note, generate_cards, generate_mindmap, generate_questions

router = APIRouter()
login_rate_limiter = InMemoryRateLimiter()
ai_rate_limiter = InMemoryRateLimiter()


@router.get("/system/status")
def system_status(request: Request, db: Session = Depends(get_db)):
    settings = getattr(request.app.state, "settings", get_settings())
    checks = {
        "database": _database_status(db),
        "pgvector": _pgvector_status(db),
        "upload_dir": _upload_dir_status(settings.upload_dir),
        "deepseek": {
            "ok": True,
            "configured": bool(settings.deepseek_api_key),
            "mode": "online" if settings.deepseek_api_key else "offline_placeholder",
            "model": settings.deepseek_model,
            "base_url": settings.deepseek_base_url,
        },
        "embedding": {
            "ok": settings.embedding_dimensions == 384,
            "provider": settings.embedding_provider,
            "model": settings.embedding_model,
            "dimensions": settings.embedding_dimensions,
        },
        "worker": _worker_status(db),
    }
    return {
        "status": "ok" if all(item.get("ok") for item in checks.values()) else "degraded",
        "environment": settings.environment,
        "ai_mode": "online" if settings.deepseek_api_key else "offline_placeholder",
        "checks": checks,
    }


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> LoginResponse:
    _enforce_login_rate_limit(request, payload.username)
    user = ensure_default_user(db)
    if payload.username != user.username or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return LoginResponse(access_token=create_token(user.id))


@router.get("/courses", response_model=list[CourseOut])
def list_courses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Course).filter(Course.user_id == user.id).order_by(Course.created_at.desc()).all()


@router.post("/courses", response_model=CourseOut)
def create_course(payload: CourseCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = Course(user_id=user.id, title=payload.title, description=payload.description, color=payload.color)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.patch("/courses/{course_id}", response_model=CourseOut)
def update_course(course_id: str, payload: CourseUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = _get_course(db, user.id, course_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


@router.delete("/courses/{course_id}")
def delete_course(course_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = _get_course(db, user.id, course_id)
    file_paths = _delete_course_related_rows(db, user.id, course_id)
    db.delete(course)
    db.commit()
    for file_path in file_paths:
        _remove_uploaded_file(file_path)
    return {"ok": True}


@router.get("/courses/{course_id}/documents", response_model=list[DocumentCardOut])
def list_course_documents(course_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_course(db, user.id, course_id)
    documents = (
        db.query(Document)
        .filter(Document.user_id == user.id, Document.course_id == course_id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return [_document_card(db, document) for document in documents]


@router.post("/courses/{course_id}/documents", response_model=DocumentCardOut)
async def upload_document(
    course_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_course(db, user.id, course_id)
    settings = get_settings()
    kind = detect_document_kind(file.filename or "upload", file.content_type or "")
    storage_dir = Path(settings.upload_dir) / user.id / course_id
    storage_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4()}{Path(file.filename or 'upload').suffix.lower()}"
    target = storage_dir / filename
    await _write_upload_with_size_limit(file, target, settings.max_upload_bytes)

    document = Document(
        user_id=user.id,
        course_id=course_id,
        title=file.filename or filename,
        original_filename=file.filename or filename,
        content_type=file.content_type or "",
        kind=kind,
        file_path=str(target),
        status="uploaded",
    )
    db.add(document)
    db.flush()
    job = IngestionJob(user_id=user.id, document_id=document.id, status="queued", progress=0)
    db.add(job)
    db.commit()
    db.refresh(document)
    db.refresh(job)
    return _document_card(db, document, job)


@router.get("/documents/{document_id}", response_model=DocumentCardOut)
def get_document(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if not document or document.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return _document_card(db, document)


@router.patch("/documents/{document_id}", response_model=DocumentCardOut)
def update_document_metadata(
    document_id: str,
    payload: DocumentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)
    if not document or document.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    if payload.chapter is not None:
        document.chapter = payload.chapter.strip()
    if payload.tags is not None:
        document.tags = _normalize_document_tags(payload.tags)
    db.commit()
    db.refresh(document)
    return _document_card(db, document)


@router.get("/documents/{document_id}/chunks", response_model=list[DocumentChunkOut])
def list_document_chunks(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if not document or document.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.user_id == user.id, DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )
    return [serialize_chunk_row(chunk) for chunk in chunks]


@router.delete("/documents/{document_id}")
def delete_document(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if not document or document.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = document.file_path
    db.query(DocumentChunk).filter(DocumentChunk.user_id == user.id, DocumentChunk.document_id == document_id).delete(
        synchronize_session=False
    )
    db.query(IngestionJob).filter(IngestionJob.user_id == user.id, IngestionJob.document_id == document_id).delete(
        synchronize_session=False
    )
    db.delete(document)
    db.commit()
    _remove_uploaded_file(file_path)
    return {"ok": True}


@router.post("/documents/{document_id}/retry", response_model=DocumentCardOut)
def retry_document_ingestion(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if not document or document.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    active_job = (
        db.query(IngestionJob)
        .filter(
            IngestionJob.user_id == user.id,
            IngestionJob.document_id == document_id,
            IngestionJob.status.in_(["queued", "processing"]),
        )
        .first()
    )
    if active_job:
        raise HTTPException(status_code=409, detail="Document is already queued or processing")
    document.status = "uploaded"
    document.error_message = ""
    job = IngestionJob(user_id=user.id, document_id=document.id, status="queued", progress=0)
    db.add(job)
    db.commit()
    db.refresh(document)
    db.refresh(job)
    return _document_card(db, document, job)


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.get(IngestionJob, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/documents/{document_id}/jobs", response_model=list[JobOut])
def list_document_jobs(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if not document or document.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return (
        db.query(IngestionJob)
        .filter(IngestionJob.user_id == user.id, IngestionJob.document_id == document_id)
        .order_by(IngestionJob.created_at.desc())
        .all()
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _enforce_ai_rate_limit(request, user)
    chunks = _retrieve_chunks(db, user.id, payload.question, payload.course_id, payload.document_ids)
    retrieval_quality = evaluate_retrieval_quality(chunks)
    prompt = build_rag_prompt(payload.question, chunks)
    answer = await DeepSeekClient().complete(prompt)
    session = _get_or_create_chat_session(db, user.id, payload)
    citations = [
        Citation(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            document_title=chunk.document_title,
            course_title=chunk.course_title,
            text_preview=_citation_preview(chunk.text),
            page_number=chunk.page_number,
            similarity=chunk.similarity,
        )
        for chunk in chunks
    ]
    citation_payload = [citation.model_dump() for citation in citations]
    db.add(ChatMessage(session_id=session.id, role="user", content=payload.question, citations=[]))
    db.add(ChatMessage(session_id=session.id, role="assistant", content=answer, citations=citation_payload))
    db.commit()
    return ChatResponse(
        answer=answer,
        citations=citations,
        session_id=session.id,
        retrieval_confidence=retrieval_quality.confidence,
        quality_notes=retrieval_quality.notes,
    )


@router.get("/chat/sessions", response_model=list[ChatSessionOut])
def list_chat_sessions(course_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(ChatSession).filter(ChatSession.user_id == user.id)
    if course_id:
        query = query.filter(ChatSession.course_id == course_id)
    sessions = query.order_by(ChatSession.created_at.desc()).limit(50).all()
    return [_chat_session_row(session) for session in sessions]


@router.patch("/chat/sessions/{session_id}", response_model=ChatSessionOut)
def rename_chat_session(session_id: str, payload: ChatSessionUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Chat session not found")
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Session title cannot be empty")
    session.title = title
    db.commit()
    db.refresh(session)
    return _chat_session_row(session)


@router.delete("/chat/sessions/{session_id}")
def delete_chat_session(session_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Chat session not found")
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete(synchronize_session=False)
    db.delete(session)
    db.commit()
    return {"ok": True}


@router.get("/chat/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
def list_chat_messages(session_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Chat session not found")
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    return [
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "citations": message.citations,
            "created_at": message.created_at.isoformat(),
        }
        for message in messages
    ]


@router.post("/study/cards", response_model=GeneratedTextResponse)
async def cards(payload: GenerateRequest, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _enforce_ai_rate_limit(request, user)
    context = _context_for_generation(db, user.id, payload.topic, payload.course_id, payload.document_ids)
    content = await generate_cards(payload.topic, context, payload.count)
    for front, back in parse_generated_cards(content):
        db.add(StudyCard(user_id=user.id, course_id=payload.course_id, front=front, back=back))
    db.commit()
    return GeneratedTextResponse(content=content)


@router.get("/study/cards", response_model=list[StudyCardOut])
def list_study_cards(course_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(StudyCard).filter(StudyCard.user_id == user.id)
    if course_id:
        query = query.filter(StudyCard.course_id == course_id)
    cards = query.order_by(StudyCard.created_at.desc()).limit(50).all()
    return [serialize_study_card_row(card) for card in cards]


@router.patch("/study/cards/{card_id}", response_model=StudyCardOut)
def update_study_card_mastery(card_id: str, payload: StudyCardUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    card = db.get(StudyCard, card_id)
    if not card or card.user_id != user.id:
        raise HTTPException(status_code=404, detail="Study card not found")
    if payload.front is not None:
        card.front = payload.front.strip()
    if payload.back is not None:
        card.back = payload.back.strip()
    if payload.mastery is not None:
        card.mastery = payload.mastery
        _upsert_progress_record(
            db=db,
            user_id=user.id,
            course_id=card.course_id,
            item_id=card.id,
            item_type="study_card",
            status=_status_for_mastery(payload.mastery),
            mastery=payload.mastery,
        )
    db.commit()
    db.refresh(card)
    return serialize_study_card_row(card)


@router.delete("/study/cards/{card_id}")
def delete_study_card(card_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    card = db.get(StudyCard, card_id)
    if not card or card.user_id != user.id:
        raise HTTPException(status_code=404, detail="Study card not found")
    db.query(ProgressRecord).filter(
        ProgressRecord.user_id == user.id,
        ProgressRecord.item_type == "study_card",
        ProgressRecord.item_id == card.id,
    ).delete(synchronize_session=False)
    db.delete(card)
    db.commit()
    return {"ok": True}


@router.post("/study/questions", response_model=GeneratedTextResponse)
async def questions(payload: GenerateRequest, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _enforce_ai_rate_limit(request, user)
    context = _context_for_generation(db, user.id, payload.topic, payload.course_id, payload.document_ids)
    content = await generate_questions(payload.topic, context, payload.count)
    for question in parse_generated_questions(content):
        db.add(GeneratedQuestion(user_id=user.id, course_id=payload.course_id, **question))
    db.commit()
    return GeneratedTextResponse(content=content)


@router.get("/study/questions", response_model=list[GeneratedQuestionOut])
def list_generated_questions(course_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(GeneratedQuestion).filter(GeneratedQuestion.user_id == user.id)
    if course_id:
        query = query.filter(GeneratedQuestion.course_id == course_id)
    questions = query.order_by(GeneratedQuestion.created_at.desc()).limit(50).all()
    return [serialize_generated_question_row(question) for question in questions]


@router.patch("/study/questions/{question_id}", response_model=GeneratedQuestionOut)
def update_generated_question(question_id: str, payload: GeneratedQuestionUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    question = db.get(GeneratedQuestion, question_id)
    if not question or question.user_id != user.id:
        raise HTTPException(status_code=404, detail="Generated question not found")
    if payload.prompt is not None:
        question.prompt = payload.prompt.strip()
    if payload.answer is not None:
        question.answer = payload.answer.strip()
    if payload.explanation is not None:
        question.explanation = payload.explanation.strip()
    db.commit()
    db.refresh(question)
    return serialize_generated_question_row(question)


@router.delete("/study/questions/{question_id}")
def delete_generated_question(question_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    question = db.get(GeneratedQuestion, question_id)
    if not question or question.user_id != user.id:
        raise HTTPException(status_code=404, detail="Generated question not found")
    db.delete(question)
    db.commit()
    return {"ok": True}


@router.post("/study/questions/{question_id}/wrong-note", response_model=WrongNoteOut)
def add_generated_question_to_wrong_notes(question_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    question = db.get(GeneratedQuestion, question_id)
    if not question or question.user_id != user.id:
        raise HTTPException(status_code=404, detail="Generated question not found")
    note = WrongNote(user_id=user.id, **build_wrong_note_from_question(question))
    db.add(note)
    db.commit()
    db.refresh(note)
    return serialize_wrong_note_row(note)


@router.post("/study/wrong-notes", response_model=GeneratedTextResponse)
async def wrong_notes(payload: WrongNoteRequest, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _enforce_ai_rate_limit(request, user)
    analysis = await analyze_wrong_note(payload.original_question, payload.user_answer, payload.correct_answer)
    note = WrongNote(
        user_id=user.id,
        course_id=payload.course_id,
        title=payload.title,
        original_question=payload.original_question,
        user_answer=payload.user_answer,
        correct_answer=payload.correct_answer,
        analysis=analysis,
    )
    db.add(note)
    db.commit()
    return GeneratedTextResponse(content=analysis)


@router.get("/study/wrong-notes", response_model=list[WrongNoteOut])
def list_wrong_notes(course_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(WrongNote).filter(WrongNote.user_id == user.id)
    if course_id:
        query = query.filter(WrongNote.course_id == course_id)
    notes = query.order_by(WrongNote.created_at.desc()).limit(50).all()
    return [serialize_wrong_note_row(note) for note in notes]


@router.delete("/study/wrong-notes/{note_id}")
def delete_wrong_note(note_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.get(WrongNote, note_id)
    if not note or note.user_id != user.id:
        raise HTTPException(status_code=404, detail="Wrong note not found")
    db.delete(note)
    db.commit()
    return {"ok": True}


@router.post("/mindmaps", response_model=GeneratedTextResponse)
async def mindmaps(payload: GenerateRequest, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _enforce_ai_rate_limit(request, user)
    context = _context_for_generation(db, user.id, payload.topic, payload.course_id, payload.document_ids)
    markdown = await generate_mindmap(payload.topic, context)
    db.add(Mindmap(user_id=user.id, course_id=payload.course_id, title=payload.topic, markdown=markdown))
    db.commit()
    return GeneratedTextResponse(content=markdown)


@router.get("/mindmaps", response_model=list[MindmapOut])
def list_mindmaps(course_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Mindmap).filter(Mindmap.user_id == user.id)
    if course_id:
        query = query.filter(Mindmap.course_id == course_id)
    rows = query.order_by(Mindmap.created_at.desc()).limit(50).all()
    return [_mindmap_row(row) for row in rows]


@router.delete("/mindmaps/{mindmap_id}")
def delete_mindmap(mindmap_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    mindmap = db.get(Mindmap, mindmap_id)
    if not mindmap or mindmap.user_id != user.id:
        raise HTTPException(status_code=404, detail="Mindmap not found")
    db.delete(mindmap)
    db.commit()
    return {"ok": True}


@router.get("/progress/overview")
def progress_overview(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    courses = db.query(Course).filter(Course.user_id == user.id).all()
    records = db.query(ProgressRecord).filter(ProgressRecord.user_id == user.id).all()
    return {
        "courses": len(courses),
        "records": len(records),
        "average_mastery": round(sum(record.mastery for record in records) / len(records), 2) if records else 0,
        "items": [
            {
                "id": record.id,
                "course_id": record.course_id,
                "item_type": record.item_type,
                "item_id": record.item_id,
                "status": record.status,
                "mastery": record.mastery,
            }
            for record in records
        ],
    }


@router.patch("/progress/items/{item_id}")
def update_progress(
    item_id: str,
    payload: ProgressUpdate,
    course_id: str,
    item_type: str = "manual",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(ProgressRecord)
        .filter(
            ProgressRecord.user_id == user.id,
            ProgressRecord.course_id == course_id,
            ProgressRecord.item_id == item_id,
            ProgressRecord.item_type == item_type,
        )
        .first()
    )
    if not record:
        record = ProgressRecord(user_id=user.id, course_id=course_id, item_id=item_id, item_type=item_type)
        db.add(record)
    record.status = payload.status
    record.mastery = payload.mastery
    db.commit()
    db.refresh(record)
    return {"id": record.id, "status": record.status, "mastery": record.mastery}


async def _write_upload_with_size_limit(file: UploadFile, target: Path, max_bytes: int) -> None:
    total = 0
    try:
        with target.open("wb") as output:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(status_code=413, detail=f"File exceeds maximum upload size of {max_bytes} bytes")
                output.write(chunk)
    except HTTPException:
        target.unlink(missing_ok=True)
        raise
    except OSError as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Failed to store uploaded file") from exc


def _enforce_login_rate_limit(request: Request, username: str) -> None:
    settings = _settings_from_request(request)
    key = f"login:{_client_ip(request)}:{username.strip().lower()}"
    login_rate_limiter.assert_allowed(
        key=key,
        limit=settings.login_rate_limit_per_minute,
        window_seconds=60,
        detail="Too many login attempts",
    )


def _enforce_ai_rate_limit(request: Request, user: User) -> None:
    settings = _settings_from_request(request)
    ai_rate_limiter.assert_allowed(
        key=f"ai:{user.id}",
        limit=settings.ai_rate_limit_per_minute,
        window_seconds=60,
        detail="Too many AI requests",
    )


def _settings_from_request(request: Request):
    return getattr(request.app.state, "settings", get_settings())


def _client_ip(request: Request) -> str:
    headers = getattr(request, "headers", {})
    forwarded_for = headers.get("x-forwarded-for", "") if hasattr(headers, "get") else ""
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    client = getattr(request, "client", None)
    return getattr(client, "host", "unknown")


def _get_course(db: Session, user_id: str, course_id: str) -> Course:
    course = db.get(Course, course_id)
    if not course or course.user_id != user_id:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def _status_for_mastery(mastery: int) -> str:
    if mastery >= 4:
        return "mastered"
    if mastery > 0:
        return "in_progress"
    return "not_started"


def _normalize_document_tags(tags: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        cleaned = tag.strip()
        key = cleaned.casefold()
        if cleaned and key not in seen:
            normalized.append(cleaned[:40])
            seen.add(key)
        if len(normalized) >= 12:
            break
    return normalized


def _upsert_progress_record(
    db: Session,
    user_id: str,
    course_id: str | None,
    item_id: str,
    item_type: str,
    status: str,
    mastery: int,
) -> ProgressRecord | None:
    if not course_id:
        return None
    record = (
        db.query(ProgressRecord)
        .filter(
            ProgressRecord.user_id == user_id,
            ProgressRecord.course_id == course_id,
            ProgressRecord.item_id == item_id,
            ProgressRecord.item_type == item_type,
        )
        .first()
    )
    if not record:
        record = ProgressRecord(user_id=user_id, course_id=course_id, item_id=item_id, item_type=item_type)
        db.add(record)
    record.status = status
    record.mastery = mastery
    return record


def _document_card(db: Session, document: Document, latest_job: IngestionJob | None = None) -> dict:
    if latest_job is None:
        latest_job = (
            db.query(IngestionJob)
            .filter(IngestionJob.user_id == document.user_id, IngestionJob.document_id == document.id)
            .order_by(IngestionJob.created_at.desc())
            .first()
        )
    chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).count()
    return serialize_document_card(document, latest_job, chunk_count)


def _database_status(db: Session) -> dict:
    try:
        db.execute(text("select 1")).scalar_one()
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _pgvector_status(db: Session) -> dict:
    try:
        installed = db.execute(text("select extname from pg_extension where extname = 'vector'")).first()
        return {"ok": bool(installed), "extension": "vector" if installed else ""}
    except Exception as exc:
        return {"ok": False, "extension": "vector", "error": str(exc)}


def _upload_dir_status(upload_dir: Path) -> dict:
    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
        probe_path = upload_dir / ".write-test"
        probe_path.write_text("ok", encoding="utf-8")
        probe_path.unlink(missing_ok=True)
        return {"ok": True, "path": str(upload_dir)}
    except OSError as exc:
        return {"ok": False, "path": str(upload_dir), "error": str(exc)}


def _worker_status(db: Session) -> dict:
    try:
        latest_job = db.query(IngestionJob).order_by(IngestionJob.updated_at.desc()).first()
        if not latest_job:
            return {"ok": True, "latest_job_status": "idle", "latest_job_progress": 0}
        return {
            "ok": latest_job.status in {"queued", "processing", "succeeded", "failed"},
            "latest_job_status": latest_job.status,
            "latest_job_progress": latest_job.progress,
            "latest_job_updated_at": latest_job.updated_at.isoformat() if latest_job.updated_at else None,
        }
    except Exception as exc:
        return {"ok": False, "latest_job_status": "unknown", "error": str(exc)}


def _delete_course_related_rows(db: Session, user_id: str, course_id: str) -> list[str]:
    documents = db.query(Document).filter(Document.user_id == user_id, Document.course_id == course_id).all()
    document_ids = [document.id for document in documents]
    file_paths = [document.file_path for document in documents]

    chat_sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id, ChatSession.course_id == course_id).all()
    chat_session_ids = [session.id for session in chat_sessions]
    if chat_session_ids:
        db.query(ChatMessage).filter(ChatMessage.session_id.in_(chat_session_ids)).delete(synchronize_session=False)
    db.query(ChatSession).filter(ChatSession.user_id == user_id, ChatSession.course_id == course_id).delete(
        synchronize_session=False
    )

    for model in [StudyCard, GeneratedQuestion, WrongNote, Mindmap, ProgressRecord]:
        db.query(model).filter(model.user_id == user_id, model.course_id == course_id).delete(synchronize_session=False)

    db.query(DocumentChunk).filter(DocumentChunk.user_id == user_id, DocumentChunk.course_id == course_id).delete(
        synchronize_session=False
    )
    if document_ids:
        db.query(IngestionJob).filter(IngestionJob.user_id == user_id, IngestionJob.document_id.in_(document_ids)).delete(
            synchronize_session=False
        )
    db.query(Document).filter(Document.user_id == user_id, Document.course_id == course_id).delete(
        synchronize_session=False
    )
    return file_paths


def _remove_uploaded_file(file_path: str) -> None:
    if not file_path:
        return
    upload_root = Path(get_settings().upload_dir).resolve()
    target = Path(file_path).resolve()
    try:
        if target.is_relative_to(upload_root) and target.is_file():
            target.unlink()
    except OSError:
        pass


def _get_or_create_chat_session(db: Session, user_id: str, payload: ChatRequest) -> ChatSession:
    if payload.session_id:
        session = db.get(ChatSession, payload.session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return session
    title = payload.question.strip().replace("\n", " ")[:60] or "新的问答"
    session = ChatSession(user_id=user_id, course_id=payload.course_id, title=title)
    db.add(session)
    db.flush()
    return session


def _chat_session_row(session: ChatSession) -> dict:
    return {
        "id": session.id,
        "course_id": session.course_id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
    }


def _retrieve_chunks(db: Session, user_id: str, question: str, course_id: str | None, document_ids: list[str]) -> list[RetrievedChunk]:
    provider = get_embedding_provider()
    question_vector = provider.embed([question])[0]
    query = _chunk_retrieval_query(db, user_id, course_id, document_ids)
    try:
        distance = DocumentChunk.embedding.cosine_distance(question_vector).label("distance")
        rows = query.add_columns(distance).order_by(distance.asc()).limit(6).all()
        return [
            _retrieved_chunk_from_row(chunk, document, course, 1 - float(distance_value or 0))
            for chunk, document, course, distance_value in rows
        ]
    except Exception:
        return _retrieve_chunks_in_memory(db, user_id, course_id, document_ids, question_vector)


def _chunk_retrieval_query(db: Session, user_id: str, course_id: str | None, document_ids: list[str]):
    query = db.query(DocumentChunk, Document, Course).join(Document, DocumentChunk.document_id == Document.id).join(Course, DocumentChunk.course_id == Course.id)
    query = query.filter(DocumentChunk.user_id == user_id)
    if course_id:
        query = query.filter(DocumentChunk.course_id == course_id)
    if document_ids:
        query = query.filter(DocumentChunk.document_id.in_(document_ids))
    return query


def _retrieve_chunks_in_memory(
    db: Session,
    user_id: str,
    course_id: str | None,
    document_ids: list[str],
    question_vector: list[float],
) -> list[RetrievedChunk]:
    query = _chunk_retrieval_query(db, user_id, course_id, document_ids)
    scored = []
    for chunk, document, course in query.limit(500).all():
        scored.append((cosine_similarity(question_vector, vector_values(chunk.embedding)), chunk, document, course))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [_retrieved_chunk_from_row(chunk, document, course, score) for score, chunk, document, course in scored[:6]]


def _retrieved_chunk_from_row(chunk: DocumentChunk, document: Document, course: Course, similarity: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk.id,
        document_id=document.id,
        document_title=document.title,
        course_title=course.title,
        text=chunk.text,
        page_number=chunk.page_number,
        similarity=similarity,
    )


def _citation_preview(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[:limit].rstrip()}..."


def _mindmap_row(mindmap: Mindmap) -> dict:
    return {
        "id": mindmap.id,
        "course_id": mindmap.course_id,
        "title": mindmap.title,
        "markdown": mindmap.markdown,
        "created_at": mindmap.created_at.isoformat(),
    }


def _context_for_generation(db: Session, user_id: str, topic: str, course_id: str | None, document_ids: list[str]) -> str:
    chunks = _retrieve_chunks(db, user_id, topic, course_id, document_ids)
    if not chunks:
        return "没有检索到相关课程资料。"
    return "\n\n".join(f"[{chunk.document_title}] {chunk.text}" for chunk in chunks)
