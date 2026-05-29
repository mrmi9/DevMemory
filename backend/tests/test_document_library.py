from dataclasses import dataclass
from datetime import datetime

from app.services.document_library import serialize_document_card


@dataclass
class FakeDocument:
    id: str = "doc-1"
    course_id: str = "course-1"
    title: str = "SNMP notes.md"
    original_filename: str = "SNMP notes.md"
    kind: str = "markdown"
    status: str = "ready"
    error_message: str = ""
    extracted_text: str = "SNMP 用于网络管理。\n考试重点包括 MIB、OID 和 Trap。"
    created_at: datetime = datetime(2026, 5, 29, 10, 30, 0)
    updated_at: datetime = datetime(2026, 5, 29, 10, 32, 0)


@dataclass
class FakeJob:
    id: str = "job-1"
    status: str = "succeeded"
    progress: int = 100
    error_message: str = ""


def test_serialize_document_card_includes_job_and_chunk_visibility():
    payload = serialize_document_card(FakeDocument(), FakeJob(), chunk_count=12)

    assert payload == {
        "id": "doc-1",
        "course_id": "course-1",
        "title": "SNMP notes.md",
        "original_filename": "SNMP notes.md",
        "kind": "markdown",
        "status": "ready",
        "error_message": "",
        "text_preview": "SNMP 用于网络管理。\n考试重点包括 MIB、OID 和 Trap。",
        "created_at": "2026-05-29T10:30:00",
        "updated_at": "2026-05-29T10:32:00",
        "chunk_count": 12,
        "latest_job": {
            "id": "job-1",
            "status": "succeeded",
            "progress": 100,
            "error_message": "",
        },
    }


def test_serialize_document_card_handles_missing_job():
    payload = serialize_document_card(FakeDocument(status="uploaded"), None, chunk_count=0)

    assert payload["latest_job"] is None
    assert payload["chunk_count"] == 0
    assert payload["status"] == "uploaded"


def test_serialize_document_card_truncates_long_preview():
    payload = serialize_document_card(FakeDocument(extracted_text="A" * 700), None, chunk_count=1)

    assert payload["text_preview"] == f"{'A' * 497}..."
