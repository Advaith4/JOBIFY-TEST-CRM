"""
src/api/dependencies.py
FastAPI dependency injectors — DB session and JWT-authenticated current user.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from src.database.connection import get_session
from src.core.security import decode_token
from src.models import User

_bearer = HTTPBearer(auto_error=False)


def _resolve_current_user(
    credentials: HTTPAuthorizationCredentials | None,
    session: Session,
) -> User | None:
    if credentials is None:
        return None

    payload = decode_token(credentials.credentials)
    if payload is None:
        return None

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        return None

    stmt = select(User).where(User.id == user_id)
    return session.exec(stmt).first()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    session: Session = Depends(get_session),
) -> User:
    """Extract and validate JWT. Raise 401 if missing or invalid."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = _resolve_current_user(credentials, session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    session: Session = Depends(get_session),
) -> User | None:
    """Return the current user when a valid bearer token is present, otherwise None."""
    return _resolve_current_user(credentials, session)
