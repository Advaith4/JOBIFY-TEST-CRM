"""
crew.py – Orchestrates the Hybrid RAG job recommendation pipeline.

Pipeline (run_job_crew):
  Phase 1 — LLM infers the 5 best-fit roles from the resume.
  Phase 2 — JSearch API fetches REAL job listings for those roles.
  Phase 3 — LLM ranks/filters real jobs (RAG mode — zero hallucination).

Parallel execution:
  job_crew, resume_crew, interview_crew run concurrently via ThreadPoolExecutor.
  Blocking time.sleep calls have been removed.
"""

import logging
import re
import json
import uuid
import concurrent.futures
import time

from crewai import Crew

# ── Agents ─────────────────────────────────────────────────────────────────
from agents.job_finder import create_job_finder
from agents.resume_optimizer import create_resume_optimizer, create_resume_rewriter
from agents.interview_coach import (
    create_interview_coach, 
    create_interviewer, 
    create_evaluator, 
    create_followup_coach, 
    create_difficulty_controller
)

# ── Tasks ──────────────────────────────────────────────────────────────────
from tasks.job_task import create_role_inference_task, create_job_ranking_task
from tasks.resume_task import create_resume_task, create_resume_analysis_task, create_bullet_rewriting_task
from tasks.interview_task import (
    create_interview_task, 
    create_interview_start_task, 
    create_evaluator_task, 
    create_followup_task, 
    create_difficulty_task
)

# ── Utils ──────────────────────────────────────────────────────────────────
from utils.skill_scorer import get_priority, generate_action_plan
from utils.job_search import fetch_jobs_for_roles

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────

def extract_json(raw: str, task_name="LLM") -> dict | None:
    logger.debug("%s Raw Output Length: %d", task_name, len(raw) if raw else 0)
    """
    Safely extract the first JSON object from ANY messy LLM output.
    Strategy:
      1. Try direct parse.
      2. Regex-extract the outermost {...} block and retry.
      3. Return None on failure so callers can apply safe fallbacks.
    """
    if not raw:
        return None

    # 1. Direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 2. Regex extraction — find the outermost JSON object
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

    logger.warning("extract_json: could not parse JSON from LLM output (len=%d)", len(raw))
    return None


def _is_valid_url(url: str) -> bool:
    """Return True if url looks like a real https link."""
    return isinstance(url, str) and url.startswith("https://") and len(url) > 15


_TITLE_NOISE_WORDS = {
    "junior", "intern", "internship", "entry", "level", "fresher", "remote",
    "full", "time", "contract", "opening", "hiring", "urgent",
}


def _normalize_title_family(title: str) -> str:
    normalized = re.sub(r"[^a-z0-9\s/+&-]", " ", (title or "").lower())
    tokens = [token for token in normalized.split() if token and token not in _TITLE_NOISE_WORDS]
    family = " ".join(tokens[:6]).strip()
    return family or normalized.strip()


def _dedupe_roles(roles: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for role in roles:
        role_name = str(role or "").strip()
        if not role_name:
            continue
        family = _normalize_title_family(role_name)
        if family in seen:
            continue
        seen.add(family)
        deduped.append(role_name)
    return deduped


def _select_diverse_jobs(jobs: list[dict], limit: int, max_per_title_family: int = 2) -> list[dict]:
    selected: list[dict] = []
    deferred: list[dict] = []
    family_count: dict[str, int] = {}

    for job in jobs:
        family = _normalize_title_family(job.get("role") or job.get("title") or "")
        if family_count.get(family, 0) >= max_per_title_family:
            deferred.append(job)
            continue
        family_count[family] = family_count.get(family, 0) + 1
        selected.append(job)
        if len(selected) >= limit:
            return selected

    for job in deferred:
        selected.append(job)
        if len(selected) >= limit:
            break

    return selected


def _validate_and_score_jobs(jobs: list[dict], all_real_jobs: list[dict]) -> list[dict]:
    """
    Post-process pipeline:
      1. Reject any job whose link is not in the set of API-fetched URLs.
      2. Validate and clamp match_score.
      3. Compute priority + action_plan.
      4. Ensure matched_skills / missing_skills exist.

    Returns only verified, scored jobs sorted best-first.
    """
    # Build a whitelist of real API URLs (lowercased for comparison)
    real_urls: set[str] = {j["url"].lower() for j in all_real_jobs if j.get("url")}

    verified: list[dict] = []
    for job in jobs:
        link = job.get("link") or job.get("url") or ""

        # ── Hallucination guard: reject if URL wasn't from the API ──────────
        if not _is_valid_url(link):
            logger.warning("Dropping job '%s' — link is not a valid URL: %s",
                           job.get("role", "?"), link)
            continue
        if link.lower() not in real_urls:
            logger.warning("Dropping job '%s' — link not in API results (possible hallucination): %s",
                           job.get("role", "?"), link)
            continue

        # ── match_score: validate and clamp ─────────────────────────────────
        try:
            score = int(job.get("match_score", 0))
            score = max(0, min(100, score))
        except (TypeError, ValueError):
            score = 0
        job["match_score"] = score
        job["priority"] = get_priority(score)
        job["action_plan"] = generate_action_plan(score, job.get("missing_skills", []))

        # ── Ensure skill lists exist ─────────────────────────────────────────
        job.setdefault("matched_skills", [])
        job.setdefault("missing_skills", [])
        job.setdefault("reason", "")

        # ── Normalise field name (LLM sometimes uses 'url' instead of 'link') ─
        job["link"] = link

        verified.append(job)

    # Sort best-matching first
    verified.sort(key=lambda j: j["match_score"], reverse=True)
    return _select_diverse_jobs(verified, limit=len(verified), max_per_title_family=2)


def run_with_retries(func, *args):
    """Exponential backoff for rate-limited LLM APIs (Groq 6000 TPM limit)."""
    for attempt in range(4):
        try:
            return func(*args)
        except Exception as exc:
            err = str(exc).lower()
            if "rate limit" in err or "429" in err or "decommission" in err:
                import re
                match = re.search(r"try again in ([0-9.]+)s", err)
                if match:
                    delay = float(match.group(1)) + 2.0
                else:
                    delay = 20 * (attempt + 1)
                logger.warning("Rate limit hit in %s. Retrying in %.1fs... (attempt %d/4)",
                               func.__name__, delay, attempt + 1)
                time.sleep(delay)
            else:
                raise
    return func(*args)


# ── Job Pipeline ───────────────────────────────────────────────────────────

def run_job_crew(resume_content: str, prefs: dict = None) -> dict:
    """
    Hybrid RAG job recommendation pipeline:

      Phase 1 — LLM infers 5 best roles from resume.
      Phase 2 — JSearch API fetches REAL jobs for those roles.
      Phase 3 — LLM ranks/filters real jobs (Hybrid RAG — no hallucination).
    """
    agent = create_job_finder()
    run_id = uuid.uuid4().hex[:8]

    # ── Phase 1: Role Inference ──────────────────────────────────────────────
    logger.info("[%s] Phase 1: Inferring best job roles from resume...", run_id)
    infer_task = create_role_inference_task(agent, resume_content)
    infer_crew = Crew(agents=[agent], tasks=[infer_task], verbose=False)
    infer_result = infer_crew.kickoff()
    infer_raw = getattr(infer_result, "raw", str(infer_result)).strip()
    infer_data = extract_json(infer_raw)

    if infer_data and isinstance(infer_data.get("roles"), list) and infer_data["roles"]:
        roles = _dedupe_roles([str(r) for r in infer_data["roles"] if r])[:5]
    else:
        roles = [
            "Junior Software Developer",
            "Backend Developer Intern",
            "Frontend Developer Intern",
            "Data Analyst Intern",
            "Machine Learning Intern",
        ]
        logger.warning("[%s] Role inference failed — using fallback roles.", run_id)

    logger.info("[%s] Inferred roles: %s", run_id, roles)

    # ── Phase 2: Fetch REAL Jobs from JSearch API ────────────────────────────
    logger.info("[%s] Phase 2: Fetching real job listings from JSearch API...", run_id)
    real_jobs = fetch_jobs_for_roles(roles, prefs=prefs, jobs_per_role=5)
    logger.info("[%s] Fetched %d unique real jobs.", run_id, len(real_jobs))

    # Hard fallback: if API fails entirely, return structured empty result
    if not real_jobs:
        logger.error("[%s] JSearch API returned no jobs. Returning empty result.", run_id)
        return {
            "suggested_roles": roles,
            "jobs": [],
            "message": "No relevant jobs found",
            "_warning": "Could not fetch live job data. Check JOOBLE_API_KEY or RAPIDAPI_KEY and connectivity.",
        }

    # ── Phase 2.5: Pre-scoring (Rule-based logic to select top 10) ──────────
    # Extract generic skills/keywords from resume (words > 4 chars) to prescore
    skills_extracted = set(re.findall(r'\b[a-zA-Z]{5,}\b', resume_content.lower()))
    
    def score_job(job, skills):
        score = 0
        description = (job.get("description") or "").lower()
        title = (job.get("title") or "").lower()
        text_to_search = title + " " + description
        for skill in skills:
            if skill in text_to_search:
                score += 1
        return score

    real_jobs = sorted(real_jobs, key=lambda j: score_job(j, skills_extracted), reverse=True)
    real_jobs = _select_diverse_jobs(real_jobs, limit=10, max_per_title_family=2)
    logger.info("[%s] Pre-scored top 10 jobs selected.", run_id)

    # ── Phase 3: Hybrid RAG — LLM ranks ONLY real jobs ──────────────────────
    logger.info("[%s] Phase 3: LLM ranking %d real jobs (RAG mode)...", run_id, len(real_jobs))
    rank_task = create_job_ranking_task(agent, resume_content, real_jobs)
    rank_crew = Crew(agents=[agent], tasks=[rank_task], verbose=False)
    rank_result = rank_crew.kickoff()
    raw = getattr(rank_result, "raw", str(rank_result)).strip()

    data = extract_json(raw)
    if not data or not isinstance(data.get("jobs"), list):
        logger.warning("[%s] LLM ranking output parse failed — applying safe fallback.", run_id)
        data = {"suggested_roles": roles, "jobs": []}

    # ── Validation & Scoring ─────────────────────────────────────────────────
    logger.info("[%s] Validating and scoring %d candidate jobs...", run_id, len(data["jobs"]))
    verified_jobs = _validate_and_score_jobs(data["jobs"], real_jobs)

    # Filter: keep ≥30% match, but always surface at least 3 results
    good = [j for j in verified_jobs if j["match_score"] >= 30]
    candidate_jobs = good if len(good) >= 3 else verified_jobs
    final_jobs = _select_diverse_jobs(candidate_jobs, limit=5, max_per_title_family=2)

    logger.info("[%s] Final result: %d verified jobs returned.", run_id, len(final_jobs))
    logger.info("[%s] Jobs: %s", run_id,
                [f"{j.get('role','?')} @ {j.get('company','?')} ({j.get('match_score',0)}%)"
                 for j in final_jobs])

    return {
        "suggested_roles": data.get("suggested_roles", roles),
        "jobs": final_jobs,
    }


# ── Supporting Crews ───────────────────────────────────────────────────────

def run_resume_crew(resume_content: str) -> dict:
    agent = create_resume_optimizer()
    task = create_resume_task(agent, resume_content)
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = getattr(result, "raw", str(result)).strip()
    return extract_json(raw) or {"improvements": []}


def run_interview_crew(resume_content: str) -> dict:
    agent = create_interview_coach()
    task = create_interview_task(agent, resume_content)
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = getattr(result, "raw", str(result)).strip()
    return extract_json(raw) or {"questions": []}


# ── Master Pipeline ────────────────────────────────────────────────────────

def analyze_resume_pipeline(resume_content: str, prefs: dict = None) -> dict:
    """
    Runs all 3 agents concurrently and combines their outputs.
    Blocking time.sleep calls have been removed — the thread pool handles concurrency.
    """
    logger.info("🚀 Starting parallel analysis pipeline...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future_jobs = executor.submit(run_with_retries, run_job_crew, resume_content, prefs)
        future_resume = executor.submit(run_with_retries, run_resume_crew, resume_content)
        future_interview = executor.submit(run_with_retries, run_interview_crew, resume_content)

        jobs_data = future_jobs.result()
        resume_data = future_resume.result()
        interview_data = future_interview.result()

    result = {
        "roles": jobs_data.get("suggested_roles", []),
        "jobs": jobs_data.get("jobs", []),
        "improvements": resume_data.get("improvements", []),
        "questions": interview_data.get("questions", []),
    }

    logger.info("✅ Pipeline complete. roles=%d, jobs=%d, improvements=%d, questions=%d",
                len(result["roles"]), len(result["jobs"]),
                len(result["improvements"]), len(result["questions"]))
    return result

# ── New Endpoints / Features ───────────────────────────────────────────────

def run_resume_analyzer(resume_content: str, target_role: str = "") -> dict:
    agent = create_resume_optimizer()
    task = create_resume_analysis_task(agent, resume_content, target_role)
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = getattr(result, "raw", str(result)).strip()
    return extract_json(raw) or {"score": 0, "issues": [], "improvements": [], "section_feedback": {}}

def run_resume_rewriter(resume_content: str) -> dict:
    agent = create_resume_rewriter()
    task = create_bullet_rewriting_task(agent, resume_content)
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = getattr(result, "raw", str(result)).strip()
    return extract_json(raw) or {"rewritten_lines": []}

def run_interview_start(
    role: str,
    difficulty: int,
    weak_areas: list = None,
    resume_context: dict | None = None,
    section_scores: dict | None = None,
    focus_mode: str = "weak_area",
    training_mode: str = "adaptive",
    interviewer_persona: dict | str | None = None,
    coach_memory: dict | None = None,
    domain_focus: str = "",
) -> dict:
    if weak_areas is None: weak_areas = []
    agent = create_interviewer()
    task = create_interview_start_task(
        agent,
        role,
        difficulty,
        weak_areas,
        resume_context=resume_context or {},
        section_scores=section_scores or {},
        focus_mode=focus_mode,
        training_mode=training_mode,
        interviewer_persona=interviewer_persona or {},
        coach_memory=coach_memory or {},
        domain_focus=domain_focus,
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = getattr(result, "raw", str(result)).strip()
    return extract_json(raw) or {
        "question": "Could you tell me about yourself and your experience?",
        "focus_area": "general introduction",
        "focus_type": "general",
        "interviewer_signal": "I will listen for specific evidence.",
        "pressure_level": "medium",
    }

def run_interview_answer(
    role: str,
    question: str,
    answer: str,
    current_diff: int,
    weak_areas: list | None = None,
    resume_context: dict | None = None,
    section_scores: dict | None = None,
    focus_mode: str = "weak_area",
    training_mode: str = "adaptive",
    interviewer_persona: dict | str | None = None,
    coach_memory: dict | None = None,
    domain_focus: str = "",
) -> dict:
    weak_areas = weak_areas or []
    resume_context = resume_context or {}
    section_scores = section_scores or {}
    coach_memory = coach_memory or {}
    # ── Multi-Agent Iterative Execution ──
    # 1. Evaluator reviews the answer -> yields score
    ag_eval = create_evaluator()
    t_eval = create_evaluator_task(ag_eval, question, answer)
    c_eval = Crew(agents=[ag_eval], tasks=[t_eval], verbose=False)
    
    raw_eval = getattr(c_eval.kickoff(), "raw", "").strip()
    eval_json = extract_json(raw_eval) or {"score": 5, "strengths": ["Clear communication"], "weaknesses": ["Needs more depth"], "improvements": "Elaborate more."}
    score = eval_json.get("score", 5)
    try:
        numeric_score = int(score)
    except (TypeError, ValueError):
        numeric_score = 5

    if numeric_score <= 4 and weak_areas:
        adaptive_focus_mode = "simplify_weak_area"
    elif numeric_score >= 8:
        adaptive_focus_mode = "increase_depth"
    else:
        adaptive_focus_mode = focus_mode
    
    # 2. Run Follow-up generator and Difficulty controller in parallel
    def _run_followup():
        ag_f = create_followup_coach()
        t_f = create_followup_task(
            ag_f,
            role,
            question,
            answer,
            current_diff,
            weak_areas=weak_areas,
            resume_context=resume_context,
            section_scores=section_scores,
            focus_mode=adaptive_focus_mode,
            training_mode=training_mode,
            interviewer_persona=interviewer_persona or {},
            coach_memory=coach_memory,
            domain_focus=domain_focus,
        )
        c_f = Crew(agents=[ag_f], tasks=[t_f], verbose=False)
        raw_f = getattr(c_f.kickoff(), "raw", "").strip()
        return extract_json(raw_f) or {
            "question": "Can you elaborate further?",
            "focus_area": weak_areas[0] if weak_areas else "general depth",
            "focus_type": "weak_area" if weak_areas else "general",
        }
        
    def _run_diff():
        ag_d = create_difficulty_controller()
        t_d = create_difficulty_task(ag_d, current_diff, score)
        c_d = Crew(agents=[ag_d], tasks=[t_d], verbose=False)
        raw_d = getattr(c_d.kickoff(), "raw", "").strip()
        return extract_json(raw_d) or {"new_difficulty": current_diff}

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        fut_f = ex.submit(run_with_retries, _run_followup)
        fut_d = ex.submit(run_with_retries, _run_diff)
        f_json = fut_f.result()
        d_json = fut_d.result()
        
    return {
        "evaluation": eval_json,
        "next_question": f_json.get("question", "Can you explain specifically how you handled that?"),
        "new_difficulty": d_json.get("new_difficulty", current_diff),
        "focus_area": f_json.get("focus_area", weak_areas[0] if weak_areas else "general"),
        "focus_type": f_json.get("focus_type", "weak_area" if "weak" in adaptive_focus_mode else "general"),
        "adaptive_mode": adaptive_focus_mode,
        "interviewer_signal": f_json.get("interviewer_signal", ""),
        "pressure_level": f_json.get("pressure_level", "medium"),
    }

def run_tailored_resume_rewriter(resume_content: str, job_description: str) -> dict:
    agent = create_resume_rewriter()
    
    # We create a custom task on the fly to tailor specifically to the JD
    from crewai import Task
    description = (
        "You are an expert ATS resume optimizer. You must rewrite the candidate's resume bullet points "
        f"to perfectly align with this specific Job Description:\n\n{job_description}\n\n"
        f"Candidate Resume:\n{resume_content}\n\n"
        "Return valid JSON containing 'rewritten_lines' array."
    )
    
    task = Task(
        description=description,
        expected_output="Valid JSON with 'rewritten_lines' containing strings of tailored bullets.",
        agent=agent
    )
    
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = getattr(result, "raw", str(result)).strip()
    return extract_json(raw) or {"rewritten_lines": []}
