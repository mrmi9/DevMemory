from fastapi.testclient import TestClient

from app.config import Settings
from app.database import get_db


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one(self):
        return self.value

    def first(self):
        return (self.value,) if self.value else None


class FakeQuery:
    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def first(self):
        return type("Job", (), {"status": "succeeded", "progress": 100, "updated_at": None})()


class FakeDb:
    def execute(self, statement):
        text = str(statement)
        if "pg_extension" in text:
            return FakeResult("vector")
        return FakeResult(1)

    def query(self, model):
        return FakeQuery()


def test_system_status_reports_private_deployment_readiness(monkeypatch, tmp_path):
    import app.main as main

    monkeypatch.setattr(main, "run_migrations", lambda: None)
    app = main.create_app(
        Settings(
            environment="test",
            upload_dir=tmp_path,
            deepseek_api_key="",
            embedding_provider="hash",
        )
    )
    app.dependency_overrides[get_db] = lambda: FakeDb()

    with TestClient(app) as client:
        response = client.get("/api/system/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["environment"] == "test"
    assert payload["ai_mode"] == "offline_placeholder"
    assert payload["checks"]["database"]["ok"] is True
    assert payload["checks"]["pgvector"]["ok"] is True
    assert payload["checks"]["upload_dir"]["ok"] is True
    assert payload["checks"]["deepseek"]["configured"] is False
    assert payload["checks"]["embedding"]["provider"] == "hash"
    assert payload["checks"]["worker"]["latest_job_status"] == "succeeded"
