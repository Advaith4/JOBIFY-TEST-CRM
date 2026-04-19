"""
src/api/routes/resume.py
POST /api/resume/upload  – upload PDF, extract text, upsert in DB
"""
import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from src.database.connection import get_session
from src.models import User, Resume
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/api/resume", tags=["resume"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}
MAX_FILE_SIZE_MB = 5


class ResumeAnalyzeReq(BaseModel):
    target_role: str = Field(default="", max_length=120)


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    os.makedirs("data", exist_ok=True)
    temp_path = f"data/resume_{uuid.uuid4().hex}.pdf"

    try:
        # Save temp file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate file size
        size_mb = os.path.getsize(temp_path) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit.")

        # Extract text
        from utils.resume_parser import extract_text_from_pdf
        resume_text = extract_text_from_pdf(temp_path)
        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF. Is it a scanned image?")

        # Upsert resume
        resume = session.exec(select(Resume).where(Resume.user_id == current_user.id)).first()
        if resume:
            resume.raw_text = resume_text
        else:
            resume = Resume(user_id=current_user.id, raw_text=resume_text)
            session.add(resume)
        session.commit()

        return {"success": True, "message": "Resume stored successfully."}

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/analyze")
def analyze_resume(
    req: ResumeAnalyzeReq,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    resume = session.exec(select(Resume).where(Resume.user_id == current_user.id)).first()
    if not resume:
        raise HTTPException(status_code=400, detail="Please upload a resume first.")

    try:
        from crew import run_resume_analyzer

        result = run_resume_analyzer(resume.raw_text, req.target_role.strip())
        return {
            "success": True,
            "score": result.get("score", 0),
            "issues": result.get("issues", []),
            "improvements": result.get("improvements", []),
            "section_feedback": result.get("section_feedback", {}),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Resume analyzer failed: {exc}")
