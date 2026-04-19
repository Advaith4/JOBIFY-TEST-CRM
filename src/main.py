"""
src/main.py
FastAPI application entry point.

Run locally:
    uvicorn src.main:app --reload --port 8000
Docker:
    CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
import logging
import os
import sys
import io
from contextlib import asynccontextmanager
from pathlib import Path

# Force UTF-8 output on Windows to prevent emoji/unicode crashes
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def _disable_broken_local_proxies() -> None:
    """
    Some Windows setups inject dead proxy vars like 127.0.0.1:9, which break
    outbound HTTP for Groq, Jooble, RapidAPI, and related SDKs. Clear only
    those known-bad values and leave legitimate proxy configs untouched.
    """
    proxy_vars = (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "GIT_HTTP_PROXY",
        "GIT_HTTPS_PROXY",
    )
    bad_markers = ("127.0.0.1:9", "localhost:9")

    for var in proxy_vars:
        value = os.getenv(var, "")
        if value and any(marker in value for marker in bad_markers):
            os.environ.pop(var, None)


_disable_broken_local_proxies()

import appdirs
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config import settings
from src.database.connection import create_db_and_tables
from src.core.exceptions import http_exception_handler, validation_exception_handler
from src.api.routes import auth, resume, jobs, interview

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── CrewAI storage isolation ──────────────────────────────────────────────────
def _prepare_crewai_storage() -> None:
    os.environ.setdefault("CREWAI_STORAGE_DIR", "jobify_local")
    os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
    os.environ.setdefault("CREWAI_DISABLE_TRACKING", "true")
    storage_root = Path.cwd() / "data" / ".crewai_storage"
    storage_root.mkdir(parents=True, exist_ok=True)
    appdirs.user_data_dir = lambda appname=None, appauthor=None, version=None, roaming=False: str(
        storage_root / (appauthor or "CrewAI") / (appname or "jobify_local")
    )

_prepare_crewai_storage()

# ── App lifecycle ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Jobify AI CRM...")
    create_db_and_tables()
    yield
    logger.info("Shutting down.")

# ── Application factory ───────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception Handlers ────────────────────────────────────────────────────────
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# ── API Routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(resume.router)
app.include_router(jobs.router)
app.include_router(interview.router)

# ── Static Frontend (must be LAST) ────────────────────────────────────────────
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
