import base64
import hashlib
import hmac
import time

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import User


def hash_password(password: str) -> str:
    salt = "study-kb"
    digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return f"sha256${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), stored_hash)


def create_token(user_id: str) -> str:
    settings = get_settings()
    expires = int(time.time()) + 60 * 60 * 24 * 30
    payload = f"{user_id}:{expires}"
    signature = hmac.new(settings.access_token_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{signature}".encode("utf-8")).decode("ascii")


def read_token(token: str) -> str:
    settings = get_settings()
    try:
        decoded = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        user_id, expires_text, signature = decoded.rsplit(":", 2)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    payload = f"{user_id}:{expires_text}"
    expected = hmac.new(settings.access_token_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected) or int(expires_text) < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user_id


def get_current_user(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    user_id = read_token(authorization.removeprefix("Bearer ").strip())
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user")
    return user


def ensure_default_user(db: Session) -> User:
    settings = get_settings()
    user = db.query(User).filter(User.username == settings.default_username).first()
    if user:
        return user
    user = User(username=settings.default_username, password_hash=hash_password(settings.default_password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
