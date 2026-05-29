from app.services.embeddings import vector_values
from app.schemas import ChatRequest, ChatResponse, Citation


def test_chat_schema_supports_session_continuation():
    request = ChatRequest(question="summarize SNMP", course_id="course-1", session_id="session-1")
    response = ChatResponse(
        answer="answer",
        citations=[],
        session_id="session-1",
        retrieval_confidence="none",
        quality_notes=["没有检索到可用资料"],
    )

    assert request.session_id == "session-1"
    assert response.session_id == "session-1"
    assert response.retrieval_confidence == "none"
    assert response.quality_notes == ["没有检索到可用资料"]


def test_citation_exposes_document_link_and_text_preview():
    citation = Citation(
        chunk_id=7,
        document_id="document-1",
        document_title="network.pdf",
        course_title="Computer Networks",
        text_preview="SNMP trap is an event notification.",
        page_number=3,
        similarity=0.92,
    )

    assert citation.document_id == "document-1"
    assert citation.course_title == "Computer Networks"
    assert citation.text_preview == "SNMP trap is an event notification."


class AmbiguousVector:
    def __iter__(self):
        return iter([0.1, 0.2, 0.3])

    def __bool__(self):
        raise ValueError("truth value is ambiguous")


def test_vector_values_handles_pgvector_like_values_without_truthiness():
    assert vector_values(AmbiguousVector()) == [0.1, 0.2, 0.3]
    assert vector_values(None) == []
