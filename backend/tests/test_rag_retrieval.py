from app.api.routes import _retrieve_chunks


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


def test_retrieve_chunks_uses_pgvector_ordering_for_top_k():
    db = RetrievalDb()

    assert _retrieve_chunks(db, "user-1", "SNMP trap", "course-1", []) == []

    assert db.query_obj.order_by_called is True
    assert db.query_obj.limit_value == 6
