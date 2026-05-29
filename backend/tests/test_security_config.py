import pytest
from fastapi.testclient import TestClient

from app.auth import hash_password, verify_password
from app.config import Settings, validate_runtime_settings


def test_production_settings_reject_default_access_token_secret():
    settings = Settings(environment="production", access_token_secret="change-this-secret")

    with pytest.raises(ValueError, match="STUDY_ACCESS_TOKEN_SECRET"):
        validate_runtime_settings(settings)


def test_production_settings_reject_empty_password_and_short_secret():
    weak_secret = "short-secret"
    settings = Settings(
        environment="production",
        access_token_secret=weak_secret,
        default_password="",
        cors_origins=["https://study.example"],
    )

    with pytest.raises(ValueError, match="STUDY_ACCESS_TOKEN_SECRET"):
        validate_runtime_settings(settings)

    settings = Settings(
        environment="production",
        access_token_secret="x" * 40,
        default_password="",
        cors_origins=["https://study.example"],
    )

    with pytest.raises(ValueError, match="STUDY_DEFAULT_PASSWORD"):
        validate_runtime_settings(settings)


def test_production_settings_validate_upload_dir_and_embedding_dimensions(tmp_path):
    upload_dir = tmp_path / "uploads"
    settings = Settings(
        environment="production",
        access_token_secret="x" * 40,
        default_password="safe-password",
        cors_origins=["https://study.example"],
        upload_dir=upload_dir,
        embedding_dimensions=768,
    )

    with pytest.raises(ValueError, match="STUDY_EMBEDDING_DIMENSIONS"):
        validate_runtime_settings(settings)

    settings = Settings(
        environment="production",
        access_token_secret="x" * 40,
        default_password="safe-password",
        cors_origins=["https://study.example"],
        upload_dir=upload_dir,
    )

    validate_runtime_settings(settings)
    assert upload_dir.exists()


def test_application_uses_configured_cors_origins():
    from app.main import create_app

    settings = Settings(cors_origins=["https://study.example"])

    app = create_app(settings)

    cors_middleware = next(item for item in app.user_middleware if item.cls.__name__ == "CORSMiddleware")
    assert cors_middleware.kwargs["allow_origins"] == ["https://study.example"]


def test_health_endpoint_reports_status_without_auth(monkeypatch):
    import app.main as main

    monkeypatch.setattr(main, "run_migrations", lambda: None)
    app = main.create_app(Settings(environment="test"))

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "environment": "test"}


def test_password_hash_uses_pbkdf2_and_verifies_legacy_sha256_hashes():
    password_hash = hash_password("correct horse battery staple")

    assert password_hash.startswith("pbkdf2_sha256$")
    assert verify_password("correct horse battery staple", password_hash) is True
    assert verify_password("wrong password", password_hash) is False
    assert verify_password(
        "changeme",
        "sha256$1685210512848ca0e13ce7b4635767c0799e0d6928f4357dec691fd675fb156d",
    ) is True
