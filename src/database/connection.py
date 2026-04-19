import os
import logging

from sqlmodel import SQLModel, create_engine, Session, text
from src.config import settings

logger = logging.getLogger(__name__)

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
    _ensure_resume_lab_columns()
    _ensure_interview_context_columns()
    _ensure_career_coach_memory_table()


def _ensure_resume_lab_columns() -> None:
    """Lightweight migration for the interactive Resume Lab fields."""
    try:
        if _db_url.startswith("sqlite"):
            _ensure_sqlite_resume_lab_columns()
        else:
            _ensure_postgres_resume_lab_columns()
    except Exception as exc:
        logger.warning("Resume Lab column migration skipped: %s", exc)


def _ensure_sqlite_resume_lab_columns() -> None:
    columns = {
        "original_text": "TEXT",
        "current_text": "TEXT",
        "parsed_resume": "TEXT",
        "last_analysis": "TEXT",
        "applied_fixes": "TEXT DEFAULT '[]'",
        "updated_at": "DATETIME",
    }
    with Session(engine) as session:
        existing = {row[1] for row in session.exec(text("PRAGMA table_info(resumes)")).all()}
        if not existing:
            return
        for name, definition in columns.items():
            if name not in existing:
                session.exec(text(f"ALTER TABLE resumes ADD COLUMN {name} {definition}"))
        session.exec(text("UPDATE resumes SET original_text = raw_text WHERE original_text IS NULL"))
        session.exec(text("UPDATE resumes SET current_text = raw_text WHERE current_text IS NULL"))
        session.exec(text("UPDATE resumes SET applied_fixes = '[]' WHERE applied_fixes IS NULL OR applied_fixes = ''"))
        session.commit()


def _ensure_postgres_resume_lab_columns() -> None:
    statements = [
        "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS original_text TEXT",
        "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS current_text TEXT",
        "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS parsed_resume TEXT",
        "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS last_analysis TEXT",
        "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS applied_fixes TEXT DEFAULT '[]'",
        "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
        "UPDATE resumes SET original_text = raw_text WHERE original_text IS NULL",
        "UPDATE resumes SET current_text = raw_text WHERE current_text IS NULL",
        "UPDATE resumes SET applied_fixes = '[]' WHERE applied_fixes IS NULL OR applied_fixes = ''",
    ]
    with Session(engine) as session:
        for statement in statements:
            session.exec(text(statement))
        session.commit()


def _ensure_interview_context_columns() -> None:
    """Lightweight migration for resume-aware interview sessions."""
    try:
        if _db_url.startswith("sqlite"):
            _ensure_sqlite_interview_context_columns()
        else:
            _ensure_postgres_interview_context_columns()
    except Exception as exc:
        logger.warning("Interview context column migration skipped: %s", exc)


def _ensure_sqlite_interview_context_columns() -> None:
    columns = {
        "personalization_context": "TEXT DEFAULT '{}'",
        "training_mode": "VARCHAR(40) DEFAULT 'adaptive'",
        "interviewer_persona": "VARCHAR(40) DEFAULT 'balanced'",
    }
    with Session(engine) as session:
        existing = {row[1] for row in session.exec(text("PRAGMA table_info(interview_sessions)")).all()}
        if not existing:
            return
        for name, definition in columns.items():
            if name not in existing:
                session.exec(text(f"ALTER TABLE interview_sessions ADD COLUMN {name} {definition}"))
        session.exec(text("UPDATE interview_sessions SET personalization_context = '{}' WHERE personalization_context IS NULL OR personalization_context = ''"))
        session.exec(text("UPDATE interview_sessions SET training_mode = 'adaptive' WHERE training_mode IS NULL OR training_mode = ''"))
        session.exec(text("UPDATE interview_sessions SET interviewer_persona = 'balanced' WHERE interviewer_persona IS NULL OR interviewer_persona = ''"))
        session.commit()


def _ensure_postgres_interview_context_columns() -> None:
    statements = [
        "ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS personalization_context TEXT DEFAULT '{}'",
        "ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS training_mode VARCHAR(40) DEFAULT 'adaptive'",
        "ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS interviewer_persona VARCHAR(40) DEFAULT 'balanced'",
        "UPDATE interview_sessions SET personalization_context = '{}' WHERE personalization_context IS NULL OR personalization_context = ''",
        "UPDATE interview_sessions SET training_mode = 'adaptive' WHERE training_mode IS NULL OR training_mode = ''",
        "UPDATE interview_sessions SET interviewer_persona = 'balanced' WHERE interviewer_persona IS NULL OR interviewer_persona = ''",
    ]
    with Session(engine) as session:
        for statement in statements:
            session.exec(text(statement))
        session.commit()


def _ensure_career_coach_memory_table() -> None:
    """Create long-term coach memory table where supported."""
    try:
        if _db_url.startswith("sqlite") or os.getenv("AUTO_CREATE_DB_SCHEMA", "").strip().lower() in {"1", "true", "yes", "on"}:
            SQLModel.metadata.create_all(engine)
        elif not _db_url.startswith("sqlite"):
            _ensure_postgres_career_coach_memory_table()
    except Exception as exc:
        logger.warning("Career coach memory migration skipped: %s", exc)


def _ensure_postgres_career_coach_memory_table() -> None:
    statement = """
    CREATE TABLE IF NOT EXISTS career_coach_memory (
        id SERIAL PRIMARY KEY,
        user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
        recurring_weak_areas TEXT DEFAULT '[]',
        score_trend TEXT DEFAULT '[]',
        session_history TEXT DEFAULT '[]',
        daily_plan TEXT,
        preferred_persona VARCHAR(40) DEFAULT 'balanced',
        preferred_training_mode VARCHAR(40) DEFAULT 'adaptive',
        session_count INTEGER DEFAULT 0,
        avg_answer_score DOUBLE PRECISION,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    """
    with Session(engine) as session:
        session.exec(text(statement))
        session.commit()


def get_session():
    with Session(engine) as session:
        yield session
