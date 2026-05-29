from datetime import datetime

import pytest
from fastapi import HTTPException

from app.api.routes import delete_chat_session, rename_chat_session
from app.models import ChatMessage
from app.schemas import ChatSessionUpdate


class FakeUser:
    id = "user-1"


class FakeSession:
    id = "session-1"
    user_id = "user-1"
    course_id = "course-1"
    title = "SNMP 复习"
    created_at = datetime(2026, 5, 29, 16, 30, 0)


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
