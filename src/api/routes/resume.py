"""
src/api/routes/resume.py
POST /api/resume/upload  – upload PDF, extract text, upsert in DB
"""
import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from src.database.connection import get_session
from src.models import User, Resume
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/api/resume", tags=["resume"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}
MAX_FILE_SIZE_MB = 5


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
