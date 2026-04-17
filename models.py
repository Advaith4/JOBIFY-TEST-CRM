from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    target_role: Optional[str] = None
    location: Optional[str] = Field(default="India")
    experience: Optional[str] = Field(default="Entry-level")

class Resume(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    raw_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class JobApplication(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    company_name: Optional[str] = None
    job_title: str
    job_description_url: Optional[str] = None
    status: str = Field(default="Bookmarked")
    tailored_resume_bullets: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
