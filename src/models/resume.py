from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

class Resume(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    raw_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
