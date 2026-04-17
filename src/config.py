import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "Jobify AI CRM"
    DEBUG: bool = False

    # --- AI Keys ---
    GROQ_API_KEY: str = ""
    RAPIDAPI_KEY: str = ""
    MODEL_NAME: str = "llama-3.1-8b-instant"

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./jobify.db"

    # --- JWT ---
    SECRET_KEY: str = "change-me-in-production-min-32-chars!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # --- CORS ---
    ALLOWED_ORIGINS: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
