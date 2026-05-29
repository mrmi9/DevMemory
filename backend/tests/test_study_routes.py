from dataclasses import dataclass
from datetime import datetime

import pytest
from fastapi import HTTPException

from app.api import routes
from app.api.routes import add_generated_question_to_wrong_notes, delete_document
from app.models import DocumentChunk, IngestionJob


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
