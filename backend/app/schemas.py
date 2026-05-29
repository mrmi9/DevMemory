from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CourseCreate(BaseModel):
    title: str
    description: str = ""
    color: str = "#2563eb"


class CourseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    color: str | None = None


class CourseOut(BaseModel):
    id: str
    title: str
    description: str
    color: str

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: str
    course_id: str
    title: str
    original_filename: str
    kind: str
    status: str
    error_message: str = ""
    chapter: str = ""
    tags: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class DocumentUpdate(BaseModel):
    chapter: str | None = Field(default=None, max_length=160)
    tags: list[str] | None = None


class JobOut(BaseModel):
    id: str
    document_id: str
    job_type: str
    status: str
    progress: int
    error_message: str = ""

    model_config = {"from_attributes": True}


class DocumentJobSummary(BaseModel):
    id: str
    status: str
    progress: int
    error_message: str = ""


class DocumentCardOut(DocumentOut):
    text_preview: str = ""
    created_at: str
    updated_at: str
    chunk_count: int
    latest_job: DocumentJobSummary | None = None


class DocumentChunkOut(BaseModel):
    id: int
    chunk_index: int
    text: str
    token_count: int
    page_number: int | None = None
    char_start: int
    char_end: int


class ChatRequest(BaseModel):
    question: str
    course_id: str | None = None
    document_ids: list[str] = Field(default_factory=list)
    session_id: str | None = None


class Citation(BaseModel):
    chunk_id: int
    document_id: str
    document_title: str
    course_title: str
    text_preview: str
    page_number: int | None = None
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    session_id: str
    assistant_message_id: str | None = None
    retrieval_confidence: str = "unknown"
    quality_notes: list[str] = Field(default_factory=list)


class ChatSessionOut(BaseModel):
    id: str
    course_id: str | None = None
    title: str
    created_at: str


class ChatSessionUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    citations: list[dict] = Field(default_factory=list)
    created_at: str


class ChatAssetRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=10)


class GenerateRequest(BaseModel):
    topic: str
    course_id: str | None = None
    document_ids: list[str] = Field(default_factory=list)
    count: int = 8


class GeneratedTextResponse(BaseModel):
    content: str


class MindmapOut(BaseModel):
    id: str
    course_id: str | None = None
    title: str
    markdown: str
    created_at: str


class StudyCardOut(BaseModel):
    id: str
    course_id: str | None = None
    front: str
    back: str
    source: str
    mastery: int
    created_at: str


class StudyCardUpdate(BaseModel):
    front: str | None = Field(default=None, min_length=1)
    back: str | None = Field(default=None, min_length=1)
    mastery: int | None = Field(default=None, ge=0, le=5)


class StudyCardMasteryUpdate(StudyCardUpdate):
    pass


class GeneratedQuestionOut(BaseModel):
    id: str
    course_id: str | None = None
    question_type: str
    prompt: str
    answer: str
    explanation: str = ""
    created_at: str


class GeneratedQuestionUpdate(BaseModel):
    prompt: str | None = Field(default=None, min_length=1)
    answer: str | None = Field(default=None, min_length=1)
    explanation: str | None = None


class WrongNoteRequest(BaseModel):
    course_id: str | None = None
    title: str
    original_question: str
    user_answer: str = ""
    correct_answer: str = ""


class WrongNoteOut(BaseModel):
    id: str
    course_id: str | None = None
    title: str
    original_question: str
    user_answer: str = ""
    correct_answer: str = ""
    analysis: str = ""
    tags: list[str] = Field(default_factory=list)
    created_at: str


class ProgressUpdate(BaseModel):
    status: str
    mastery: int = Field(ge=0, le=5)
