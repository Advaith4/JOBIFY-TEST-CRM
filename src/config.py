from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    # --- App ---
    APP_NAME: str = "Jobify AI CRM"
    DEBUG: bool = False

    # --- AI Keys ---
    GROQ_API_KEY: str = ""
    JOOBLE_API_KEY: str = ""
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

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return False

        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
            return True
        if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
            return False
        return False

settings = Settings()
