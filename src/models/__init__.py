from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Registered user. Password stored as bcrypt hash."""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=50)
    hashed_password: str
    target_role: Optional[str] = Field(default=None, max_length=100)
    location: Optional[str] = Field(default="India", max_length=100)
    experience: Optional[str] = Field(default="Entry-level", max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Resume(SQLModel, table=True):
    """Latest resume text and interactive Resume Lab state for a user."""
    __tablename__ = "resumes"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    raw_text: str
    original_text: Optional[str] = None
    current_text: Optional[str] = None
    parsed_resume: Optional[str] = None
    last_analysis: Optional[str] = None
    applied_fixes: str = Field(default="[]")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class JobApplication(SQLModel, table=True):
    """Tracked job with AI-tailored resume bullets."""
    __tablename__ = "job_applications"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    company_name: Optional[str] = Field(default=None, max_length=200)
    job_title: str = Field(max_length=200)
    job_description_url: Optional[str] = Field(default=None, max_length=500)
    status: str = Field(default="Bookmarked", max_length=50)
    tailored_resume_bullets: Optional[str] = None  # JSON array stored as text
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InterviewSession(SQLModel, table=True):
    """Persisted mock interview session with full chat history."""
    __tablename__ = "interview_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    session_token: str = Field(index=True, unique=True)   # UUID hex — links to in-memory state
    role: str = Field(max_length=100)
    difficulty: int = Field(default=5)
    training_mode: str = Field(default="adaptive", max_length=40)
    interviewer_persona: str = Field(default="balanced", max_length=40)
    messages: str = Field(default="[]")  # JSON: [{role, content, score?, timestamp}]
    personalization_context: str = Field(default="{}")  # JSON: resume weaknesses, section scores, focus mix
    avg_score: Optional[float] = None
    status: str = Field(default="active", max_length=20)  # active | completed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CareerCoachMemory(SQLModel, table=True):
    """Long-term coaching memory synthesized from resume analysis and interview sessions."""
    __tablename__ = "career_coach_memory"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, unique=True)
    recurring_weak_areas: str = Field(default="[]")  # JSON: [{area, count, last_seen}]
    score_trend: str = Field(default="[]")  # JSON: recent answer scores and focus areas
    session_history: str = Field(default="[]")  # JSON: compact session summaries
    daily_plan: Optional[str] = None  # JSON: latest generated coaching plan
    preferred_persona: str = Field(default="balanced", max_length=40)
    preferred_training_mode: str = Field(default="adaptive", max_length=40)
    session_count: int = Field(default=0)
    avg_answer_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
