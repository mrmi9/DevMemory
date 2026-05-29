import base64
import io

import pytest
import anyio
from fastapi import HTTPException
from fastapi import UploadFile

from app.auth import create_token
from app.config import Settings
from app.schemas import ChatRequest, LoginRequest


def test_create_token_uses_configured_ttl_minutes(monkeypatch):
    import app.auth as auth

    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: Settings(access_token_secret="x" * 40, access_token_ttl_minutes=2),
    )
    monkeypatch.setattr(auth.time, "time", lambda: 1_700_000_000)

    token = create_token("user-1")
    decoded = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")

    assert decoded.startswith("user-1:1700000120:")


def test_upload_writer_rejects_files_over_configured_limit(tmp_path):
    from app.api.routes import _write_upload_with_size_limit

    async def run_scenario():
        upload = UploadFile(file=io.BytesIO(b"abcdef"), filename="large.md")
        target = tmp_path / "large.md"

        with pytest.raises(HTTPException) as exc_info:
            await _write_upload_with_size_limit(upload, target, max_bytes=5)

        assert exc_info.value.status_code == 413
        assert "File exceeds" in exc_info.value.detail
        assert not target.exists()

    anyio.run(run_scenario)


def test_rate_limiter_blocks_after_configured_limit_and_recovers_after_window():
    from app.rate_limit import InMemoryRateLimiter

    now = 1_000.0
    limiter = InMemoryRateLimiter(clock=lambda: now)

    limiter.assert_allowed("login:127.0.0.1", limit=2, window_seconds=60, detail="Too many login attempts")
    limiter.assert_allowed("login:127.0.0.1", limit=2, window_seconds=60, detail="Too many login attempts")
    with pytest.raises(HTTPException) as exc_info:
        limiter.assert_allowed("login:127.0.0.1", limit=2, window_seconds=60, detail="Too many login attempts")

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "Too many login attempts"

    now = 1_061.0
    limiter.assert_allowed("login:127.0.0.1", limit=2, window_seconds=60, detail="Too many login attempts")


def test_login_enforces_rate_limit_before_password_check(monkeypatch):
    from app.api import routes

    class BlockingLimiter:
        def assert_allowed(self, key, limit, window_seconds, detail):
            raise HTTPException(status_code=429, detail=detail)

    request = type(
        "FakeRequest",
        (),
        {
            "client": type("Client", (), {"host": "127.0.0.1"})(),
            "app": type("App", (), {"state": type("State", (), {"settings": Settings()})()})(),
        },
    )()
    monkeypatch.setattr(routes, "login_rate_limiter", BlockingLimiter())

    with pytest.raises(HTTPException) as exc_info:
        routes.login(LoginRequest(username="admin", password="wrong"), request=request, db=object())

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "Too many login attempts"


def test_chat_enforces_ai_rate_limit_before_generation(monkeypatch):
    from app.api import routes

    async def run_scenario():
        class BlockingLimiter:
            def assert_allowed(self, key, limit, window_seconds, detail):
                raise HTTPException(status_code=429, detail=detail)

        user = type("FakeUser", (), {"id": "user-1"})()
        request = type(
            "FakeRequest",
            (),
            {
                "client": type("Client", (), {"host": "127.0.0.1"})(),
                "app": type("App", (), {"state": type("State", (), {"settings": Settings()})()})(),
            },
        )()
        monkeypatch.setattr(routes, "ai_rate_limiter", BlockingLimiter())

        with pytest.raises(HTTPException) as exc_info:
            await routes.chat(ChatRequest(question="Explain this"), request=request, user=user, db=object())

        assert exc_info.value.status_code == 429
        assert exc_info.value.detail == "Too many AI requests"

    anyio.run(run_scenario)
