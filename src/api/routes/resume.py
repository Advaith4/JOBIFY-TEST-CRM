"""
src/api/routes/resume.py
Interactive Resume Lab endpoints.
"""
import os
import shutil
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from src.api.dependencies import get_current_user
from src.database.connection import get_session
from src.models import Resume, User
from src.resume_lab import (
    analyze_resume,
    apply_fix,
    apply_top_fixes,
    dumps_json,
    find_issue,
    load_json_field,
    mark_issue_status,
    parse_resume,
    repair_resume_text_spacing,
    rescore_resume,
)

router = APIRouter(prefix="/api/resume", tags=["resume"])

MAX_FILE_SIZE_MB = 5


class ResumeAnalyzeReq(BaseModel):
    target_role: str = Field(default="", max_length=120)


class ApplyFixReq(BaseModel):
    issue_id: str = Field(min_length=6, max_length=64)
    target_role: str = Field(default="", max_length=120)


class ApplyTopFixesReq(BaseModel):
    limit: int = Field(default=3, ge=1, le=10)
    target_role: str = Field(default="", max_length=120)


class ManualEditReq(BaseModel):
    current_resume: str = Field(min_length=50, max_length=50000)


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    os.makedirs("data", exist_ok=True)
    temp_path = f"data/resume_{uuid.uuid4().hex}.pdf"

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        size_mb = os.path.getsize(temp_path) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit.")

        from utils.resume_parser import extract_text_from_pdf

        resume_text = extract_text_from_pdf(temp_path)
        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF. Is it a scanned image?")

        parsed = parse_resume(resume_text)
        resume = session.exec(select(Resume).where(Resume.user_id == current_user.id)).first()
        now = datetime.utcnow()
        if resume:
            resume.raw_text = resume_text
            resume.original_text = resume_text
            resume.current_text = resume_text
            resume.parsed_resume = dumps_json(parsed)
            resume.last_analysis = None
            resume.applied_fixes = "[]"
            resume.updated_at = now
        else:
            resume = Resume(
                user_id=current_user.id,
                raw_text=resume_text,
                original_text=resume_text,
                current_text=resume_text,
                parsed_resume=dumps_json(parsed),
                applied_fixes="[]",
                created_at=now,
                updated_at=now,
            )
            session.add(resume)
        session.commit()

        return {
            "success": True,
            "message": "Resume stored successfully.",
            "lab": _resume_lab_response(resume),
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/lab")
def get_resume_lab(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    resume = session.exec(select(Resume).where(Resume.user_id == current_user.id)).first()
    if not resume:
        return {"success": True, "has_resume": False}

    _ensure_lab_state(resume)
    session.add(resume)
    session.commit()
    session.refresh(resume)
    return _resume_lab_response(resume)


@router.post("/analyze")
def analyze_current_resume(
    req: ResumeAnalyzeReq,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    resume = _get_resume_or_400(session, current_user)
    _ensure_lab_state(resume)

    current_text = resume.current_text or resume.raw_text
    result = analyze_resume(current_text, req.target_role.strip())
    _store_analysis(resume, result)
    session.add(resume)
    session.commit()

    return {
        "success": True,
        **result,
        **_legacy_analysis_fields(result),
        "applied_fixes": load_json_field(resume.applied_fixes, []),
        "current_resume": resume.current_text,
    }


@router.post("/rescore")
def rescore_current_resume(
    req: ResumeAnalyzeReq,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    resume = _get_resume_or_400(session, current_user)
    _ensure_lab_state(resume)

    result = rescore_resume(resume.current_text or resume.raw_text, req.target_role.strip())
    _store_analysis(resume, result)
    session.add(resume)
    session.commit()

    return {
        "success": True,
        **result,
        **_legacy_analysis_fields(result),
        "applied_fixes": load_json_field(resume.applied_fixes, []),
        "current_resume": resume.current_text,
    }


@router.post("/fixes/apply")
def apply_resume_fix(
    req: ApplyFixReq,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    resume = _get_resume_or_400(session, current_user)
    _ensure_lab_state(resume)

    analysis = load_json_field(resume.last_analysis, None)
    if not analysis:
        analysis = analyze_resume(resume.current_text or resume.raw_text, req.target_role.strip())

    issue = find_issue(analysis, req.issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Fix not found. Re-score the resume and try again.")

    applied_fixes = load_json_field(resume.applied_fixes, [])
    result = apply_fix(resume.current_text or resume.raw_text, issue, applied_fixes)

    resume.current_text = result["current_resume"]
    resume.raw_text = result["current_resume"]
    resume.applied_fixes = dumps_json(result["applied_fixes"])
    resume.parsed_resume = dumps_json(parse_resume(result["current_resume"]))
    resume.last_analysis = dumps_json(mark_issue_status(analysis, req.issue_id, result["status"]))
    resume.updated_at = datetime.utcnow()
    session.add(resume)
    session.commit()

    return {
        "success": result["applied"],
        "message": result["message"],
        "status": result["status"],
        "current_resume": resume.current_text,
        "applied_fixes": result["applied_fixes"],
        "analysis": load_json_field(resume.last_analysis, {}),
        "parsed_resume": load_json_field(resume.parsed_resume, {}),
    }


@router.post("/fixes/apply-top")
def apply_resume_top_fixes(
    req: ApplyTopFixesReq,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    resume = _get_resume_or_400(session, current_user)
    _ensure_lab_state(resume)

    analysis = load_json_field(resume.last_analysis, None)
    if not analysis:
        analysis = analyze_resume(resume.current_text or resume.raw_text, req.target_role.strip())

    result = apply_top_fixes(
        resume.current_text or resume.raw_text,
        analysis,
        load_json_field(resume.applied_fixes, []),
        req.limit,
    )

    updated_analysis = analysis
    for issue in result["applied"]:
        updated_analysis = mark_issue_status(updated_analysis, issue["id"], "applied")
    for issue in result["skipped"]:
        updated_analysis = mark_issue_status(updated_analysis, issue["id"], "missing")

    resume.current_text = result["current_resume"]
    resume.raw_text = result["current_resume"]
    resume.applied_fixes = dumps_json(result["applied_fixes"])
    resume.parsed_resume = dumps_json(parse_resume(result["current_resume"]))
    resume.last_analysis = dumps_json(updated_analysis)
    resume.updated_at = datetime.utcnow()
    session.add(resume)
    session.commit()

    return {
        "success": True,
        "message": f"Applied {len(result['applied'])} fixes.",
        "current_resume": resume.current_text,
        "applied_fixes": result["applied_fixes"],
        "applied": result["applied"],
        "skipped": result["skipped"],
        "analysis": updated_analysis,
        "parsed_resume": load_json_field(resume.parsed_resume, {}),
    }


@router.put("/text")
def update_resume_text(
    req: ManualEditReq,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    resume = _get_resume_or_400(session, current_user)
    _ensure_lab_state(resume)

    resume.current_text = req.current_resume.strip()
    resume.raw_text = resume.current_text
    resume.parsed_resume = dumps_json(parse_resume(resume.current_text))
    resume.last_analysis = None
    resume.updated_at = datetime.utcnow()
    session.add(resume)
    session.commit()

    return _resume_lab_response(resume)


@router.post("/reset")
def reset_resume_lab(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    resume = _get_resume_or_400(session, current_user)
    _ensure_lab_state(resume)

    original = resume.original_text or resume.raw_text
    resume.current_text = original
    resume.raw_text = original
    resume.applied_fixes = "[]"
    resume.parsed_resume = dumps_json(parse_resume(original))
    resume.last_analysis = None
    resume.updated_at = datetime.utcnow()
    session.add(resume)
    session.commit()

    return _resume_lab_response(resume)


@router.get("/download")
def download_resume(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    resume = _get_resume_or_400(session, current_user)
    _ensure_lab_state(resume)

    text = resume.current_text or resume.raw_text
    return PlainTextResponse(
        text,
        media_type="text/plain",
        headers={"Content-Disposition": 'attachment; filename="jobify-improved-resume.txt"'},
    )


def _get_resume_or_400(session: Session, current_user: User) -> Resume:
    resume = session.exec(select(Resume).where(Resume.user_id == current_user.id)).first()
    if not resume:
        raise HTTPException(status_code=400, detail="Please upload a resume first.")
    return resume


def _ensure_lab_state(resume: Resume) -> None:
    current = resume.current_text or resume.raw_text or ""
    original = resume.original_text or resume.raw_text or current
    repaired_current = repair_resume_text_spacing(current)
    repaired_original = repair_resume_text_spacing(original)
    text_changed = repaired_current != current or repaired_original != original

    resume.original_text = repaired_original
    resume.current_text = repaired_current
    resume.raw_text = repaired_current
    if not resume.applied_fixes:
        resume.applied_fixes = "[]"
    if text_changed:
        resume.applied_fixes = dumps_json(_repair_applied_fixes(load_json_field(resume.applied_fixes, [])))
        repaired_analysis = _repair_saved_analysis(load_json_field(resume.last_analysis, None))
        resume.last_analysis = dumps_json(repaired_analysis) if repaired_analysis else None
        resume.parsed_resume = dumps_json(parse_resume(repaired_current))
    elif not resume.parsed_resume:
        resume.parsed_resume = dumps_json(parse_resume(repaired_current))
    if not resume.updated_at:
        resume.updated_at = datetime.utcnow()


def _store_analysis(resume: Resume, analysis: dict[str, Any]) -> None:
    parsed = parse_resume(resume.current_text or resume.raw_text)
    resume.parsed_resume = dumps_json(parsed)
    resume.last_analysis = dumps_json(analysis)
    resume.updated_at = datetime.utcnow()


def _resume_lab_response(resume: Resume) -> dict[str, Any]:
    _ensure_lab_state(resume)
    applied = load_json_field(resume.applied_fixes, [])
    parsed = load_json_field(resume.parsed_resume, parse_resume(resume.current_text or resume.raw_text))
    analysis = load_json_field(resume.last_analysis, None)
    current_text = resume.current_text or resume.raw_text
    original_text = resume.original_text or resume.raw_text

    return {
        "success": True,
        "has_resume": True,
        "original_resume": original_text,
        "current_resume": current_text,
        "parsed_resume": parsed,
        "last_analysis": analysis,
        "applied_fixes": applied,
        "stats": {
            "applied_count": len(applied),
            "word_count": len(current_text.split()),
            "changed_characters": abs(len(current_text) - len(original_text)),
            "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
        },
    }


def _legacy_analysis_fields(analysis: dict[str, Any]) -> dict[str, Any]:
    issues = []
    improvements = []
    section_feedback = {}

    for section in analysis.get("sections", []) or []:
        section_name = str(section.get("section", "resume"))
        section_issues = section.get("issues", []) or []
        if not section_issues:
            continue

        issue_summaries = []
        for issue in section_issues:
            problem = str(issue.get("problem", "")).strip()
            improved = str(issue.get("improved", "")).strip()
            if problem:
                issues.append(f"{section_name.title()}: {problem}")
                issue_summaries.append(problem)
            if improved:
                improvements.append(improved)

        if issue_summaries:
            section_feedback[section_name] = "; ".join(issue_summaries[:2])

    return {
        "issues": issues,
        "improvements": improvements,
        "section_feedback": section_feedback,
    }


def _repair_applied_fixes(applied_fixes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    repaired: list[dict[str, Any]] = []
    for item in applied_fixes or []:
        if not isinstance(item, dict):
            continue
        updated = dict(item)
        for key in ("original", "improved"):
            if isinstance(updated.get(key), str):
                updated[key] = repair_resume_text_spacing(updated[key])
        repaired.append(updated)
    return repaired


def _repair_saved_analysis(analysis: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(analysis, dict):
        return analysis

    repaired = load_json_field(dumps_json(analysis), {})
    for section in repaired.get("sections", []) or []:
        if not isinstance(section, dict):
            continue
        for issue in section.get("issues", []) or []:
            if not isinstance(issue, dict):
                continue
            for key in ("original", "problem", "improved"):
                if isinstance(issue.get(key), str):
                    issue[key] = repair_resume_text_spacing(issue[key])

    summary_feedback = repaired.get("summary_feedback")
    if isinstance(summary_feedback, dict):
        for key in ("strengths", "weaknesses", "priority_fixes"):
            values = summary_feedback.get(key)
            if isinstance(values, list):
                summary_feedback[key] = [
                    repair_resume_text_spacing(value) if isinstance(value, str) else value
                    for value in values
                ]

    return repaired
