from datetime import datetime

import pytest
from fastapi import HTTPException

from app.api import routes
from app.api.routes import (
    add_chat_message_to_wrong_notes,
    delete_chat_session,
    generate_questions_from_chat_message,
    rename_chat_session,
    save_chat_message_as_study_card,
)
from app.models import ChatMessage, ChatSession, GeneratedQuestion
from app.schemas import ChatAssetRequest, ChatSessionUpdate


class FakeUser:
    id = "user-1"


class FakeSession:
    id = "session-1"
    user_id = "user-1"
    course_id = "course-1"
    title = "SNMP 复习"
    created_at = datetime(2026, 5, 29, 16, 30, 0)


class FakeAssistantMessage:
    id = "message-2"
    session_id = "session-1"
    role = "assistant"
    content = "SNMP trap 是由设备主动发送的事件通知。"
    citations = [{"document_title": "network.pdf", "text_preview": "trap notification"}]
    created_at = datetime(2026, 5, 29, 16, 31, 0)


class FakeUserMessage:
    id = "message-1"
    session_id = "session-1"
    role = "user"
    content = "什么是 SNMP trap？"
    citations = []
    created_at = datetime(2026, 5, 29, 16, 30, 0)


class PreviousMessageQuery:
    def __init__(self, message):
        self.message = message
        self.filter_called = False
        self.ordered = False

    def filter(self, *conditions):
        self.filter_called = True
        return self

    def order_by(self, *clauses):
        self.ordered = True
        return self

    def first(self):
        return self.message


class ChatAssetDb:
    def __init__(self):
        self.session = FakeSession()
        self.assistant_message = FakeAssistantMessage()
        self.previous_message = FakeUserMessage()
        self.added_rows = []
        self.committed = False
        self.refreshed = []
        self.previous_query = PreviousMessageQuery(self.previous_message)

    def get(self, model, row_id):
        if model is ChatMessage and row_id == "message-2":
            return self.assistant_message
        if model is ChatSession and row_id == "session-1":
            return self.session
        return None

    def query(self, model):
        assert model is ChatMessage
        return self.previous_query

    def add(self, row):
        row.id = f"asset-{len(self.added_rows) + 1}"
        row.created_at = datetime(2026, 5, 29, 16, 40, len(self.added_rows))
        self.added_rows.append(row)

    def commit(self):
        self.committed = True

    def refresh(self, row):
        self.refreshed.append(row)


class DeleteMessagesQuery:
    def __init__(self):
        self.filter_called = False
        self.deleted = False

    def filter(self, *conditions):
        self.filter_called = True
        return self

    def delete(self, synchronize_session=False):
        self.deleted = True
        self.synchronize_session = synchronize_session
        return 2


class ChatSessionDb:
    def __init__(self, session):
        self.session = session
        self.deleted_session = None
        self.committed = False
        self.refreshed = None
        self.message_query = DeleteMessagesQuery()

    def get(self, model, row_id):
        return self.session if row_id == "session-1" else None

    def query(self, model):
        assert model is ChatMessage
        return self.message_query

    def delete(self, row):
        self.deleted_session = row

    def commit(self):
        self.committed = True

    def refresh(self, row):
        self.refreshed = row


def test_rename_chat_session_updates_owned_session_title():
    session = FakeSession()
    db = ChatSessionDb(session)

    payload = rename_chat_session("session-1", ChatSessionUpdate(title="  期末重点  "), user=FakeUser(), db=db)

    assert session.title == "期末重点"
    assert db.committed is True
    assert db.refreshed is session
    assert payload["title"] == "期末重点"
    assert payload["created_at"] == "2026-05-29T16:30:00"


def test_delete_chat_session_removes_messages_before_session():
    session = FakeSession()
    db = ChatSessionDb(session)

    payload = delete_chat_session("session-1", user=FakeUser(), db=db)

    assert payload == {"ok": True}
    assert db.message_query.filter_called is True
    assert db.message_query.deleted is True
    assert db.deleted_session is session
    assert db.committed is True


def test_chat_session_management_hides_other_users_sessions():
    session = FakeSession()
    session.user_id = "other-user"
    db = ChatSessionDb(session)

    with pytest.raises(HTTPException) as exc_info:
        delete_chat_session("session-1", user=FakeUser(), db=db)

    assert exc_info.value.status_code == 404
    assert db.deleted_session is None
    assert db.committed is False


def test_save_chat_message_as_study_card_preserves_question_answer_and_sources():
    db = ChatAssetDb()

    payload = save_chat_message_as_study_card("message-2", user=FakeUser(), db=db)

    card = db.added_rows[0]
    assert card.course_id == "course-1"
    assert card.source == "chat"
    assert card.front == "什么是 SNMP trap？"
    assert "SNMP trap 是由设备主动发送的事件通知。" in card.back
    assert "network.pdf" in card.back
    assert db.previous_query.filter_called is True
    assert db.committed is True
    assert payload["id"] == "asset-1"
    assert payload["source"] == "chat"


def test_add_chat_message_to_wrong_notes_creates_answer_derived_focus_note():
    db = ChatAssetDb()

    payload = add_chat_message_to_wrong_notes("message-2", user=FakeUser(), db=db)

    note = db.added_rows[0]
    assert note.course_id == "course-1"
    assert note.title == "什么是 SNMP trap？"
    assert note.original_question == "什么是 SNMP trap？"
    assert note.correct_answer == "SNMP trap 是由设备主动发送的事件通知。"
    assert note.tags == ["chat-answer", "重点"]
    assert "network.pdf" in note.analysis
    assert payload["id"] == "asset-1"


@pytest.mark.anyio
async def test_generate_questions_from_chat_message_uses_answer_as_generation_context(monkeypatch):
    db = ChatAssetDb()
    captured = {}

    async def fake_generate_questions(topic, context, count):
        captured["topic"] = topic
        captured["context"] = context
        captured["count"] = count
        return "Q: SNMP trap 的触发方式是什么？\nA: 由设备主动触发。\nExplanation: trap 是事件驱动。"

    monkeypatch.setattr(routes, "generate_questions", fake_generate_questions)

    payload = await generate_questions_from_chat_message(
        "message-2",
        ChatAssetRequest(count=5),
        user=FakeUser(),
        db=db,
    )

    question = db.added_rows[0]
    assert captured["topic"] == "什么是 SNMP trap？"
    assert "SNMP trap 是由设备主动发送的事件通知。" in captured["context"]
    assert captured["count"] == 5
    assert isinstance(question, GeneratedQuestion)
    assert question.course_id == "course-1"
    assert payload[0]["prompt"] == "SNMP trap 的触发方式是什么？"


def test_chat_asset_creation_rejects_other_users_message():
    db = ChatAssetDb()
    db.session.user_id = "other-user"

    with pytest.raises(HTTPException) as exc_info:
        save_chat_message_as_study_card("message-2", user=FakeUser(), db=db)

    assert exc_info.value.status_code == 404
    assert db.added_rows == []


def test_chat_asset_creation_rejects_answer_without_citations():
    db = ChatAssetDb()
    db.assistant_message.citations = []

    with pytest.raises(HTTPException) as exc_info:
        save_chat_message_as_study_card("message-2", user=FakeUser(), db=db)

    assert exc_info.value.status_code == 409
    assert db.added_rows == []
