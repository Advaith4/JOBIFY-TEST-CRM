---
title: Jobify OpenEnv
sdk: docker
app_port: 7860
tags:
  - openenv
  - hiring
  - evaluation
  - meta-openenv-hackathon
---

# Jobify.ai - AI Career Assistant (Copilot Edition)

Jobify is an AI-powered career assistant that analyzes resumes, suggests real job opportunities, improves resume quality, and supports interview preparation. The project now also includes an OpenEnv-compatible evaluation environment for the Meta OpenEnv Hackathon.

---

## Key Features

### 1. Real-Time Job Search
- Uses the JSearch API through RapidAPI to fetch live job postings.
- Infers best-fit roles from a resume before retrieval.
- Ranks only real fetched jobs to reduce hallucinated recommendations.

### 2. Resume Optimization
- Analyzes resume quality for ATS and recruiter friendliness.
- Rewrites weak bullet points into stronger action-oriented content.

### 3. Interactive Interview Support
- Generates realistic interview questions.
- Evaluates answers and adapts question difficulty.

### 4. OpenEnv Evaluation Layer
- Wraps the existing Jobify logic into benchmarkable tasks.
- Provides deterministic grading and reproducible baseline scoring.

---

## Tech Stack

### Backend
- Python 3.10+
- FastAPI / Uvicorn
- CrewAI
- OpenAI-compatible client for baseline inference
- Groq-powered existing Jobify agents

### Utilities
- pypdf
- python-dotenv
- requests
- pydantic

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
HF_TOKEN=your_huggingface_token
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
API_BASE_URL=https://router.huggingface.co/v1
LOCAL_IMAGE_NAME=optional_local_image_name
```

### 5. Run the Main App
```bash
venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open:
`http://127.0.0.1:8000`

---

# OpenEnv Integration

## Overview and Motivation
`JobifyEnv` converts the existing Jobify project into an OpenEnv-compatible evaluation benchmark for real hiring workflows. Instead of using toy problems, the environment evaluates realistic tasks humans and AI systems perform in recruiting pipelines:
- extracting skills from resumes
- matching a candidate to a role
- improving resume quality for hiring outcomes

This makes the project relevant to the OpenEnv hackathon because it measures useful real-world assistant behavior in a structured, reproducible way.

## OpenEnv Interface
The environment implements:
- typed `Observation`, `Action`, and `Reward` models using Pydantic
- `reset()` to start a task
- `step(action)` to advance the trajectory
- `state()` to inspect current environment state
- baseline inference config via `HF_TOKEN`, `API_BASE_URL`, and `MODEL_NAME`

## Observation Space
Each observation contains:
- `task_id`
- `difficulty`
- `prompt`
- `expected_schema`
- `attempt`
- `remaining_attempts`
- `feedback`

## Action Space
Each action is a text response:
- `response`

The agent is expected to return JSON matching the task schema.

## Reward Space
Each reward contains:
- `score`
- `correctness`
- `relevance`
- `clarity`
- `progress`
- `penalty`

Reward is computed as:
`0.4 * correctness + 0.3 * relevance + 0.3 * clarity`

The environment also:
- rewards incremental progress through revision attempts
- penalizes blank actions
- penalizes repeated unchanged responses

## Tasks
### EASY - Skill Extraction
Objective:
Extract the candidate's core technical skills from a resume.

Reused modules:
- `utils.resume_parser`
- `utils.skill_scorer`

### MEDIUM - Job Matching
Objective:
Compare resume skills against a target backend job and estimate fit.

Reused modules:
- `utils.skill_scorer`
- `agents.skill_matcher`

### HARD - Resume Optimization
Objective:
Identify weaknesses and rewrite resume bullets to make them stronger for ATS and recruiter review.

Reused modules:
- `agents.resume_optimizer`
- `tasks.resume_task`

## Grading
Each task has a deterministic programmatic grader that scores from `0.0` to `1.0`.

The graders use:
- keyword overlap
- semantic relevance through normalized text matching
- presence of action verbs like `developed`, `built`, `improved`
- measurable impact such as numbers or percentages

## Incremental Reward Workflow
The environment supports short trajectories.
If the first answer is weak, the agent receives feedback and can revise the answer on the next step.
This makes the reward more meaningful than simple one-shot pass/fail grading.

## Baseline Inference
Run the OpenEnv baseline:

```bash
python -m openenv.inference
```

It uses:
- OpenAI client
- `HF_TOKEN` from environment variables
- `API_BASE_URL` and `MODEL_NAME` with safe defaults
- deterministic task ordering
- `temperature=0` for reproducibility

## Example Baseline Output
```text
Task: skill_extraction
Attempt Rewards: [0.71, 0.82]
Final Reward: 0.8200
Task: job_matching
Attempt Rewards: [0.73, 0.85]
Final Reward: 0.8500
Task: resume_optimization
Attempt Rewards: [0.69, 0.78]
Final Reward: 0.7800
Baseline Score: 0.8167
```

## Run with Docker
Build:
```bash
docker build -t jobify-openenv .
```

Run:
```bash
docker run --env-file .env -p 7860:7860 jobify-openenv
```

For Hugging Face Spaces:
- the repo README includes Docker Space metadata
- the Space can be tagged with `openenv`
- the container serves the main app on port `7860`

## Submission Notes
- `openenv.yaml` contains environment metadata
- the project includes a working Dockerfile
- the OpenEnv wrapper reuses existing project logic instead of replacing it
- the benchmark tasks are realistic, deterministic, and increasing in difficulty
