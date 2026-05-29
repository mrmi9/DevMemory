from app.api import routes
from app.api.routes import _retrieve_chunks
from app.services.embeddings import HashEmbeddingProvider


class RetrievalQuery:
    def __init__(self):
        self.order_by_called = False
        self.limit_value = None

    def join(self, *args):
        return self

    def filter(self, *args):
        return self

    def add_columns(self, *columns):
        self.added_columns = columns
        return self

    def order_by(self, *criteria):
        self.order_by_called = True
        self.order_criteria = criteria
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def all(self):
        return []


class RetrievalDb:
    def __init__(self):
        self.query_obj = RetrievalQuery()

    def query(self, *models):
        self.models = models
        return self.query_obj


class FakeEmbeddingProvider:
    def embed(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]


def test_retrieve_chunks_uses_pgvector_ordering_for_top_k(monkeypatch):
    monkeypatch.setattr(routes, "get_embedding_provider", lambda: FakeEmbeddingProvider())
    db = RetrievalDb()

    assert _retrieve_chunks(db, "user-1", "SNMP trap", "course-1", []) == []

    assert db.query_obj.order_by_called is True
    assert db.query_obj.limit_value == 6


class FakeChunk:
    id = 1
    document_id = "document-1"
    course_id = "course-1"
    text = "网络协议是计算机通信规则"
    page_number = None
    embedding = [0.0 for _ in range(384)]


class FakeDocument:
    id = "document-1"
    title = "network.md"


class FakeCourse:
    title = "计算机网络"


class RetrievalRows:
    def __init__(self, rows=None):
        self.rows = rows

    def limit(self, value):
        self.limit_value = value
        return self

    def all(self):
        return self.rows if self.rows is not None else [(FakeChunk(), FakeDocument(), FakeCourse())]


def test_hash_retrieval_recomputes_similarity_from_chunk_text(monkeypatch):
    monkeypatch.setattr(routes, "get_embedding_provider", lambda: HashEmbeddingProvider())
    monkeypatch.setattr(routes, "_chunk_retrieval_query", lambda *args: RetrievalRows())

    chunks = _retrieve_chunks(RetrievalDb(), "user-1", "什么是网络协议", "course-1", [])

    assert chunks[0].similarity > 0.1


def test_hash_retrieval_filters_untrusted_low_similarity_chunks(monkeypatch):
    class UntrustedChunk(FakeChunk):
        id = 2
        document_id = "document-2"
        text = "烹饪配方需要控制火候"

    class DuplicateTitleDocument(FakeDocument):
        id = "document-2"
        title = "network.md"

    rows = RetrievalRows([
        (FakeChunk(), FakeDocument(), FakeCourse()),
        (UntrustedChunk(), DuplicateTitleDocument(), FakeCourse()),
    ])
    monkeypatch.setattr(routes, "get_embedding_provider", lambda: HashEmbeddingProvider())
    monkeypatch.setattr(routes, "_chunk_retrieval_query", lambda *args: rows)

    chunks = _retrieve_chunks(RetrievalDb(), "user-1", "什么是网络协议", "course-1", [])

    assert [chunk.document_id for chunk in chunks] == ["document-1"]


def test_hash_retrieval_keeps_best_weak_positive_match(monkeypatch):
    class WeakRelevantChunk(FakeChunk):
        text = "SNMP Trap 使用 UDP 162 端口发送告警通知"

    class UnrelatedChunk(FakeChunk):
        id = 2
        document_id = "document-2"
        text = "向量数据库用于相似度检索"

    rows = RetrievalRows([
        (WeakRelevantChunk(), FakeDocument(), FakeCourse()),
        (UnrelatedChunk(), FakeDocument(), FakeCourse()),
    ])
    monkeypatch.setattr(routes, "get_embedding_provider", lambda: HashEmbeddingProvider())
    monkeypatch.setattr(routes, "_chunk_retrieval_query", lambda *args: rows)

    chunks = _retrieve_chunks(RetrievalDb(), "user-1", "trap是什么", "course-1", [])

    assert [chunk.chunk_id for chunk in chunks] == [1]
    assert chunks[0].similarity > 0
