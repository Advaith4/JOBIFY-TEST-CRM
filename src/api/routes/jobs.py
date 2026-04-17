"""
src/api/routes/jobs.py
GET  /api/jobs/feed       – run AI pipeline, return job feed for current user
POST /api/jobs/track      – track a job and generate tailored resume bullets (BackgroundTask)
GET  /api/jobs/tracker    – fetch all tracked applications for current user
"""
import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from src.database.connection import get_session
from src.models import User, Resume, JobApplication
from src.api.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class TrackJobReq(BaseModel):
    company_name: str = Field(max_length=200)
    job_title: str = Field(min_length=1, max_length=200)
    description_url: str = Field(default="", max_length=500)


def _run_tailor_in_background(application_id: int, resume_text: str, job_title: str, company: str, url: str):
    """Run in FastAPI BackgroundTask — does not block the HTTP response."""
    from src.database.connection import engine
    from sqlmodel import Session as S
    from crew import run_tailored_resume_rewriter

    jd_context = f"{job_title} at {company}. Link: {url}"
    try:
        result = run_tailored_resume_rewriter(resume_text, jd_context)
        bullets = json.dumps(result.get("rewritten_lines", []))
        status = "Draft Ready"
    except Exception as exc:
        logger.error("Tailor background task failed: %s", exc)
        bullets = json.dumps([])
        status = "Tailor Failed"

    with S(engine) as s:
        app = s.get(JobApplication, application_id)
        if app:
            app.tailored_resume_bullets = bullets
            app.status = status
            s.add(app)
            s.commit()


@router.get("/feed")
def get_feed(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    resume = session.exec(select(Resume).where(Resume.user_id == current_user.id)).first()
    if not resume:
        raise HTTPException(status_code=400, detail="Please upload a resume first.")

    prefs = {
        "location": current_user.location,
        "experience": current_user.experience,
        "job_type": "Full-time",
        "work_mode": "Any",
    }

    try:
        from crew import run_job_crew
        return run_job_crew(resume.raw_text, prefs)
    except Exception as exc:
        logger.error("Job feed pipeline failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/track", status_code=202)
def track_job(
    req: TrackJobReq,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    resume = session.exec(select(Resume).where(Resume.user_id == current_user.id)).first()
    if not resume:
        raise HTTPException(status_code=400, detail="No resume on file.")

    application = JobApplication(
        user_id=current_user.id,
        company_name=req.company_name,
        job_title=req.job_title,
        job_description_url=req.description_url,
        status="Tailoring...",
    )
    session.add(application)
    session.commit()
    session.refresh(application)

    # Non-blocking: response returns instantly, tailoring runs in background
    background_tasks.add_task(
        _run_tailor_in_background,
        application.id,
        resume.raw_text,
        req.job_title,
        req.company_name,
        req.description_url,
    )

    return {"success": True, "message": "Job tracked. Resume tailoring started in background.", "application_id": application.id}


@router.get("/tracker")
def get_tracker(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    apps = session.exec(
        select(JobApplication)
        .where(JobApplication.user_id == current_user.id)
        .order_by(JobApplication.created_at.desc())
    ).all()
    return [a.model_dump() for a in apps]
