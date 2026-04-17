from sqlmodel import Session, select
from fastapi import HTTPException
from src.models.domain import User, Resume, TrackedJob
from src.models.schemas import TrackJobReq
import json

# Absolute import from the old utility for now (until we refactor old utils)
from crew import run_job_crew, run_tailored_resume_rewriter

def get_daily_feed(db: Session, user: User) -> dict:
    resume = db.exec(select(Resume).where(Resume.user_id == user.id)).first()
    if not resume:
        raise HTTPException(status_code=400, detail="Please upload a resume first.")

    prefs = {
        "location": user.location,
        "experience": user.experience,
        "job_type": "Full-time",
        "work_mode": "Any"
    }
    
    try:
        # Wrap the legacy job_crew call
        jobs_data = run_job_crew(resume.raw_text, prefs)
        return jobs_data
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")

def track_and_tailor_job(db: Session, user: User, req: TrackJobReq) -> dict:
    resume = db.exec(select(Resume).where(Resume.user_id == user.id)).first()
    if not resume:
        raise HTTPException(status_code=400, detail="No resume on file.")

    # Create the tracked job record
    app = TrackedJob(
        user_id=user.id,
        company_name=req.company_name,
        job_title=req.job_title,
        job_description_url=req.description_url,
        status="Tailoring..."
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    
    jd_context = f"{req.job_title} at {req.company_name}. Link: {req.description_url}"
    tailored_result = run_tailored_resume_rewriter(resume.raw_text, jd_context)
    
    # Store JSON string securely
    app.tailored_bullets = json.dumps(tailored_result.get("rewritten_lines", []))
    app.status = "Draft Ready"
    db.add(app)
    db.commit()
    db.refresh(app)
    
    return {"message": "Job tracked and resume tailored!", "application": app.model_dump()}

def get_user_applications(db: Session, user: User):
    apps = db.exec(
        select(TrackedJob)
        .where(TrackedJob.user_id == user.id)
        .order_by(TrackedJob.created_at.desc())
    ).all()
    return [app.model_dump() for app in apps]
