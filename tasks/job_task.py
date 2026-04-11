"""
job_task.py – CrewAI task definitions for the Hybrid RAG job pipeline.

Phase 1: Role inference  → LLM reads resume, returns best-fit roles as JSON.
Phase 2: RAG ranking     → LLM receives REAL fetched jobs, returns ranked TOP-5 JSON.
                           LLM NEVER generates job data; it only filters/ranks.
"""
import json
from crewai import Task


def create_role_inference_task(agent, resume_content: str) -> Task:
    """
    Phase 1: Identify the candidate's primary domain and 5 best-fit roles.
    """
    description = (
        "Analyze the resume below and identify the 5 best entry-level / internship "
        "job roles for this candidate.\n\n"

        "CANDIDATE RESUME:\n"
        "---------------------\n"
        f"{resume_content[:2000]}\n"
        "---------------------\n\n"

        "STEP 1 — Find the PRIMARY DOMAIN:\n"
        "Look at the candidate's projects (most important), skills, and experience. "
        "Identify their single dominant domain, for example:\n"
        "  • Mobile (Flutter, Android, iOS, React Native)\n"
        "  • Web Frontend (React, Vue, Angular, Next.js)\n"
        "  • Web Backend (Node.js, Django, FastAPI, Spring)\n"
        "  • Data / ML (Python, TensorFlow, scikit-learn, pandas)\n"
        "  • DevOps / Cloud (AWS, Docker, Kubernetes)\n\n"

        "STEP 2 — Suggest 5 roles WITHIN that domain ONLY:\n"
        "All 5 roles must use the candidate's primary tech stack. "
        "DO NOT cross domains. For example: if Flutter/mobile is primary, "
        "suggest ONLY mobile roles (Flutter Developer, Mobile App Developer, "
        "Cross-Platform Developer, Android Developer, React Native Developer). "
        "NEVER suggest Data Scientist, ML Engineer, DB Developer, or UI/UX "
        "unless those are clearly the candidate's primary domain.\n\n"

        "Return ONLY valid JSON (no extra text):\n"
        '{"roles": ["Role 1", "Role 2", "Role 3", "Role 4", "Role 5"]}\n\n'

        "Rules:\n"
        "- Entry-level, junior, or internship only\n"
        "- Be specific (e.g. 'Junior Flutter Developer', not just 'Developer')\n"
        "- All 5 roles within the same primary domain\n"
        "- No senior or lead positions\n"
        "- Valid JSON only, no markdown"
    )

    return Task(
        description=description,
        expected_output='JSON: {"roles": ["role1", "role2", "role3", "role4", "role5"]}',
        agent=agent,
    )


def create_job_ranking_task(agent, resume_content: str, real_jobs: list[dict]) -> Task:
    """
    Phase 2 — Hybrid RAG Ranking Task.

    The LLM receives a curated list of REAL jobs fetched from JSearch API.
    Its ONLY job is to select and rank the TOP 5 most relevant ones.
    It must NOT invent new jobs, modify URLs, or add jobs not in the list.

    real_jobs: list of {title, company, url, location, description}
    """
    # Serialize real jobs into a compact numbered block for the prompt.
    # Cap at 10 jobs and 250-char descriptions to stay inside Groq's 6000 TPM free-tier limit.
    capped_jobs = real_jobs[:10]
    jobs_block_lines = []
    for i, job in enumerate(capped_jobs, start=1):
        desc = (job.get('description') or '')[:250].replace('\n', ' ')
        jobs_block_lines.append(
            f"[{i}] title: {job.get('title', '')} | company: {job.get('company', '')} "
            f"| location: {job.get('location', '')} | url: {job.get('url', '')} "
            f"| desc: {desc}"
        )
    jobs_block = "\n".join(jobs_block_lines) if jobs_block_lines else "(No jobs fetched)"

    description = (
        "You are a job recommendation engine operating in STRICT RAG mode.\n\n"

        "═══════════════════════════════════════════════════════\n"
        "⚠️  CRITICAL RULES — READ BEFORE ANYTHING ELSE:\n"
        "  1. You MUST only use jobs from the REAL JOB LISTINGS section below.\n"
        "  2. You MUST NEVER invent, create, or hallucinate any job.\n"
        "  3. You MUST copy the 'url' field EXACTLY as given — do NOT modify it.\n"
        "  4. You MUST return ONLY valid JSON — no markdown, no prose.\n"
        "  5. If fewer than 5 real jobs are relevant, return only those that are.\n"
        "═══════════════════════════════════════════════════════\n\n"

        "CANDIDATE RESUME:\n"
        "---------------------\n"
        f"{resume_content[:1500]}\n"
        "---------------------\n\n"

        "REAL JOB LISTINGS (fetched live from JSearch API — these are the ONLY valid jobs):\n"
        "─────────────────────────────────────────────────────────────────────────────────\n"
        f"{jobs_block}\n"
        "─────────────────────────────────────────────────────────────────────────────────\n\n"

        "YOUR TASK:\n"
        "Select the TOP 5 most relevant jobs from the list above for this candidate.\n"
        "For each selected job:\n"
        "  - Copy title, company, url, location EXACTLY as shown above.\n"
        "  - Write a 'reason' (1-2 sentences) explaining WHY this specific job "
        "fits this specific candidate's skills and experience.\n"
        "  - Compute 'match_score' (integer 0-100) based on how well the candidate's "
        "skills align with the job description. Be honest and precise.\n"
        "  - List 'matched_skills': skills from the resume that match this job.\n"
        "  - List 'missing_skills': skills the job requires that are NOT in the resume.\n\n"

        "REQUIRED OUTPUT FORMAT (strict JSON only — no text before or after):\n"
        "{\n"
        '  "suggested_roles": ["role1", "role2"],\n'
        '  "jobs": [\n'
        '    {\n'
        '      "role": "exact title from listing above",\n'
        '      "company": "exact company from listing above",\n'
        '      "link": "exact url from listing above — do NOT change",\n'
        '      "location": "exact location from listing above",\n'
        '      "reason": "why this job fits this candidate",\n'
        '      "matched_skills": ["skill1", "skill2"],\n'
        '      "missing_skills": ["skill3"],\n'
        '      "match_score": 78\n'
        '    }\n'
        '  ]\n'
        "}\n\n"

        "VALIDATION CHECKLIST (enforce before responding):\n"
        "  ✅ Every url/link value is copied verbatim from the listing\n"
        "  ✅ No job exists in output that wasn't in the listing above\n"
        "  ✅ match_score is an integer between 0 and 100\n"
        "  ✅ Output is valid JSON with double quotes, no trailing commas\n"
        "  ✅ 'reason' field is present for every job"
    )

    return Task(
        description=description,
        expected_output=(
            "Valid JSON with suggested_roles and up to 5 jobs. Each job has: "
            "role, company, link (verbatim from API), location, reason, "
            "matched_skills, missing_skills, match_score (integer)."
        ),
        agent=agent,
    )