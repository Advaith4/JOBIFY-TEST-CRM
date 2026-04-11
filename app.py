import os
import logging
import shutil
import uuid
from pathlib import Path

import appdirs
from fastapi import FastAPI, UploadFile, File, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


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
    run_interview_answer
)

interview_sessions = {}

class InterviewStartReq(BaseModel):
    role: str
    difficulty: int = 5
    weak_areas: list[str] = []

class InterviewAnswerReq(BaseModel):
    session_id: str
    answer: str

logger = logging.getLogger(__name__)

app = FastAPI(title="Jobify API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes will be evaluated in order

@app.post("/api/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    location: str = Form(default="India"),
    job_type: str = Form(default="Full-time"),
    work_mode: str = Form(default="Any"),
    experience: str = Form(default="Entry-level")
):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "Only PDF files are supported."})

    # Use UUID to avoid filename collisions in concurrent uploads
    if not os.path.exists("data"):
        os.makedirs("data")

    temp_path = f"data/resume_{uuid.uuid4().hex}.pdf"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # 1. Extract text from PDF
        resume_content = extract_text_from_pdf(temp_path)
        
        if not resume_content or len(resume_content) < 50:
            return JSONResponse(status_code=400, content={"error": "Could not extract sufficient text from the PDF. Make sure it is text-based."})
            
        # 2. Run the AI Pipeline
        prefs = {
            "location": location,
            "job_type": job_type,
            "work_mode": work_mode,
            "experience": experience
        }
        results = analyze_resume_pipeline(resume_content, prefs)
        
        return JSONResponse(content=results)
        
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print("API ERROR CAUGHT:", err_msg)
        return JSONResponse(status_code=500, content={"error": f"{str(e)} | Details: {err_msg}"})
    finally:
        # Clean up the temp file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

# ── New Endpoints (Resume Copilot & Interview Coach) ─────────────────────────

@app.post("/resume/analyze")
async def resume_analyzer_endpoint(
    file: UploadFile = File(...),
    target_role: str = Form(default="")
):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "Only PDF files are supported."})

    if not os.path.exists("data"): os.makedirs("data")
    temp_path = f"data/eval_{uuid.uuid4().hex}.pdf"
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        resume_content = extract_text_from_pdf(temp_path)
        if not resume_content or len(resume_content) < 50:
            return JSONResponse(status_code=400, content={"error": "Empty or bad PDF"})
            
        results = run_resume_analyzer(resume_content, target_role)
        return JSONResponse(content=results)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@app.post("/resume/rewrite")
async def resume_rewrite_endpoint(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "Only PDFs."})

    if not os.path.exists("data"): os.makedirs("data")
    temp_path = f"data/rewrite_{uuid.uuid4().hex}.pdf"
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        resume_content = extract_text_from_pdf(temp_path)
        if not resume_content or len(resume_content) < 50:
            return JSONResponse(status_code=400, content={"error": "Empty or bad PDF"})
            
        results = run_resume_rewriter(resume_content)
        return JSONResponse(content=results)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

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
        
        # update session state dynamically!
        session["questions"].append(session["current_question"])
        session["answers"].append(req.answer)
        
        eval_score = results.get("evaluation", {}).get("score", 5)
        session["scores"].append(eval_score)

        new_diff = results.get("new_difficulty", session["difficulty"])
        
        # Force bounds on difficulty safely parsing as int
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
