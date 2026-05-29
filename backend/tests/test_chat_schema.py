from app.services.embeddings import vector_values
from app.schemas import ChatRequest, ChatResponse


def test_chat_schema_supports_session_continuation():
    request = ChatRequest(question="summarize SNMP", course_id="course-1", session_id="session-1")
    response = ChatResponse(answer="answer", citations=[], session_id="session-1")

    assert request.session_id == "session-1"
    assert response.session_id == "session-1"


class AmbiguousVector:
    def __iter__(self):
        return iter([0.1, 0.2, 0.3])

    def __bool__(self):
        raise ValueError("truth value is ambiguous")


def test_vector_values_handles_pgvector_like_values_without_truthiness():
    assert vector_values(AmbiguousVector()) == [0.1, 0.2, 0.3]
    assert vector_values(None) == []
