"""
src/api/routes/interview.py
POST /api/interview/start         – start new session (persisted to DB)
POST /api/interview/answer        – submit answer, get eval + next question (persisted)
GET  /api/interview/sessions      – list all past sessions for current user
GET  /api/interview/sessions/{id} – get full message history of a session
"""
import uuid
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from src.database.connection import get_session
from src.models import InterviewSession, User
from src.api.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/interview", tags=["interview"])

# In-memory state for active sessions (fast access during live interview)
_sessions: dict[str, dict[str, Any]] = {}


class StartReq(BaseModel):
    role: str = Field(min_length=1, max_length=100)
    difficulty: int = Field(default=5, ge=1, le=10)
    weak_areas: list[str] = Field(default_factory=list)


class AnswerReq(BaseModel):
    session_id: str
    answer: str = Field(min_length=1, max_length=5000)


def _save_messages(db: Session, session_token: str, messages: list, avg_score: float | None = None):
    """Persist updated message list to DB."""
    rec = db.exec(select(InterviewSession).where(InterviewSession.session_token == session_token)).first()
    if rec:
        rec.messages = json.dumps(messages)
        rec.avg_score = avg_score
        rec.updated_at = datetime.utcnow()
        db.add(rec)
        db.commit()


@router.post("/start")
def start_interview(
    req: StartReq,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        from crew import run_interview_start
        result = run_interview_start(req.role, req.difficulty, req.weak_areas)
    except Exception as exc:
        logger.error("Interview start failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

    question = result.get("question", "")
    session_token = uuid.uuid4().hex

    # Persist to DB
    first_msg = {"role": "ai", "content": question, "timestamp": datetime.utcnow().isoformat()}
    db_session = InterviewSession(
        user_id=current_user.id,
        session_token=session_token,
        role=req.role,
        difficulty=req.difficulty,
        messages=json.dumps([first_msg]),
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    # Keep live state in memory
    _sessions[session_token] = {
        "role": req.role,
        "difficulty": req.difficulty,
        "weak_areas": req.weak_areas,
        "questions": [],
        "answers": [],
        "scores": [],
        "messages": [first_msg],
        "current_question": question,
        "db_id": db_session.id,
    }

    return {"session_id": session_token, "question": question, "db_id": db_session.id}


@router.post("/answer")
def submit_answer(
    req: AnswerReq,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    state = _sessions.get(req.session_id)
    if state is None:
        # Try to reload from DB (e.g. server restart)
        rec = db.exec(select(InterviewSession).where(InterviewSession.session_token == req.session_id)).first()
        if rec is None:
            raise HTTPException(status_code=400, detail="Invalid session ID. Please start a new interview.")
        msgs = json.loads(rec.messages)
        last_ai = next((m["content"] for m in reversed(msgs) if m["role"] == "ai"), "")
        state = {
            "role": rec.role, "difficulty": rec.difficulty, "weak_areas": [],
            "questions": [], "answers": [], "scores": [], "messages": msgs,
            "current_question": last_ai, "db_id": rec.id,
        }
        _sessions[req.session_id] = state

    try:
        from crew import run_interview_answer
        result = run_interview_answer(
            role=state["role"],
            question=state["current_question"],
            answer=req.answer,
            current_diff=state["difficulty"],
        )
    except Exception as exc:
        logger.error("Interview answer failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

    # Update in-memory state
    state["questions"].append(state["current_question"])
    state["answers"].append(req.answer)
    score = result.get("evaluation", {}).get("score", 5)
    state["scores"].append(score)

    new_diff = result.get("new_difficulty", state["difficulty"])
    try:
        new_diff = int(new_diff)
    except (TypeError, ValueError):
        new_diff = state["difficulty"]
    state["difficulty"] = max(1, min(10, new_diff))
    state["current_question"] = result.get("next_question", "")

    now = datetime.utcnow().isoformat()
    state["messages"].append({"role": "user", "content": req.answer, "timestamp": now})
    state["messages"].append({
        "role": "ai",
        "content": result.get("next_question", ""),
        "feedback": result.get("evaluation", {}).get("improvements", ""),
        "score": score,
        "timestamp": now,
    })

    avg = sum(state["scores"]) / len(state["scores"]) if state["scores"] else None
    _save_messages(db, req.session_id, state["messages"], avg)

    return result


@router.get("/sessions")
def list_sessions(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Return all past interview sessions for the sidebar, newest first."""
    records = db.exec(
        select(InterviewSession)
        .where(InterviewSession.user_id == current_user.id)
        .order_by(InterviewSession.created_at.desc())
    ).all()
    return [
        {
            "id": r.id,
            "session_token": r.session_token,
            "role": r.role,
            "difficulty": r.difficulty,
            "avg_score": r.avg_score,
            "status": r.status,
            "message_count": len(json.loads(r.messages)),
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]


@router.get("/sessions/{session_id}")
def get_session_history(
    session_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Return the full message log for a specific past session."""
    rec = db.get(InterviewSession, session_id)
    if not rec or rec.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {
        "id": rec.id,
        "role": rec.role,
        "difficulty": rec.difficulty,
        "avg_score": rec.avg_score,
        "status": rec.status,
        "messages": json.loads(rec.messages),
        "created_at": rec.created_at.isoformat(),
    }
