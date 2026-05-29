from dataclasses import dataclass

from app.services.document_library import serialize_chunk_row


@dataclass
class FakeChunk:
    id: int = 7
    chunk_index: int = 2
    text: str = "SNMP Trap 常用于设备主动告警。"
    token_count: int = 19
    page_number: int | None = 5
    char_start: int = 120
    char_end: int = 148


def test_serialize_chunk_row_exposes_inspection_fields():
    payload = serialize_chunk_row(FakeChunk())

    assert payload == {
        "id": 7,
        "chunk_index": 2,
        "text": "SNMP Trap 常用于设备主动告警。",
        "token_count": 19,
        "page_number": 5,
        "char_start": 120,
        "char_end": 148,
    }
