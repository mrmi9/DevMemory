from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: Literal["development", "test", "production"] = "development"
    app_name: str = "AI Study Knowledge Base"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg://study:study@postgres:5432/study"
    upload_dir: Path = Path("/data/uploads")
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    embedding_provider: str = "hash"
    embedding_api_key: str = ""
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 384
    default_username: str = "admin"
    default_password: str = "changeme"
    access_token_secret: str = "change-this-secret"
    access_token_ttl_minutes: int = 60 * 24
    max_upload_bytes: int = 50 * 1024 * 1024
    login_rate_limit_per_minute: int = 5
    ai_rate_limit_per_minute: int = 30
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", env_prefix="STUDY_")


def validate_runtime_settings(settings: Settings) -> None:
    if settings.environment != "production":
        return
    if settings.access_token_secret == "change-this-secret" or len(settings.access_token_secret) < 32:
        raise ValueError("STUDY_ACCESS_TOKEN_SECRET must be changed to a strong value in production")
    if settings.default_password == "changeme" or not settings.default_password.strip():
        raise ValueError("STUDY_DEFAULT_PASSWORD must be changed in production")
    if settings.access_token_ttl_minutes <= 0:
        raise ValueError("STUDY_ACCESS_TOKEN_TTL_MINUTES must be greater than zero in production")
    if settings.max_upload_bytes <= 0:
        raise ValueError("STUDY_MAX_UPLOAD_BYTES must be greater than zero in production")
    if settings.login_rate_limit_per_minute <= 0:
        raise ValueError("STUDY_LOGIN_RATE_LIMIT_PER_MINUTE must be greater than zero in production")
    if settings.ai_rate_limit_per_minute <= 0:
        raise ValueError("STUDY_AI_RATE_LIMIT_PER_MINUTE must be greater than zero in production")
    if "*" in settings.cors_origins:
        raise ValueError("STUDY_CORS_ORIGINS must not contain '*' in production")
    if settings.embedding_dimensions != 384:
        raise ValueError("STUDY_EMBEDDING_DIMENSIONS must stay 384 until the pgvector schema is migrated")
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    probe_path = settings.upload_dir / ".write-test"
    try:
        probe_path.write_text("ok", encoding="utf-8")
        probe_path.unlink(missing_ok=True)
    except OSError as exc:
        raise ValueError("STUDY_UPLOAD_DIR must be writable in production") from exc


@lru_cache
def get_settings() -> Settings:
    return Settings()
