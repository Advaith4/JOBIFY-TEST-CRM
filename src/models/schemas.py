from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

# --- Auth ---
class LoginReq(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    has_resume: bool

# --- Jobs ---
class TrackJobReq(BaseModel):
    company_name: str
    job_title: str
    description_url: str = ""

class JobApplicationResponse(BaseModel):
    id: int
    company_name: Optional[str]
    job_title: str
    status: str
    tailored_bullets: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Interview ---
class InterviewStartReq(BaseModel):
    role: str
    difficulty: int = 5
    weak_areas: List[str] = []

class InterviewAnswerReq(BaseModel):
    session_id: int
    answer: str

class InterviewStartResponse(BaseModel):
    session_id: int
    question: str

class InterviewAnswerResponse(BaseModel):
    evaluation: dict
    next_question: str
    new_difficulty: int
