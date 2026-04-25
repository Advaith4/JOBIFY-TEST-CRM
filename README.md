# Jobify.ai — AI Career Assistant

Jobify is an AI-powered career assistant that analyzes resumes, finds real job opportunities, improves resume quality, and helps with mock interviews.

## Quick Start

Prerequisites
- Python 3.10+ (recommended)
- Git (optional)
- Optional: a PostgreSQL database (Supabase) if you want to persist users and applications

Install and run (Windows PowerShell)

```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& "venv\Scripts\Activate.ps1"
pip install -r requirements.txt
```

Run the app

```powershell
# Option A: run via uvicorn for autoreload
uvicorn app:app --reload --host 127.0.0.1 --port 8000

# Option B: run the packaged entrypoint
python app.py
```

Visit the web UI: http://localhost:8000

API docs (Swagger UI): http://localhost:8000/docs

Static preview (quick):

```powershell
python -m http.server 9000 --directory static
# then open http://localhost:9000
```

## Environment variables (.env)
Create a `.env` file in the project root with the following variables (examples shown earlier in the repo):

- `GROQ_API_KEY` — optional: Groq / external search API key
- `RAPIDAPI_KEY` — optional: RapidAPI key for job search providers
- `HF_TOKEN` — Hugging Face API token (if using HF router/model endpoints)
- `MODEL_NAME` — Model identifier (if applicable) used by CrewAI/agents
- `API_BASE_URL` — Optional alternate model router base URL
- `DATABASE_URL` — Your Postgres connection string (Supabase example):
	- Example: `postgresql://username:password@host:5432/postgres`
	- Note: `database.py` auto-replaces `postgres://` with `postgresql://` when needed.

If `DATABASE_URL` is not set, many endpoints will still run in a degraded mode (the app yields None session and returns friendly error messages).

## Project Structure (high level)
- `app.py` — FastAPI application and API routes
- `static/` — Frontend (HTML, CSS, JS)
- `templates/` — (not used) — frontend is static
- `database.py` — SQLModel/engine setup and `get_session()` dependency
- `models.py` — SQLModel domain models
- `agents/` — CrewAI agents and helper scripts used by the AI pipelines
- `requirements.txt` — Python dependencies
- `Dockerfile` — container build instructions (basic)

## Running with Docker
Build and run the image (example):

```bash
docker build -t jobify:local .
docker run -p 8000:8000 --env-file .env jobify:local
```

## Important Notes & Troubleshooting
- Port already in use: If port 8000 is occupied, stop the other process or change the port when running `uvicorn`.
- `psycopg2`/`psycopg2-binary`: The Postgres driver is required when `DATABASE_URL` points to Postgres. If you get `ModuleNotFoundError: No module named 'psycopg2'`, install `psycopg2-binary` in your environment.
- Supabase/Postgres connection strings sometimes start with `postgres://` — `database.py` converts that to `postgresql://` for SQLAlchemy compatibility.
- CrewAI and related ML dependencies are heavyweight; installation can take time and may require compiling native wheels on some platforms.
- If you plan to use hosted models (Hugging Face, etc.), make sure `HF_TOKEN` and `API_BASE_URL` are set correctly.

## Features
- Real-time job search and ranked matches
- Resume storage and automated text extraction
- Auto-tailoring of resume bullets for tracked jobs
- Interactive mock interview studio with scoring and feedback

## Contributing
- Fork, create a branch, and open a PR. Keep changes focused and include a short description of what you changed.

## License
See project root for license information (if any).

---
If you'd like, I can also add a short example showing how to call the `/api/jobs/feed/{user_id}` and `/api/interview/start` endpoints.
- Select target roles and difficulty (1-10) to initiate a dynamic AI examiner.
- The AI evaluates answers logically in real-time, assigning a score and formulating targeted follow-up questions autonomously.

---

## Tech Stack

### Backend
- Python 3.10+
- FastAPI & Uvicorn (REST endpoints)
- SQLModel/SQLite (Lightweight relational CRM tracking)
- CrewAI (LLM Orchestration)
- Groq-powered endpoints for massive multi-agent throughput

### Frontend
- Premium Glassmorphic Split-Pane UI (Vanilla HTML/CSS/JS)
- Real-time client-side navigation (Dashboard, Feed, Studio, Tracker)
- Dynamic DOM insertion & cache busting mechanisms

### Utilities
- pypdf
- python-dotenv
- requests

---

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/Advaith4/JOBIFY.git
cd JOBIFY
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
```

Windows:
```bash
venv\Scripts\activate
```

macOS/Linux:
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key
JOOBLE_API_KEY=your_jooble_api_key
JOOBLE_API_BASE_URL=https://in.jooble.org/api/{api_key}
RAPIDAPI_KEY=your_rapidapi_key
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
```

`JOOBLE_API_KEY` is now the preferred jobs provider key. `RAPIDAPI_KEY` is optional and is only used as fallback for JSearch.
`JOOBLE_API_BASE_URL` defaults to the India Jooble endpoint shown above.

### 5. Run the Main App
```bash
venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open:
`http://127.0.0.1:8000`

---

## Run with Docker
Build:
```bash
docker build -t jobify .
```

Run:
```bash
docker run --env-file .env -p 7860:7860 jobify
```
