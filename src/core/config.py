import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Jobify AI CRM"
    API_V1_STR: str = "/api/v1"
    
    # Supabase Database URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Auth & Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-please-change-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week
    
    # External APIs
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    JOOBLE_API_KEY: str = os.getenv("JOOBLE_API_KEY", "")
    RAPIDAPI_KEY: str = os.getenv("RAPIDAPI_KEY", "")
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
