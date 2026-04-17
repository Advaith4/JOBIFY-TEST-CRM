from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, JSON, Column

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    target_role: Optional[str] = None
    location: Optional[str] = Field(default="India")
    experience: Optional[str] = Field(default="Entry-level")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Resume(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    raw_text: str
    summary_metadata: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TrackedJob(SQLModel, table=True):
    __tablename__ = "tracked_job"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    company_name: Optional[str] = None
    job_title: str
    job_description_url: Optional[str] = None
    status: str = Field(default="Draft Ready")
    tailored_bullets: Optional[str] = Field(default=None, description="JSON array of optimized bullets")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class InterviewSession(SQLModel, table=True):
    __tablename__ = "interview_session"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    role_focused: str
    difficulty: int = Field(default=5)
    
    # Store chat history robustly by dropping memory dicts to the database
    chat_history: Optional[str] = Field(sa_column=Column(JSON), default="[]")
    
    status: str = Field(default="in_progress")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
