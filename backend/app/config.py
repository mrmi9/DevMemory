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
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", env_prefix="STUDY_")


def validate_runtime_settings(settings: Settings) -> None:
    if settings.environment != "production":
        return
    if settings.access_token_secret == "change-this-secret" or len(settings.access_token_secret) < 32:
        raise ValueError("STUDY_ACCESS_TOKEN_SECRET must be changed to a strong value in production")
    if settings.default_password == "changeme":
        raise ValueError("STUDY_DEFAULT_PASSWORD must be changed in production")
    if "*" in settings.cors_origins:
        raise ValueError("STUDY_CORS_ORIGINS must not contain '*' in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()
