from fastapi.testclient import TestClient

from app.config import Settings
from app.database import get_db
from app.auth import get_current_user


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
    def __init__(self):
        self.settings = {}

    def execute(self, statement):
        text = str(statement)
        if "pg_extension" in text:
            return FakeResult("vector")
        return FakeResult(1)

    def query(self, model):
        if getattr(model, "__name__", "") == "SystemSetting":
            return FakeSettingsQuery(self)
        return FakeQuery()

    def get(self, model, row_id):
        if getattr(model, "__name__", "") == "SystemSetting":
            return self.settings.get(row_id)
        return None

    def add(self, row):
        self.settings[row.key] = row

    def commit(self):
        pass

    def refresh(self, row):
        pass


class FakeSettingsQuery:
    def __init__(self, db):
        self.db = db

    def filter(self, *args):
        return self

    def all(self):
        return list(self.db.settings.values())


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


def test_ai_config_can_be_saved_from_page_without_exposing_secret(monkeypatch, tmp_path):
    import app.main as main

    monkeypatch.setattr(main, "run_migrations", lambda: None)
    app = main.create_app(
        Settings(
            environment="test",
            upload_dir=tmp_path,
            deepseek_api_key="",
            deepseek_model="deepseek-v4-pro",
        )
    )
    fake_db = FakeDb()
    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: type("User", (), {"id": "user-1"})()

    with TestClient(app) as client:
        response = client.put(
            "/api/system/ai-config",
            json={
                "api_key": "sk-test-page-config-123456",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-chat",
            },
        )
        status_response = client.get("/api/system/status")
        config_response = client.get("/api/system/ai-config")

    assert response.status_code == 200
    payload_text = response.text + status_response.text + config_response.text
    assert "sk-test-page-config-123456" not in payload_text
    assert response.json()["configured"] is True
    assert response.json()["api_key_hint"] == "••••3456"
    assert status_response.json()["ai_mode"] == "online"
    assert status_response.json()["checks"]["deepseek"]["configured"] is True
    assert status_response.json()["checks"]["deepseek"]["model"] == "deepseek-chat"
    assert config_response.json() == {
        "configured": True,
        "api_key_hint": "••••3456",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
    }
