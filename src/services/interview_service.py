from sqlmodel import Session, select
from fastapi import HTTPException
from src.models.domain import User, InterviewSession
from src.models.schemas import InterviewStartReq, InterviewAnswerReq
import json

from crew import run_interview_start, run_interview_answer

def start_interview_session(db: Session, user: User, req: InterviewStartReq) -> dict:
    try:
        # Call legacy ai logic for first question
        results = run_interview_start(req.role, req.difficulty, req.weak_areas)
        first_q = results.get("question", "Tell me about yourself.")
        
        # Initialize robust DB session state instead of volatile memory dict
        initial_history = [
            {"role": "system", "content": "Interview Started"},
            {"role": "ai", "content": first_q}
        ]
        
        db_session = InterviewSession(
            user_id=user.id,
            role_focused=req.role,
            difficulty=req.difficulty,
            chat_history=json.dumps(initial_history)
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        return {"session_id": db_session.id, "question": first_q}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def answer_interview_question(db: Session, user: User, req: InterviewAnswerReq) -> dict:
    session_record = db.get(InterviewSession, req.session_id)
    if not session_record or session_record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found or forbidden")
    
    if not req.answer.strip():
        raise HTTPException(status_code=400, detail="Answer cannot be empty.")
        
    chat_history = json.loads(session_record.chat_history)
    # The last question asked by AI
    current_question = chat_history[-1]["content"] if chat_history else ""
    
    try:
        # Call legacy multi-agent logic
        results = run_interview_answer(
            role=session_record.role_focused,
            question=current_question,
            answer=req.answer,
            current_diff=session_record.difficulty
        )
        
        # Extract evaluated metrics
        eval_score = results.get("evaluation", {}).get("score", 5)
        new_diff = results.get("new_difficulty", session_record.difficulty)
        next_q = results.get("next_question", "Thank you, that's all.")
        
        try:
            new_diff = int(new_diff)
            session_record.difficulty = max(1, min(10, new_diff))
        except (ValueError, TypeError):
            pass
            
        # Append to safely saved JSON history
        chat_history.append({"role": "user", "content": req.answer, "score": eval_score})
        chat_history.append({"role": "ai", "content": next_q})
        
        session_record.chat_history = json.dumps(chat_history)
        db.add(session_record)
        db.commit()
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
