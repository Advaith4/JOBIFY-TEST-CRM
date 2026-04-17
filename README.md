# Jobify.ai - AI Career Assistant (Copilot Edition)

Jobify is an AI-powered career assistant that analyzes resumes, suggests real job opportunities, improves resume quality, and supports interview preparation.

---

## Key Features

### 1. Real-Time Job Search
- Uses the JSearch API through RapidAPI to fetch live job postings.
- Infers best-fit roles from a resume before retrieval.
- Ranks only real fetched jobs to reduce hallucinated recommendations.

### 2. Job Tracker & Resume Auto-Tailor
- Track incoming job URLs into a personal SQLModel CRM database.
- Uses CrewAI agents to completely rewrite your resume bullets specific to individual job descriptions on the fly.
- Secure, token-based (UUID/DB) UI for managing pending application statuses.

### 3. Interactive Mock Interview Studio
- Fully functional Vanilla JS + Glassmorphic UI chatbot interface.
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
RAPIDAPI_KEY=your_rapidapi_key
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
```

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
