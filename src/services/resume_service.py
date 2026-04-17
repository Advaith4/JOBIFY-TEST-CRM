import os
import uuid
import shutil
from sqlmodel import Session, select
from fastapi import UploadFile, HTTPException
from src.models.domain import User, Resume

from utils.resume_parser import extract_text_from_pdf

def upload_resume_to_db(db: Session, user: User, file: UploadFile) -> dict:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Secure file handling logic, with guaranteed cleanup
    upload_dir = "data"
    os.makedirs(upload_dir, exist_ok=True)
    temp_path = os.path.join(upload_dir, f"resume_{uuid.uuid4().hex}.pdf")
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        resume_content = extract_text_from_pdf(temp_path)
        if not resume_content or len(resume_content) < 50:
            raise HTTPException(status_code=400, detail="PDF extraction failed or document is empty.")
            
        # Insert or update Resume
        resume = db.exec(select(Resume).where(Resume.user_id == user.id)).first()
        if resume:
            resume.raw_text = resume_content
        else:
            resume = Resume(user_id=user.id, raw_text=resume_content)
            db.add(resume)
            
        db.commit()
        return {"message": "Resume safely stored in CRM!", "extracted_length": len(resume_content)}
        
    finally:
        # Prevent resource locking bug
        if os.path.exists(temp_path):
            os.remove(temp_path)
