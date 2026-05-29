from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Study Knowledge Base"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg://study:study@postgres:5432/study"
    upload_dir: Path = Path("/data/uploads")
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    embedding_provider: str = "hash"
    embedding_dimensions: int = 384
    default_username: str = "admin"
    default_password: str = "changeme"
    access_token_secret: str = "change-this-secret"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="STUDY_")


@lru_cache
def get_settings() -> Settings:
    return Settings()
