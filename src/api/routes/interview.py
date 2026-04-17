"""
src/api/routes/interview.py
POST /api/interview/start   – start a new interview session
POST /api/interview/answer  – submit answer, get evaluation + next question
"""
import uuid
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/interview", tags=["interview"])

# In-memory session store (upgrade to Redis for multi-instance production)
_sessions: dict[str, dict[str, Any]] = {}


class StartReq(BaseModel):
    role: str = Field(min_length=1, max_length=100)
    difficulty: int = Field(default=5, ge=1, le=10)
    weak_areas: list[str] = Field(default_factory=list)


class AnswerReq(BaseModel):
    session_id: str
    answer: str = Field(min_length=1, max_length=5000)


@router.post("/start")
def start_interview(req: StartReq):
    try:
        from crew import run_interview_start
        result = run_interview_start(req.role, req.difficulty, req.weak_areas)
    except Exception as exc:
        logger.error("Interview start failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

    session_id = uuid.uuid4().hex
    _sessions[session_id] = {
        "role": req.role,
        "difficulty": req.difficulty,
        "weak_areas": req.weak_areas,
        "questions": [],
        "answers": [],
        "scores": [],
        "current_question": result.get("question"),
    }
    return {"session_id": session_id, "question": result.get("question")}


@router.post("/answer")
def submit_answer(req: AnswerReq):
    session = _sessions.get(req.session_id)
    if session is None:
        raise HTTPException(status_code=400, detail="Invalid session ID. Please start a new interview.")

    try:
        from crew import run_interview_answer
        result = run_interview_answer(
            role=session["role"],
            question=session["current_question"],
            answer=req.answer,
            current_diff=session["difficulty"],
        )
    except Exception as exc:
        logger.error("Interview answer failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

    session["questions"].append(session["current_question"])
    session["answers"].append(req.answer)
    session["scores"].append(result.get("evaluation", {}).get("score", 5))

    new_diff = result.get("new_difficulty", session["difficulty"])
    try:
        new_diff = int(new_diff)
    except (TypeError, ValueError):
        new_diff = session["difficulty"]
    session["difficulty"] = max(1, min(10, new_diff))
    session["current_question"] = result.get("next_question")

    return result
