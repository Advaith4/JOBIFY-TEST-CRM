from sqlmodel import Session, select
from fastapi import HTTPException, status
from src.models.domain import User, Resume
from src.models.schemas import LoginReq, TokenResponse
from src.core.security import verify_password, get_password_hash, create_access_token

def authenticate_or_register_user(db: Session, req: LoginReq) -> TokenResponse:
    user = db.exec(select(User).where(User.username == req.username)).first()
    
    if not user:
        # For seamless UX, auto-register if completely new
        hashed_pw = get_password_hash(req.password)
        user = User(username=req.username, hashed_password=hashed_pw)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Validate password if user exists
        if not verify_password(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )
            
    access_token = create_access_token(subject=user.id)
    
    # Check if they have a saved resume
    resume = db.exec(select(Resume).where(Resume.user_id == user.id)).first()
    has_resume = resume is not None
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        username=user.username,
        has_resume=has_resume
    )
