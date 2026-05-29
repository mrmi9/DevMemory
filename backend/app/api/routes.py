from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
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
    Citation,
    CourseCreate,
    CourseOut,
    CourseUpdate,
    DocumentCardOut,
    DocumentChunkOut,
    DocumentOut,
    GeneratedQuestionOut,
    GenerateRequest,
    GeneratedTextResponse,
    JobOut,
    LoginRequest,
    LoginResponse,
    ProgressUpdate,
    StudyCardMasteryUpdate,
    StudyCardOut,
    WrongNoteRequest,
    WrongNoteOut,
)
from app.services.document_parser import detect_document_kind
from app.services.document_library import serialize_chunk_row, serialize_document_card
from app.services.embeddings import HashEmbeddingProvider, cosine_similarity, vector_values
from app.services.llm import DeepSeekClient
from app.services.rag import RetrievedChunk, build_rag_prompt
from app.services.study_library import build_wrong_note_from_question, parse_generated_cards, parse_generated_questions, serialize_generated_question_row, serialize_study_card_row, serialize_wrong_note_row
from app.services.study_generation import analyze_wrong_note, generate_cards, generate_mindmap, generate_questions

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
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
    db.delete(course)
    db.commit()
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
    target.write_bytes(await file.read())

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
async def chat(payload: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chunks = _retrieve_chunks(db, user.id, payload.question, payload.course_id, payload.document_ids)
    prompt = build_rag_prompt(payload.question, chunks)
    answer = await DeepSeekClient().complete(prompt)
    session = _get_or_create_chat_session(db, user.id, payload)
    citations = [
        Citation(
            chunk_id=chunk.chunk_id,
            document_title=chunk.document_title,
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
    )


@router.get("/chat/sessions", response_model=list[ChatSessionOut])
def list_chat_sessions(course_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(ChatSession).filter(ChatSession.user_id == user.id)
    if course_id:
        query = query.filter(ChatSession.course_id == course_id)
    sessions = query.order_by(ChatSession.created_at.desc()).limit(50).all()
    return [
        {
            "id": session.id,
            "course_id": session.course_id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
        }
        for session in sessions
    ]


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
async def cards(payload: GenerateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
def update_study_card_mastery(card_id: str, payload: StudyCardMasteryUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    card = db.get(StudyCard, card_id)
    if not card or card.user_id != user.id:
        raise HTTPException(status_code=404, detail="Study card not found")
    card.mastery = payload.mastery
    db.commit()
    db.refresh(card)
    return serialize_study_card_row(card)


@router.post("/study/questions", response_model=GeneratedTextResponse)
async def questions(payload: GenerateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
async def wrong_notes(payload: WrongNoteRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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


@router.post("/mindmaps", response_model=GeneratedTextResponse)
async def mindmaps(payload: GenerateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    context = _context_for_generation(db, user.id, payload.topic, payload.course_id, payload.document_ids)
    markdown = await generate_mindmap(payload.topic, context)
    db.add(Mindmap(user_id=user.id, course_id=payload.course_id, title=payload.topic, markdown=markdown))
    db.commit()
    return GeneratedTextResponse(content=markdown)


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


def _get_course(db: Session, user_id: str, course_id: str) -> Course:
    course = db.get(Course, course_id)
    if not course or course.user_id != user_id:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


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


def _retrieve_chunks(db: Session, user_id: str, question: str, course_id: str | None, document_ids: list[str]) -> list[RetrievedChunk]:
    query = db.query(DocumentChunk, Document, Course).join(Document, DocumentChunk.document_id == Document.id).join(Course, DocumentChunk.course_id == Course.id)
    query = query.filter(DocumentChunk.user_id == user_id)
    if course_id:
        query = query.filter(DocumentChunk.course_id == course_id)
    if document_ids:
        query = query.filter(DocumentChunk.document_id.in_(document_ids))

    provider = HashEmbeddingProvider()
    question_vector = provider.embed([question])[0]
    scored = []
    for chunk, document, course in query.limit(500).all():
        scored.append((cosine_similarity(question_vector, vector_values(chunk.embedding)), chunk, document, course))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        RetrievedChunk(
            chunk_id=chunk.id,
            document_title=document.title,
            course_title=course.title,
            text=chunk.text,
            page_number=chunk.page_number,
            similarity=score,
        )
        for score, chunk, document, course in scored[:6]
    ]


def _context_for_generation(db: Session, user_id: str, topic: str, course_id: str | None, document_ids: list[str]) -> str:
    chunks = _retrieve_chunks(db, user_id, topic, course_id, document_ids)
    if not chunks:
        return "没有检索到相关课程资料。"
    return "\n\n".join(f"[{chunk.document_title}] {chunk.text}" for chunk in chunks)
