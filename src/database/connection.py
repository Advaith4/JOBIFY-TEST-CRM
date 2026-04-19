import os

from sqlmodel import SQLModel, create_engine, Session
from src.config import settings

_db_url = settings.DATABASE_URL
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)

# connect_args only needed for SQLite
_connect_args = {"check_same_thread": False} if _db_url.startswith("sqlite") else {}

engine = create_engine(_db_url, echo=settings.DEBUG, connect_args=_connect_args)


def create_db_and_tables() -> None:
    auto_create = os.getenv("AUTO_CREATE_DB_SCHEMA", "").strip().lower() in {"1", "true", "yes", "on"}
    if _db_url.startswith("sqlite") or auto_create:
        SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
