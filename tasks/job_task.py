"""
job_task.py - CrewAI task definitions for the hybrid RAG job pipeline.

Phase 1: role inference -> identify realistic adjacent role targets.
Phase 2: ranking -> score and explain only REAL fetched jobs.
"""

import json

from crewai import Task


def create_role_inference_task(agent, resume_content: str, profile_context: dict | None = None) -> Task:
    """Phase 1: identify a realistic and diverse role mix."""
    profile_context = profile_context or {}
    description = (
        "You are Jobify's AI career coach. Analyze the candidate profile and select the 5 most realistic roles "
        "they should target right now.\n\n"
        "CANDIDATE RESUME:\n"
        "---------------------\n"
        f"{resume_content[:2000]}\n"
        "---------------------\n\n"
        "PROFILE CONTEXT:\n"
        "---------------------\n"
        f"{json.dumps(profile_context, ensure_ascii=False)}\n"
        "---------------------\n\n"
        "ROLE SELECTION RULES:\n"
        "- Use resume strengths, project evidence, skills, and weak signals together.\n"
        "- Pick entry-level, junior, or internship roles only.\n"
        "- Create variation across 2-3 adjacent title families when justified.\n"
        "- Avoid duplicates that are the same role with tiny wording changes.\n"
        "- Prefer roles that would lead to distinct live job searches.\n"
        "- Mix safer and slightly stretch roles if the resume supports it.\n"
        "- Example for a data-heavy profile: Data Analyst, Junior Data Scientist, ML Engineer Intern.\n"
        "- Example for a backend-heavy profile: Backend Engineer, API Developer, Platform Engineer Intern.\n"
        "- No senior, lead, architect, or staff roles.\n\n"
        "Return ONLY valid JSON:\n"
        '{"roles": ["Role 1", "Role 2", "Role 3", "Role 4", "Role 5"]}'
    )

    return Task(
        description=description,
        expected_output='JSON: {"roles": ["role1", "role2", "role3", "role4", "role5"]}',
        agent=agent,
    )


def create_job_ranking_task(
    agent,
    resume_content: str,
    real_jobs: list[dict],
    profile_context: dict | None = None,
) -> Task:
    """Phase 2: rank only fetched jobs and explain fit, gaps, and next steps."""
    profile_context = profile_context or {}
    capped_jobs = real_jobs[:10]
    jobs_block_lines = []
    for i, job in enumerate(capped_jobs, start=1):
        desc = (job.get("description") or "")[:220].replace("\n", " ")
        jobs_block_lines.append(
            f"[{i}] title: {job.get('title', '')} | company: {job.get('company', '')} "
            f"| location: {job.get('location', '')} | url: {job.get('url', '')} "
            f"| source_role: {job.get('source_role', '')} | desc: {desc}"
        )
    jobs_block = "\n".join(jobs_block_lines) if jobs_block_lines else "(No jobs fetched)"

    description = (
        "You are Jobify's personalized job recommendation engine operating in STRICT RAG mode.\n\n"
        "CRITICAL RULES:\n"
        "1. You MUST only use jobs from the REAL JOB LISTINGS section below.\n"
        "2. You MUST NEVER invent or hallucinate any job.\n"
        "3. You MUST copy the url field EXACTLY as given.\n"
        "4. You MUST return ONLY valid JSON.\n"
        "5. If fewer than 5 jobs are relevant, return only those.\n\n"
        "CANDIDATE RESUME:\n"
        "---------------------\n"
        f"{resume_content[:1400]}\n"
        "---------------------\n\n"
        "PROFILE CONTEXT:\n"
        "---------------------\n"
        f"{json.dumps(profile_context, ensure_ascii=False)}\n"
        "---------------------\n\n"
        "REAL JOB LISTINGS:\n"
        "---------------------\n"
        f"{jobs_block}\n"
        "---------------------\n\n"
        "YOUR TASK:\n"
        "Select the TOP 5 most relevant jobs from the list above.\n"
        "Prefer role diversity when match quality is similar. If two jobs are strong but nearly the same role family, "
        "keep the better one and use another strong job from a different family when available.\n"
        "For each selected job:\n"
        "- Copy title, company, url, and location EXACTLY as shown above.\n"
        "- Write why_match: 1-2 sentences explaining why this specific role fits the candidate.\n"
        "- Write gap_summary: 1 short sentence describing what the candidate lacks or has not clearly proven yet.\n"
        "- Write improvement_plan: 1 short sentence telling the candidate how to close that gap.\n"
        "- Compute match_score as an integer from 0 to 100.\n"
        "- List matched_skills from the resume that clearly align.\n"
        "- List missing_skills that seem necessary but are not clearly shown.\n"
        "- Set fit_bucket to one of: strong, close, stretch.\n\n"
        "REQUIRED OUTPUT FORMAT:\n"
        "{\n"
        '  "suggested_roles": ["role1", "role2"],\n'
        '  "jobs": [\n'
        '    {\n'
        '      "role": "exact title from listing above",\n'
        '      "company": "exact company from listing above",\n'
        '      "link": "exact url from listing above",\n'
        '      "location": "exact location from listing above",\n'
        '      "why_match": "why this job fits this candidate",\n'
        '      "gap_summary": "what the candidate lacks or has not proven yet",\n'
        '      "improvement_plan": "how the candidate should improve",\n'
        '      "matched_skills": ["skill1", "skill2"],\n'
        '      "missing_skills": ["skill3"],\n'
        '      "match_score": 78,\n'
        '      "fit_bucket": "close"\n'
        '    }\n'
        '  ]\n'
        "}\n\n"
        "VALIDATION CHECKLIST:\n"
        "- Every link is copied verbatim from the listing.\n"
        "- No output job exists outside the listing above.\n"
        "- match_score is an integer between 0 and 100.\n"
        "- why_match, gap_summary, and improvement_plan exist for every job."
    )

    return Task(
        description=description,
        expected_output=(
            "Valid JSON with suggested_roles and up to 5 jobs. Each job has role, company, link, location, "
            "why_match, gap_summary, improvement_plan, matched_skills, missing_skills, match_score, and fit_bucket."
        ),
        agent=agent,
    )
