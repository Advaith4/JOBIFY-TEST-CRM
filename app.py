import os
import logging
import shutil
import uuid
import json
from pathlib import Path
from contextlib import asynccontextmanager

import appdirs
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select

from database import create_db_and_tables, get_session
from models import User, Resume, JobApplication

def _prepare_crewai_storage() -> None:
    os.environ.setdefault("CREWAI_STORAGE_DIR", "jobify_local")
    os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
    os.environ.setdefault("CREWAI_DISABLE_TRACKING", "true")

    storage_root = Path.cwd() / "data" / ".crewai_storage"
    storage_root.mkdir(parents=True, exist_ok=True)
    appdirs.user_data_dir = lambda appname=None, appauthor=None, version=None, roaming=False: str(
        storage_root / (appauthor or "CrewAI") / (appname or "jobify_local")
    )


_prepare_crewai_storage()

from utils.resume_parser import extract_text_from_pdf
from crew import (
    analyze_resume_pipeline,
    run_resume_analyzer,
    run_resume_rewriter,
    run_interview_start,
    run_interview_answer,
    run_tailored_resume_rewriter,
    run_job_crew
)

interview_sessions = {}

class InterviewStartReq(BaseModel):
    role: str
    difficulty: int = 5
    weak_areas: list[str] = []

class InterviewAnswerReq(BaseModel):
    session_id: str
    answer: str

class LoginReq(BaseModel):
    username: str

class TrackJobReq(BaseModel):
    user_id: int
    company_name: str
    job_title: str
    description_url: str = ""

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Jobify AI CRM", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/auth/login")
def login(req: LoginReq, session: Session = Depends(get_session)):
    if not session:
        return JSONResponse(status_code=500, content={"error": "Database not configured"})
    user = session.exec(select(User).where(User.username == req.username)).first()
    if not user:
        user = User(username=req.username)
        session.add(user)
        session.commit()
        session.refresh(user)
    
    # Check if they have a saved resume
    resume = session.exec(select(Resume).where(Resume.user_id == user.id)).first()
    has_resume = resume is not None
    
    return {"user_id": user.id, "username": user.username, "has_resume": has_resume}


@app.post("/api/resume/upload/{user_id}")
async def upload_resume(
    user_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    if not session:
        return JSONResponse(status_code=500, content={"error": "Database not configured"})
        
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "Only PDF files are supported."})

    if not os.path.exists("data"):
        os.makedirs("data")

    temp_path = f"data/resume_{uuid.uuid4().hex}.pdf"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        resume_content = extract_text_from_pdf(temp_path)
        if not resume_content or len(resume_content) < 50:
            return JSONResponse(status_code=400, content={"error": "PDF extraction failed."})
            
        # Save to DB
        resume = session.exec(select(Resume).where(Resume.user_id == user.id)).first()
        if resume:
            resume.raw_text = resume_content
        else:
            resume = Resume(user_id=user.id, raw_text=resume_content)
            session.add(resume)
        session.commit()
        
        return {"message": "Resume safely stored in CRM!"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/api/jobs/feed/{user_id}")
def daily_feed(user_id: int, session: Session = Depends(get_session)):
    if not session:
        return JSONResponse(status_code=500, content={"error": "Database not configured"})
        
    user = session.get(User, user_id)
    resume = session.exec(select(Resume).where(Resume.user_id == user_id)).first()
    
    if not resume:
        return JSONResponse(status_code=400, content={"error": "Please upload a resume first."})

    prefs = {
        "location": user.location,
        "experience": user.experience,
        "job_type": "Full-time",
        "work_mode": "Any"
    }
    
    # We directly use the job_crew function independently for the feed!
    try:
        jobs_data = run_job_crew(resume.raw_text, prefs)
        return jobs_data
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/applications/track")
def track_and_tailor(req: TrackJobReq, session: Session = Depends(get_session)):
    if not session:
        return JSONResponse(status_code=500, content={"error": "Database not configured"})
        
    resume = session.exec(select(Resume).where(Resume.user_id == req.user_id)).first()
    if not resume:
        return JSONResponse(status_code=400, content={"error": "No resume on file."})
        
    app = JobApplication(
        user_id=req.user_id,
        company_name=req.company_name,
        job_title=req.job_title,
        job_description_url=req.description_url,
        status="Tailoring..."
    )
    session.add(app)
    session.commit()
    session.refresh(app)
    
    # Fire off AI tailored rewriter
    # In a prod env this would be a background task, but we will run it inline for simplicity
    jd_context = f"{req.job_title} at {req.company_name}. Link: {req.description_url}"
    tailored_result = run_tailored_resume_rewriter(resume.raw_text, jd_context)
    
    app.tailored_resume_bullets = json.dumps(tailored_result.get("rewritten_lines", []))
    app.status = "Draft Ready"
    session.add(app)
    session.commit()
    
    return {"message": "Job tracked and resume tailored!", "application": app.model_dump()}

@app.get("/api/applications/{user_id}")
def get_applications(user_id: int, session: Session = Depends(get_session)):
    if not session:
        return []
    apps = session.exec(select(JobApplication).where(JobApplication.user_id == user_id).order_by(JobApplication.created_at.desc())).all()
    return [app.model_dump() for app in apps]


@app.post("/interview/start")
async def interview_start(req: InterviewStartReq):
    try:
        results = run_interview_start(req.role, req.difficulty, req.weak_areas)
        session_id = uuid.uuid4().hex
        interview_sessions[session_id] = {
            "role": req.role,
            "difficulty": req.difficulty,
            "weak_areas": req.weak_areas,
            "questions": [],
            "answers": [],
            "scores": [],
            "current_question": results.get("question")
        }
        return {"session_id": session_id, "question": results.get("question")}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/interview/answer")
async def interview_answer(req: InterviewAnswerReq):
    if req.session_id not in interview_sessions:
        return JSONResponse(status_code=400, content={"error": "Invalid session ID. Please start a new interview."})
    
    session = interview_sessions[req.session_id]
    
    if not req.answer.strip():
        return JSONResponse(status_code=400, content={"error": "Answer cannot be empty."})
    
    try:
        results = run_interview_answer(
            role=session["role"],
            question=session["current_question"],
            answer=req.answer,
            current_diff=session["difficulty"]
        )
        
        session["questions"].append(session["current_question"])
        session["answers"].append(req.answer)
        
        eval_score = results.get("evaluation", {}).get("score", 5)
        session["scores"].append(eval_score)
        new_diff = results.get("new_difficulty", session["difficulty"])
        try:
            new_diff = int(new_diff)
        except (ValueError, TypeError):
            new_diff = session["difficulty"]
            
        session["difficulty"] = max(1, min(10, new_diff))
        session["current_question"] = results.get("next_question")
        
        return results
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# Mount the static directory for the Frontend (MUST BE LAST)
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Make sure to run with: uvicorn app:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
