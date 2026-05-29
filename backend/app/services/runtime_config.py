from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import SessionLocal
from app.models import SystemSetting


DEEPSEEK_API_KEY = "deepseek_api_key"
DEEPSEEK_BASE_URL = "deepseek_base_url"
DEEPSEEK_MODEL = "deepseek_model"
DEEPSEEK_KEYS = (DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL)


@dataclass(frozen=True)
class DeepSeekRuntimeConfig:
    api_key: str
    base_url: str
    model: str

    @property
    def configured(self) -> bool:
        return bool(self.api_key)


def get_deepseek_runtime_config(
    db: Session | None = None,
    settings: Settings | None = None,
) -> DeepSeekRuntimeConfig:
    settings = settings or get_settings()
    values = _load_settings(db)
    api_key = values.get(DEEPSEEK_API_KEY) or settings.deepseek_api_key
    base_url = values.get(DEEPSEEK_BASE_URL) or settings.deepseek_base_url
    model = values.get(DEEPSEEK_MODEL) or settings.deepseek_model
    return DeepSeekRuntimeConfig(
        api_key=api_key.strip(),
        base_url=base_url.strip().rstrip("/") or settings.deepseek_base_url,
        model=model.strip() or settings.deepseek_model,
    )


def save_deepseek_runtime_config(
    db: Session,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> DeepSeekRuntimeConfig:
    updates: dict[str, str] = {}
    if api_key is not None and api_key.strip():
        updates[DEEPSEEK_API_KEY] = api_key.strip()
    if base_url is not None and base_url.strip():
        updates[DEEPSEEK_BASE_URL] = base_url.strip().rstrip("/")
    if model is not None and model.strip():
        updates[DEEPSEEK_MODEL] = model.strip()

    for key, value in updates.items():
        row = db.get(SystemSetting, key)
        if row is None:
            row = SystemSetting(key=key, value=value)
            db.add(row)
        else:
            row.value = value

    db.commit()
    return get_deepseek_runtime_config(db)


def mask_secret(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    if len(value) <= 4:
        return "••••"
    return f"••••{value[-4:]}"


def _load_settings(db: Session | None) -> dict[str, str]:
    owns_session = db is None
    session = db or SessionLocal()
    try:
        rows = session.query(SystemSetting).filter(SystemSetting.key.in_(DEEPSEEK_KEYS)).all()
        return {row.key: row.value for row in rows}
    except SQLAlchemyError:
        return {}
    finally:
        if owns_session:
            session.close()
