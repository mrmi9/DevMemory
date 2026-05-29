from dataclasses import dataclass
from datetime import datetime

import pytest
from fastapi import HTTPException

from app.api import routes
from app.api.routes import (
    add_generated_question_to_wrong_notes,
    delete_course,
    delete_document,
    delete_generated_question,
    delete_mindmap,
    delete_study_card,
    delete_wrong_note,
    update_generated_question,
    update_document_metadata,
    update_study_card_mastery,
)
from app.models import (
    ChatMessage,
    ChatSession,
    Document,
    DocumentChunk,
    GeneratedQuestion,
    IngestionJob,
    Mindmap,
    ProgressRecord,
    StudyCard,
    WrongNote,
)
from app.schemas import DocumentUpdate, GeneratedQuestionUpdate, StudyCardMasteryUpdate, StudyCardUpdate


@dataclass
class FakeUser:
    id: str = "user-1"


class FakeQuestion:
    id = "question-1"
    user_id = "user-1"
    course_id = "course-1"
    question_type = "short-answer"
    prompt = "Explain SNMP trap."
    answer = "It is a device-initiated notification."
    explanation = "Trap is event-driven."
    created_at = datetime(2026, 5, 29, 16, 25, 0)


class FakeDb:
    def __init__(self):
        self.created_note = None
        self.committed = False

    def get(self, model, row_id):
        return FakeQuestion() if row_id == "question-1" else None

    def add(self, row):
        row.id = "wrong-1"
        row.created_at = datetime(2026, 5, 29, 15, 10, 0)
        self.created_note = row

    def commit(self):
        self.committed = True

    def refresh(self, row):
        pass


def test_add_generated_question_to_wrong_notes_creates_review_note():
    db = FakeDb()

    payload = add_generated_question_to_wrong_notes("question-1", user=FakeUser(), db=db)

    assert db.committed is True
    assert db.created_note.user_id == "user-1"
    assert payload == {
        "id": "wrong-1",
        "course_id": "course-1",
        "title": "Explain SNMP trap.",
        "original_question": "Explain SNMP trap.",
        "user_answer": "",
        "correct_answer": "It is a device-initiated notification.",
        "analysis": "Trap is event-driven.",
        "tags": ["generated-question", "short-answer"],
        "created_at": "2026-05-29T15:10:00",
    }


class FakeDocument:
    id = "document-1"
    user_id = "user-1"

    def __init__(self, file_path: str):
        self.file_path = file_path


class DeleteQuery:
    def __init__(self):
        self.filter_called = False
        self.deleted = False

    def filter(self, *conditions):
        self.filter_called = True
        return self

    def delete(self, synchronize_session=False):
        self.deleted = True
        self.synchronize_session = synchronize_session
        return 1


class DeleteDocumentDb:
    def __init__(self, document):
        self.document = document
        self.deleted_document = None
        self.committed = False
        self.queries = {}

    def get(self, model, row_id):
        return self.document if row_id == "document-1" else None

    def query(self, model):
        query = DeleteQuery()
        self.queries[model] = query
        return query

    def delete(self, row):
        self.deleted_document = row

    def commit(self):
        self.committed = True


def test_delete_document_removes_owned_document_related_rows_and_uploaded_file(tmp_path, monkeypatch):
    upload_root = tmp_path / "uploads"
    file_path = upload_root / "user-1" / "course-1" / "note.md"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("# notes", encoding="utf-8")
    document = FakeDocument(str(file_path))
    db = DeleteDocumentDb(document)

    monkeypatch.setattr(routes, "get_settings", lambda: type("Settings", (), {"upload_dir": upload_root})())

    payload = delete_document("document-1", user=FakeUser(), db=db)

    assert payload == {"ok": True}
    assert db.deleted_document is document
    assert db.queries[DocumentChunk].deleted is True
    assert db.queries[IngestionJob].deleted is True
    assert db.committed is True
    assert not file_path.exists()


def test_delete_document_hides_documents_owned_by_another_user(tmp_path):
    document = FakeDocument(str(tmp_path / "note.md"))
    document.user_id = "other-user"
    db = DeleteDocumentDb(document)

    with pytest.raises(HTTPException) as exc_info:
        delete_document("document-1", user=FakeUser(), db=db)

    assert exc_info.value.status_code == 404
    assert db.deleted_document is None
    assert db.committed is False


class MetadataDocumentDb:
    def __init__(self, document):
        self.document = document
        self.committed = False
        self.refreshed = None

    def get(self, model, row_id):
        return self.document if row_id == "document-1" else None

    def commit(self):
        self.committed = True

    def refresh(self, row):
        self.refreshed = row


def test_update_document_metadata_persists_chapter_and_tags(monkeypatch):
    document = FakeDocument("E:/DevMemory/uploads/user-1/course-1/note.md")
    document.chapter = ""
    document.tags = []
    db = MetadataDocumentDb(document)

    monkeypatch.setattr(
        routes,
        "_document_card",
        lambda _db, row: {
            "id": row.id,
            "chapter": row.chapter,
            "tags": row.tags,
        },
    )

    payload = update_document_metadata(
        "document-1",
        DocumentUpdate(chapter=" 第 2 章 传输层 ", tags=["重点", " 网络 ", "重点", ""]),
        user=FakeUser(),
        db=db,
    )

    assert document.chapter == "第 2 章 传输层"
    assert document.tags == ["重点", "网络"]
    assert db.committed is True
    assert db.refreshed is document
    assert payload == {"id": "document-1", "chapter": "第 2 章 传输层", "tags": ["重点", "网络"]}


class FakeCourse:
    id = "course-1"
    user_id = "user-1"


class FakeChatSession:
    def __init__(self, session_id: str):
        self.id = session_id


class DeleteCourseQuery:
    def __init__(self, model, rows, events):
        self.model = model
        self.rows = rows
        self.events = events
        self.filter_called = False
        self.deleted = False

    def filter(self, *conditions):
        self.filter_called = True
        return self

    def all(self):
        return self.rows

    def delete(self, synchronize_session=False):
        self.deleted = True
        self.synchronize_session = synchronize_session
        self.events.append(("delete_query", self.model))
        return len(self.rows) or 1


class DeleteCourseDb:
    def __init__(self, course, documents, chat_sessions):
        self.course = course
        self.documents = documents
        self.chat_sessions = chat_sessions
        self.deleted_course = None
        self.committed = False
        self.events = []
        self.queries = {}

    def get(self, model, row_id):
        return self.course if row_id == "course-1" else None

    def query(self, model):
        rows = []
        if model is Document:
            rows = self.documents
        elif model is ChatSession:
            rows = self.chat_sessions
        query = DeleteCourseQuery(model, rows, self.events)
        self.queries.setdefault(model, []).append(query)
        return query

    def delete(self, row):
        self.deleted_course = row
        self.events.append(("delete_course", row))

    def commit(self):
        self.committed = True
        self.events.append(("commit",))


def test_delete_course_removes_owned_course_related_rows_and_uploaded_files(monkeypatch):
    first_document = FakeDocument("E:/DevMemory/uploads/user-1/course-1/first.pdf")
    second_document = FakeDocument("E:/DevMemory/uploads/user-1/course-1/second.md")
    second_document.id = "document-2"
    db = DeleteCourseDb(
        FakeCourse(),
        documents=[first_document, second_document],
        chat_sessions=[FakeChatSession("session-1"), FakeChatSession("session-2")],
    )

    monkeypatch.setattr(
        routes,
        "_remove_uploaded_file",
        lambda file_path: db.events.append(("remove_file", file_path)),
    )

    payload = delete_course("course-1", user=FakeUser(), db=db)

    assert payload == {"ok": True}
    assert db.deleted_course is db.course
    for model in [
        ChatMessage,
        ChatSession,
        StudyCard,
        GeneratedQuestion,
        WrongNote,
        Mindmap,
        ProgressRecord,
        DocumentChunk,
        IngestionJob,
        Document,
    ]:
        assert any(query.deleted for query in db.queries.get(model, [])), model
    assert db.committed is True
    assert db.events.index(("commit",)) < db.events.index(("remove_file", first_document.file_path))
    assert ("remove_file", first_document.file_path) in db.events
    assert ("remove_file", second_document.file_path) in db.events


def test_delete_course_hides_courses_owned_by_another_user():
    course = FakeCourse()
    course.user_id = "other-user"
    db = DeleteCourseDb(course, documents=[], chat_sessions=[])

    with pytest.raises(HTTPException) as exc_info:
        delete_course("course-1", user=FakeUser(), db=db)

    assert exc_info.value.status_code == 404
    assert db.deleted_course is None
    assert db.committed is False


class FakeStudyCardRow:
    id = "card-1"
    user_id = "user-1"
    course_id = "course-1"
    front = "What is SNMP trap?"
    back = "A device-initiated notification."
    source = "ai"
    mastery = 0
    created_at = datetime(2026, 5, 29, 16, 20, 0)


class ProgressRecordQuery:
    def __init__(self, record):
        self.record = record
        self.filter_called = False

    def filter(self, *conditions):
        self.filter_called = True
        return self

    def first(self):
        return self.record


class UpdateStudyCardDb:
    def __init__(self, card, progress_record=None):
        self.card = card
        self.progress_record = progress_record
        self.added_progress_record = None
        self.committed = False
        self.refreshed = None
        self.progress_query = None

    def get(self, model, row_id):
        return self.card if row_id == "card-1" else None

    def query(self, model):
        assert model is ProgressRecord
        self.progress_query = ProgressRecordQuery(self.progress_record)
        return self.progress_query

    def add(self, row):
        self.added_progress_record = row

    def commit(self):
        self.committed = True

    def refresh(self, row):
        self.refreshed = row


def test_update_study_card_mastery_records_course_progress():
    db = UpdateStudyCardDb(FakeStudyCardRow())

    payload = update_study_card_mastery(
        "card-1",
        StudyCardMasteryUpdate(mastery=4),
        user=FakeUser(),
        db=db,
    )

    assert payload["mastery"] == 4
    assert db.card.mastery == 4
    assert db.progress_query.filter_called is True
    assert db.added_progress_record.user_id == "user-1"
    assert db.added_progress_record.course_id == "course-1"
    assert db.added_progress_record.item_type == "study_card"
    assert db.added_progress_record.item_id == "card-1"
    assert db.added_progress_record.status == "mastered"
    assert db.added_progress_record.mastery == 4
    assert db.committed is True


def test_update_study_card_content_without_changing_progress():
    db = UpdateStudyCardDb(FakeStudyCardRow())

    payload = update_study_card_mastery(
        "card-1",
        StudyCardUpdate(front="What is an SNMP trap?", back="An event notification sent by a device."),
        user=FakeUser(),
        db=db,
    )

    assert payload["front"] == "What is an SNMP trap?"
    assert payload["back"] == "An event notification sent by a device."
    assert db.card.front == "What is an SNMP trap?"
    assert db.card.back == "An event notification sent by a device."
    assert db.progress_query is None
    assert db.added_progress_record is None
    assert db.committed is True


class DeleteProgressQuery:
    def __init__(self):
        self.filter_called = False
        self.deleted = False

    def filter(self, *conditions):
        self.filter_called = True
        return self

    def delete(self, synchronize_session=False):
        self.deleted = True
        self.synchronize_session = synchronize_session
        return 1


class DeleteStudyAssetDb:
    def __init__(self, row):
        self.row = row
        self.deleted_row = None
        self.committed = False
        self.refreshed = None
        self.progress_query = DeleteProgressQuery()

    def get(self, model, row_id):
        return self.row if row_id == self.row.id else None

    def query(self, model):
        assert model is ProgressRecord
        return self.progress_query

    def delete(self, row):
        self.deleted_row = row

    def commit(self):
        self.committed = True

    def refresh(self, row):
        self.refreshed = row


def test_delete_study_card_removes_owned_card_and_progress_record():
    card = FakeStudyCardRow()
    db = DeleteStudyAssetDb(card)

    payload = delete_study_card("card-1", user=FakeUser(), db=db)

    assert payload == {"ok": True}
    assert db.deleted_row is card
    assert db.progress_query.filter_called is True
    assert db.progress_query.deleted is True
    assert db.committed is True


def test_delete_generated_question_removes_owned_question():
    question = FakeQuestion()
    db = DeleteStudyAssetDb(question)

    payload = delete_generated_question("question-1", user=FakeUser(), db=db)

    assert payload == {"ok": True}
    assert db.deleted_row is question
    assert db.committed is True


def test_update_generated_question_edits_prompt_answer_and_explanation():
    question = FakeQuestion()
    db = DeleteStudyAssetDb(question)

    payload = update_generated_question(
        "question-1",
        GeneratedQuestionUpdate(
            prompt="Explain an SNMP trap.",
            answer="It is an event notification sent by a managed device.",
            explanation="Trap messages are device initiated.",
        ),
        user=FakeUser(),
        db=db,
    )

    assert payload["prompt"] == "Explain an SNMP trap."
    assert payload["answer"] == "It is an event notification sent by a managed device."
    assert payload["explanation"] == "Trap messages are device initiated."
    assert question.prompt == "Explain an SNMP trap."
    assert question.answer == "It is an event notification sent by a managed device."
    assert question.explanation == "Trap messages are device initiated."
    assert db.committed is True
    assert db.refreshed is question


def test_delete_wrong_note_removes_owned_note():
    note = type("FakeWrongNoteRow", (), {"id": "wrong-1", "user_id": "user-1"})()
    db = DeleteStudyAssetDb(note)

    payload = delete_wrong_note("wrong-1", user=FakeUser(), db=db)

    assert payload == {"ok": True}
    assert db.deleted_row is note
    assert db.committed is True


def test_delete_mindmap_removes_owned_mindmap():
    mindmap = type("FakeMindmapRow", (), {"id": "mindmap-1", "user_id": "user-1"})()
    db = DeleteStudyAssetDb(mindmap)

    payload = delete_mindmap("mindmap-1", user=FakeUser(), db=db)

    assert payload == {"ok": True}
    assert db.deleted_row is mindmap
    assert db.committed is True


def test_delete_study_card_hides_cards_owned_by_another_user():
    card = FakeStudyCardRow()
    card.user_id = "other-user"
    db = DeleteStudyAssetDb(card)

    with pytest.raises(HTTPException) as exc_info:
        delete_study_card("card-1", user=FakeUser(), db=db)

    assert exc_info.value.status_code == 404
    assert db.deleted_row is None
    assert db.committed is False
