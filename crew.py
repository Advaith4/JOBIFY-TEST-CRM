"""
Crew orchestration for Jobify.

This module keeps the existing architecture intact while improving:
- job recommendation diversity and reasoning
- resume-analysis compatibility
- interview realism and context continuity
"""

import concurrent.futures
import json
import logging
import re
import time
import uuid
from typing import Any

from crewai import Crew

from agents.interview_coach import (
    create_difficulty_controller,
    create_evaluator,
    create_followup_coach,
    create_interview_coach,
    create_interviewer,
)
from agents.job_finder import create_job_finder
from agents.resume_optimizer import create_resume_optimizer, create_resume_rewriter
from tasks.interview_task import (
    create_difficulty_task,
    create_evaluator_task,
    create_followup_task,
    create_interview_start_task,
    create_interview_task,
)
from tasks.job_task import create_job_ranking_task, create_role_inference_task
from tasks.resume_task import (
    create_bullet_rewriting_task,
    create_resume_analysis_task,
    create_resume_task,
)
from utils.job_search import fetch_jobs_for_roles
from utils.skill_scorer import generate_action_plan, get_priority

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def extract_json(raw: str, task_name: str = "LLM") -> dict | None:
    logger.debug("%s raw output length: %d", task_name, len(raw) if raw else 0)
    if not raw:
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

    logger.warning("extract_json could not parse JSON from %s output", task_name)
    return None


def _normalize_evaluation(raw_eval: Any, focus_area: str = "") -> dict:
    """Normalize evaluator output into the expected strict schema.
    This mirrors server-side normalization to keep crew-level logic consistent.
    """
    eval_obj: dict = {}
    if isinstance(raw_eval, str):
        try:
            eval_obj = json.loads(raw_eval)
        except Exception:
            m = re.search(r"\{.*\}", raw_eval or "", re.DOTALL)
            if m:
                try:
                    eval_obj = json.loads(m.group())
                except Exception:
                    eval_obj = {}
            else:
                eval_obj = {}
    elif isinstance(raw_eval, dict):
        eval_obj = dict(raw_eval)
    else:
        eval_obj = {}

    def _get_list(key, legacy_keys=()):
        for k in (key, *legacy_keys):
            v = eval_obj.get(k)
            if isinstance(v, list):
                return [str(x).strip() for x in v if x is not None and str(x).strip()]
            if isinstance(v, str) and v.strip():
                parts = [s.strip() for s in re.split(r"[\n\.]+", v) if s.strip()]
                if parts:
                    return parts
        return []

    try:
        score = int(eval_obj.get("score", eval_obj.get("overall_score", 5)))
    except Exception:
        score = 5
    score = max(0, min(10, score))

    try:
        confidence = int(eval_obj.get("confidence", round(score)))
    except Exception:
        confidence = max(0, min(10, int(score)))

    what_went_well = _get_list("what_went_well", ("strengths", "strength"))[:3]
    what_was_missing = _get_list("what_was_missing", ("weaknesses", "weakness", "missing_concepts"))[:3]
    how_to_improve = _get_list("how_to_improve", ("improvement", "improvements"))[:3]
    next_focus = str(eval_obj.get("next_focus", eval_obj.get("next_answer_focus", focus_area or "specific evidence")))
    final_verdict = eval_obj.get("final_verdict") or None
    verdict_explanation = str(eval_obj.get("verdict_explanation", ""))

    # Fill to minimum lengths with helpful, non-generic suggestions
    if len(what_went_well) < 3:
        fillers = [
            "Provided a direct attempt to answer the question",
            "Used domain-relevant terminology",
            "Outlined a concrete decision or step taken",
        ]
        for f in fillers:
            if len(what_went_well) >= 3:
                break
            if f not in what_went_well:
                what_went_well.append(f)

    if len(what_was_missing) < 3:
        fillers = [
            "Missing a concrete metric or measurable result",
            "Needed clearer tradeoffs or constraints",
            "Lacked precise ownership or role clarity",
        ]
        for f in fillers:
            if len(what_was_missing) >= 3:
                break
            if f not in what_was_missing:
                what_was_missing.append(f)

    if len(how_to_improve) < 3:
        if isinstance(eval_obj.get("how_to_improve"), str) and len(how_to_improve) < 3:
            parts = [s.strip() for s in re.split(r"[\n\.]+", eval_obj.get("how_to_improve")) if s.strip()]
            for p in parts:
                if len(how_to_improve) >= 3:
                    break
                how_to_improve.append(p)
        fillers = [
            "Use one concrete example with the decision and the result",
            "State the measurable outcome (metric or impact)",
            "Describe tradeoffs and why you chose that approach",
        ]
        for f in fillers:
            if len(how_to_improve) >= 3:
                break
            if f not in how_to_improve:
                how_to_improve.append(f)

    if final_verdict not in ("Not Ready", "Borderline", "Ready"):
        if score < 5:
            final_verdict = "Not Ready"
            verdict_explanation = verdict_explanation or "Solidify fundamentals and focus on weak-area drills before applying."
        elif score < 7.5:
            final_verdict = "Borderline"
            verdict_explanation = verdict_explanation or "Some strong answers but inconsistent; prioritize specificity and measurable outcomes."
        else:
            final_verdict = "Ready"
            verdict_explanation = verdict_explanation or "Consistent depth and clarity — you're approaching interview-ready quality."

    normalized = {
        "score": score,
        "confidence": confidence,
        "what_went_well": what_went_well,
        "what_was_missing": what_was_missing,
        "how_to_improve": how_to_improve,
        "next_focus": next_focus,
        "final_verdict": final_verdict,
        "verdict_explanation": verdict_explanation,
    }
    return normalized


def _is_valid_url(url: str) -> bool:
    return isinstance(url, str) and url.startswith("https://") and len(url) > 15


_TITLE_NOISE_WORDS = {
    "junior",
    "intern",
    "internship",
    "entry",
    "level",
    "fresher",
    "remote",
    "full",
    "time",
    "contract",
    "opening",
    "hiring",
    "urgent",
}


def _normalize_title_family(title: str) -> str:
    normalized = re.sub(r"[^a-z0-9\s/+&-]", " ", (title or "").lower())
    tokens = [token for token in normalized.split() if token and token not in _TITLE_NOISE_WORDS]
    family = " ".join(tokens[:6]).strip()
    return family or normalized.strip()


def _dedupe_roles(roles: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for role in roles:
        cleaned = " ".join(str(role or "").split())
        family = _normalize_title_family(cleaned)
        if not cleaned or family in seen:
            continue
        seen.add(family)
        output.append(cleaned)
    return output


def _dedupe_strings(items: list[str], limit: int = 6) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        cleaned = " ".join(str(item or "").split())
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        output.append(cleaned)
        if len(output) >= limit:
            break
    return output


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


def _summarize_resume_profile(resume_content: str, prefs: dict | None = None) -> dict:
    from src.resume_lab import parse_resume

    parsed = parse_resume(resume_content)
    skills = _dedupe_strings(parsed.get("skills", []), limit=12)
    experience = _dedupe_strings(parsed.get("experience", []), limit=4)
    projects = _dedupe_strings(parsed.get("projects", []), limit=4)
    summary = str(parsed.get("summary", "")).strip()

    weak_signals: list[str] = []
    if len(skills) < 6:
        weak_signals.append("Skills coverage looks thin, so ATS-heavy roles may be harder to unlock.")
    if not summary or len(summary.split()) < 18:
        weak_signals.append("Positioning is still vague because the resume summary is brief.")

    metricless_bullets = 0
    for bullet in experience + projects:
        if not re.search(r"\d|%|\busers?\b|\bclients?\b|\brequests?\b|\bhours?\b|\bdays?\b|\bmonths?\b", bullet.lower()):
            metricless_bullets += 1
    if metricless_bullets >= 2:
        weak_signals.append("Several bullets lack measurable outcomes, so stronger evidence is still needed.")

    prefs = prefs or {}
    return {
        "target_role": str(prefs.get("target_role") or "").strip(),
        "location": str(prefs.get("location") or "").strip(),
        "summary": summary[:400],
        "top_skills": skills,
        "experience_samples": experience,
        "project_samples": projects,
        "weak_signals": weak_signals[:3],
    }


def _score_live_job(job: dict, profile_context: dict) -> int:
    score = 0
    title = str(job.get("title") or "").lower()
    description = str(job.get("description") or "").lower()
    text = f"{title} {description}"

    for skill in profile_context.get("top_skills", [])[:8]:
        skill_text = str(skill).lower()
        if skill_text and skill_text in text:
            score += 3

    source_role = str(job.get("source_role") or "").lower()
    if source_role and any(token in title for token in source_role.split()[:3]):
        score += 4

    target_role = str(profile_context.get("target_role") or "").strip()
    if target_role:
        target_family = _normalize_title_family(target_role)
        if target_family and target_family in _normalize_title_family(job.get("title") or ""):
            score += 5

    return score


def _fit_bucket(score: int) -> str:
    if score >= 82:
        return "strong"
    if score >= 60:
        return "close"
    return "stretch"


def _fallback_why_match(job: dict) -> str:
    matched = _dedupe_strings(job.get("matched_skills", []), limit=3)
    role = job.get("role") or job.get("title") or "this role"
    if matched:
        return f"Strong overlap with {', '.join(matched)} makes this {role} opening a credible match."
    source_role = job.get("source_role") or "your current track"
    return f"This role stays close to {source_role} and looks reachable with your current experience."


def _fallback_gap_summary(missing_skills: list[str], profile_context: dict) -> str:
    missing = _dedupe_strings(missing_skills, limit=3)
    if missing:
        if len(missing) == 1:
            return f"You do not clearly show {missing[0]} yet."
        return f"You do not clearly show {', '.join(missing[:-1])}, and {missing[-1]} yet."
    weak_signals = profile_context.get("weak_signals", [])
    if weak_signals:
        return weak_signals[0]
    return "Your evidence is promising, but the resume still needs stronger proof of depth."


def _fallback_improvement_plan(job: dict, profile_context: dict) -> str:
    plan = generate_action_plan(job.get("match_score", 0), job.get("missing_skills", []))
    weak_signals = profile_context.get("weak_signals", [])
    if weak_signals and "Build at least 1 strong project and reapply." in plan:
        return f"{plan} Also tighten resume evidence around the weak signal you keep showing."
    return plan


def _select_balanced_final_jobs(jobs: list[dict], limit: int = 5) -> list[dict]:
    selected: list[dict] = []
    used_sources: set[str] = set()
    family_count: dict[str, int] = {}

    for pass_type in ("source", "score"):
        for job in jobs:
            if job in selected:
                continue
            family = _normalize_title_family(job.get("role") or job.get("title") or "")
            source = str(job.get("source_role") or family)
            if family_count.get(family, 0) >= 2:
                continue
            if pass_type == "source" and source in used_sources:
                continue
            selected.append(job)
            used_sources.add(source)
            family_count[family] = family_count.get(family, 0) + 1
            if len(selected) >= limit:
                return selected
    return selected


def _build_job_feed_summary(final_jobs: list[dict], suggested_roles: list[str], profile_context: dict) -> dict:
    role_mix = _dedupe_roles(
        [job.get("source_role") or job.get("role") or "" for job in final_jobs] + list(suggested_roles)
    )[:4]
    gap_skills = _dedupe_strings(
        [skill for job in final_jobs for skill in (job.get("missing_skills") or [])],
        limit=4,
    )
    best_job = final_jobs[0] if final_jobs else None

    return {
        "headline": (
            f"Best opening today: {best_job.get('role')} at {best_job.get('company')}."
            if best_job
            else "No strong live matches right now."
        ),
        "note": (
            best_job.get("why_match")
            if best_job
            else "Refresh after updating your resume or adjusting your target role."
        ),
        "role_mix": role_mix,
        "top_gap": gap_skills[0] if gap_skills else (profile_context.get("weak_signals") or ["Stronger quantified impact"])[0],
        "top_gap_note": (
            best_job.get("gap_summary")
            if best_job
            else "Your next leverage point will appear here once live jobs are found."
        ),
        "best_match": f"{best_job.get('match_score', 0)}%" if best_job else "--",
        "best_match_note": (
            best_job.get("improvement_plan")
            if best_job
            else "We need at least one verified job to calculate a strongest match."
        ),
    }


def _validate_and_score_jobs(jobs: list[dict], all_real_jobs: list[dict], profile_context: dict | None = None) -> list[dict]:
    profile_context = profile_context or {}
    real_urls: set[str] = {j["url"].lower() for j in all_real_jobs if j.get("url")}
    real_lookup = {j["url"].lower(): j for j in all_real_jobs if j.get("url")}

    verified: list[dict] = []
    for job in jobs:
        link = job.get("link") or job.get("url") or ""

        if not _is_valid_url(link):
            logger.warning("Dropping job '%s' because link is invalid: %s", job.get("role", "?"), link)
            continue
        if link.lower() not in real_urls:
            logger.warning("Dropping job '%s' because link was not fetched from the API: %s", job.get("role", "?"), link)
            continue

        try:
            score = int(job.get("match_score", 0))
        except (TypeError, ValueError):
            score = 0
        score = max(0, min(100, score))
        source = real_lookup.get(link.lower(), {})

        job["match_score"] = score
        job["source_role"] = source.get("source_role", job.get("source_role", ""))
        job["matched_skills"] = _dedupe_strings(job.get("matched_skills", []), limit=6)
        job["missing_skills"] = _dedupe_strings(job.get("missing_skills", []), limit=6)
        job["why_match"] = str(job.get("why_match") or job.get("reason") or _fallback_why_match(job)).strip()
        job["reason"] = job["why_match"]
        job["gap_summary"] = str(job.get("gap_summary") or _fallback_gap_summary(job["missing_skills"], profile_context)).strip()
        job["improvement_plan"] = str(job.get("improvement_plan") or _fallback_improvement_plan(job, profile_context)).strip()
        job["fit_bucket"] = str(job.get("fit_bucket") or _fit_bucket(score)).strip().lower()
        job["priority"] = get_priority(score)
        job["action_plan"] = job["improvement_plan"]
        job["link"] = link
        verified.append(job)

    verified.sort(key=lambda j: (j["match_score"], len(j.get("matched_skills", []))), reverse=True)
    return _select_diverse_jobs(verified, limit=len(verified), max_per_title_family=2)


def run_with_retries(func, *args):
    """Exponential backoff for rate-limited LLM APIs."""
    for attempt in range(4):
        try:
            return func(*args)
        except Exception as exc:
            err = str(exc).lower()
            if "rate limit" in err or "429" in err or "decommission" in err:
                match = re.search(r"try again in ([0-9.]+)s", err)
                delay = float(match.group(1)) + 2.0 if match else 20 * (attempt + 1)
                logger.warning(
                    "Rate limit hit in %s. Retrying in %.1fs... (attempt %d/4)",
                    func.__name__,
                    delay,
                    attempt + 1,
                )
                time.sleep(delay)
            else:
                raise
    return func(*args)


def run_job_crew(resume_content: str, prefs: dict = None) -> dict:
    """Run the job recommendation pipeline using live jobs only."""
    prefs = prefs or {}
    agent = create_job_finder()
    run_id = uuid.uuid4().hex[:8]
    profile_context = _summarize_resume_profile(resume_content, prefs)

    logger.info("[%s] Phase 1: inferring best-fit roles from resume...", run_id)
    infer_task = create_role_inference_task(agent, resume_content, profile_context)
    infer_crew = Crew(agents=[agent], tasks=[infer_task], verbose=False)
    infer_result = infer_crew.kickoff()
    infer_data = extract_json(getattr(infer_result, "raw", str(infer_result)).strip(), "role_inference")

    if infer_data and isinstance(infer_data.get("roles"), list) and infer_data["roles"]:
        roles = _dedupe_roles([str(role) for role in infer_data["roles"] if role])[:5]
    else:
        roles = _dedupe_roles(
            [
                profile_context.get("target_role", ""),
                "Backend Developer Intern",
                "Frontend Developer Intern",
                "Data Analyst Intern",
                "Machine Learning Intern",
                "Software Engineer Intern",
            ]
        )[:5]
        logger.warning("[%s] Role inference failed; using fallback roles.", run_id)

    logger.info("[%s] Inferred roles: %s", run_id, roles)

    logger.info("[%s] Phase 2: fetching live jobs...", run_id)
    real_jobs = fetch_jobs_for_roles(roles, prefs=prefs, jobs_per_role=5)
    logger.info("[%s] Fetched %d unique live jobs.", run_id, len(real_jobs))

    if not real_jobs:
        return {
            "suggested_roles": roles,
            "jobs": [],
            "summary": _build_job_feed_summary([], roles, profile_context),
            "message": "No relevant jobs found",
            "_warning": "Could not fetch live job data. Check provider keys and connectivity.",
        }

    real_jobs = sorted(real_jobs, key=lambda job: _score_live_job(job, profile_context), reverse=True)
    real_jobs = _select_diverse_jobs(real_jobs, limit=10, max_per_title_family=2)
    logger.info("[%s] Selected %d pre-scored live jobs for ranking.", run_id, len(real_jobs))

    logger.info("[%s] Phase 3: ranking verified live jobs...", run_id)
    rank_task = create_job_ranking_task(agent, resume_content, real_jobs, profile_context)
    rank_crew = Crew(agents=[agent], tasks=[rank_task], verbose=False)
    rank_result = rank_crew.kickoff()
    data = extract_json(getattr(rank_result, "raw", str(rank_result)).strip(), "job_ranking")

    if not data or not isinstance(data.get("jobs"), list):
        logger.warning("[%s] Ranking parse failed; falling back to empty ranked jobs.", run_id)
        data = {"suggested_roles": roles, "jobs": []}

    verified_jobs = _validate_and_score_jobs(data["jobs"], real_jobs, profile_context)
    good = [job for job in verified_jobs if job["match_score"] >= 35]
    candidate_jobs = good if len(good) >= 3 else verified_jobs
    final_jobs = _select_balanced_final_jobs(candidate_jobs, limit=5)

    logger.info(
        "[%s] Final jobs: %s",
        run_id,
        [f"{job.get('role', '?')} @ {job.get('company', '?')} ({job.get('match_score', 0)}%)" for job in final_jobs],
    )

    suggested_roles = _dedupe_roles(data.get("suggested_roles", roles) or roles)
    return {
        "suggested_roles": suggested_roles,
        "jobs": final_jobs,
        "summary": _build_job_feed_summary(final_jobs, suggested_roles, profile_context),
    }


def run_resume_crew(resume_content: str) -> dict:
    agent = create_resume_optimizer()
    task = create_resume_task(agent, resume_content)
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = getattr(result, "raw", str(result)).strip()
    return extract_json(raw, "resume_crew") or {"improvements": []}


def run_interview_crew(resume_content: str) -> dict:
    agent = create_interview_coach()
    task = create_interview_task(agent, resume_content)
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = getattr(result, "raw", str(result)).strip()
    return extract_json(raw, "interview_crew") or {"questions": []}


def analyze_resume_pipeline(resume_content: str, prefs: dict = None) -> dict:
    """Run jobs, resume analysis, and interview suggestions in parallel."""
    logger.info("Starting parallel analysis pipeline...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
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

    logger.info(
        "Pipeline complete. roles=%d jobs=%d improvements=%d questions=%d",
        len(result["roles"]),
        len(result["jobs"]),
        len(result["improvements"]),
        len(result["questions"]),
    )
    return result


def run_resume_analyzer(resume_content: str, target_role: str = "") -> dict:
    agent = create_resume_optimizer()
    task = create_resume_analysis_task(agent, resume_content, target_role)
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = getattr(result, "raw", str(result)).strip()
    return extract_json(raw, "resume_analyzer") or {
        "score": 0,
        "issues": [],
        "improvements": [],
        "section_feedback": {},
        "summary_feedback": {},
    }


def run_resume_rewriter(resume_content: str) -> dict:
    agent = create_resume_rewriter()
    task = create_bullet_rewriting_task(agent, resume_content)
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = getattr(result, "raw", str(result)).strip()
    return extract_json(raw, "resume_rewriter") or {"rewritten_lines": []}


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
    weak_areas = weak_areas or []
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
    return extract_json(raw, "interview_start") or {
        "question": "Walk me through the part of your experience that best proves you can do this role. Be concrete.",
        "focus_area": "general introduction",
        "focus_type": "general",
        "interviewer_signal": "I will listen for specific evidence.",
        "pressure_level": "medium",
        "answer_expectation": "Answer in 5-10 lines with context, actions, and outcome.",
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
    conversation_history: list[dict] | None = None,
    current_focus_area: str = "",
) -> dict:
    weak_areas = weak_areas or []
    resume_context = resume_context or {}
    section_scores = section_scores or {}
    coach_memory = coach_memory or {}
    conversation_history = conversation_history or []
    interviewer_persona = interviewer_persona or {}

    ag_eval = create_evaluator()
    t_eval = create_evaluator_task(
        ag_eval,
        question,
        answer,
        conversation_history=conversation_history,
        focus_area=current_focus_area or focus_mode,
        interviewer_persona=interviewer_persona,
    )
    c_eval = Crew(agents=[ag_eval], tasks=[t_eval], verbose=False)
    raw_eval = getattr(c_eval.kickoff(), "raw", "").strip()
    eval_json = extract_json(raw_eval, "interview_eval") or {
        "score": 5,
        "technical_depth": 5,
        "communication": 5,
        "specificity": 4,
        "structure": 5,
        "strengths": ["You stayed on topic."],
        "weaknesses": ["The answer needs more specifics."],
        "missing_concepts": ["Concrete example", "Tradeoff"],
        "improvement": "Answer again with one specific example, the decision you made, and the result you achieved.",
        "next_answer_focus": current_focus_area or (weak_areas[0] if weak_areas else "general depth"),
    }

    # Normalize evaluator output for consistent downstream logic
    normalized_eval = _normalize_evaluation(eval_json, current_focus_area)
    try:
        numeric_score = int(normalized_eval.get("score", 5))
    except (TypeError, ValueError):
        numeric_score = 5

    if numeric_score <= 4 and weak_areas:
        adaptive_focus_mode = "simplify_weak_area"
    elif numeric_score >= 8:
        adaptive_focus_mode = "increase_depth"
    else:
        adaptive_focus_mode = focus_mode

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
            interviewer_persona=interviewer_persona,
            coach_memory=coach_memory,
            domain_focus=domain_focus,
            conversation_history=conversation_history,
            last_score=numeric_score,
            current_focus_area=current_focus_area or normalized_eval.get("next_focus", ""),
        )
        c_f = Crew(agents=[ag_f], tasks=[t_f], verbose=False)
        raw_f = getattr(c_f.kickoff(), "raw", "").strip()
        return extract_json(raw_f, "interview_followup") or {
            "question": "Let me stop you there. Give me one concrete example, the decision you made, and the result.",
            "focus_area": current_focus_area or (weak_areas[0] if weak_areas else "general depth"),
            "focus_type": "weak_area" if weak_areas else "general",
            "interviewer_signal": "I need a more specific answer now.",
            "pressure_level": "medium",
            "answer_expectation": "Answer in 5-10 lines with a real example, tradeoff, and outcome.",
        }

    def _run_diff():
        ag_d = create_difficulty_controller()
        t_d = create_difficulty_task(ag_d, current_diff, numeric_score)
        c_d = Crew(agents=[ag_d], tasks=[t_d], verbose=False)
        raw_d = getattr(c_d.kickoff(), "raw", "").strip()
        return extract_json(raw_d, "difficulty") or {"new_difficulty": current_diff}

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_followup = executor.submit(run_with_retries, _run_followup)
        future_diff = executor.submit(run_with_retries, _run_diff)
        followup_json = future_followup.result()
        diff_json = future_diff.result()

    return {
        "evaluation": normalized_eval,
        "next_question": followup_json.get("question", "Can you explain that with a more specific example?"),
        "new_difficulty": diff_json.get("new_difficulty", current_diff),
        "focus_area": followup_json.get("focus_area", current_focus_area or (weak_areas[0] if weak_areas else "general")),
        "focus_type": followup_json.get("focus_type", "weak_area" if "weak" in adaptive_focus_mode else "general"),
        "adaptive_mode": adaptive_focus_mode,
        "interviewer_signal": followup_json.get("interviewer_signal", ""),
        "pressure_level": followup_json.get("pressure_level", "medium"),
        "answer_expectation": followup_json.get(
            "answer_expectation",
            "Answer in 5-10 lines with context, tradeoffs, and measurable outcome.",
        ),
    }


def run_tailored_resume_rewriter(resume_content: str, job_description: str) -> dict:
    agent = create_resume_rewriter()
    from crewai import Task

    description = (
        "You are an expert ATS resume optimizer. You must rewrite the candidate's resume bullet points "
        f"to align with this job description:\n\n{job_description}\n\n"
        f"Candidate Resume:\n{resume_content}\n\n"
        "Return valid JSON containing 'rewritten_lines' array."
    )

    task = Task(
        description=description,
        expected_output="Valid JSON with 'rewritten_lines' containing strings of tailored bullets.",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = getattr(result, "raw", str(result)).strip()
    return extract_json(raw, "tailored_resume_rewriter") or {"rewritten_lines": []}
