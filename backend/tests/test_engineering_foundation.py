import json
import logging

from fastapi.testclient import TestClient

from app.config import Settings


def test_app_lifespan_runs_migrations_instead_of_create_all(monkeypatch):
    import app.main as main

    calls = []
    monkeypatch.setattr(main, "run_migrations", lambda: calls.append("migrate"))

    app = main.create_app(Settings(environment="test"))

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200

    assert calls == ["migrate"]


def test_request_logging_emits_structured_json(monkeypatch, caplog):
    import app.main as main

    monkeypatch.setattr(main, "run_migrations", lambda: None)
    app = main.create_app(Settings(environment="test"))

    with caplog.at_level(logging.INFO, logger="app.request"):
        with TestClient(app) as client:
            response = client.get("/health")

    assert response.status_code == 200
    payloads = [json.loads(record.message) for record in caplog.records if record.name == "app.request"]
    assert payloads[-1]["event"] == "http_request"
    assert payloads[-1]["method"] == "GET"
    assert payloads[-1]["path"] == "/health"
    assert payloads[-1]["status_code"] == 200
    assert payloads[-1]["duration_ms"] >= 0
