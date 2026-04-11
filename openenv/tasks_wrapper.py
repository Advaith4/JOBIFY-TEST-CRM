from __future__ import annotations

import importlib
import importlib.util
import json
from dataclasses import dataclass
from typing import Any

from agents.resume_optimizer import create_resume_optimizer, create_resume_rewriter
from tasks.resume_task import create_bullet_rewriting_task, create_resume_analysis_task
from utils.resume_parser import clean_text, validate_resume_text
from utils.skill_scorer import (
    compute_match_score,
    extract_keywords,
    generate_action_plan,
    get_priority,
)


@dataclass(frozen=True)
class StandardTask:
    task_id: str
    difficulty: str
    title: str
    observation: str
    expected_output: dict[str, Any]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "difficulty": self.difficulty,
            "title": self.title,
            "observation": self.observation,
            "expected_output": self.expected_output,
            "metadata": self.metadata,
        }


def _pretty_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=True)


def _ascii_text(value: str) -> str:
    return value.encode("ascii", "ignore").decode("ascii").strip()


def _build_skill_extraction_task() -> StandardTask:
    resume_text = clean_text(
        """
        Riya Sharma
        Software Engineer

        Experience
        Built Python and FastAPI services for a campus hiring portal and improved recruiter response time by 32%.
        Developed React dashboards with SQL-backed analytics for 1200+ student applications.
        Created Docker-based deployment workflows and automated resume screening reports.

        Projects
        Machine Learning resume classifier using Python, scikit-learn, and pandas.
        Job recommendation assistant built with JavaScript, React, Node, and AWS.

        Skills
        Python, FastAPI, React, JavaScript, SQL, Docker, AWS, Machine Learning, Pandas

        Education
        B.Tech in Computer Science
        """
    )
    is_valid, validation_message = validate_resume_text(resume_text)
    extracted = extract_keywords(resume_text)
    expected_output = {
        "candidate_summary": "Software engineer profile focused on backend, frontend, and ML-enabled hiring tools.",
        "skills": sorted(extracted.keys()),
        "skill_count": len(extracted),
        "validation": {
            "is_valid_resume": is_valid,
            "message": validation_message,
        },
    }
    observation = "\n".join(
        [
            "Task: Skill Extraction",
            "Difficulty: EASY",
            "Extract the candidate's core technical skills into JSON.",
            "Return JSON with keys: candidate_summary, skills, skill_count, validation.",
            "Strict Rules:",
            "- Return raw JSON only.",
            "- Do not use markdown fences.",
            "- Use the exact keys shown above.",
            "- validation must be an object with is_valid_resume and message.",
            "- skill_count must be an integer.",
            "",
            "Resume:",
            resume_text,
        ]
    )
    return StandardTask(
        task_id="skill_extraction",
        difficulty="easy",
        title="Skill Extraction",
        observation=observation,
        expected_output=expected_output,
        metadata={
            "source_modules": ["utils.resume_parser", "utils.skill_scorer"],
            "resume_text": resume_text,
        },
    )


def _build_job_matching_task() -> StandardTask:
    resume_text = clean_text(
        """
        Aditya Rao
        Backend Developer

        Experience
        Developed Python APIs with FastAPI and PostgreSQL for hiring workflows.
        Built Docker-based deployment pipelines and integrated AWS S3 for document storage.
        Improved interview scheduling reliability by 25% using asynchronous workers.

        Projects
        Candidate matching engine using Python, SQL, Docker, AWS, and machine learning.

        Skills
        Python, FastAPI, SQL, Docker, AWS, Machine Learning, Git
        """
    )
    required_skills = ["Python", "FastAPI", "SQL", "Docker", "AWS", "REST APIs"]
    job_description = (
        "Role: Junior Backend Engineer. Requirements: Python, FastAPI, SQL, "
        "Docker, AWS, REST APIs, and strong problem solving."
    )
    match_result = compute_match_score(resume_text, required_skills)
    priority = _ascii_text(get_priority(match_result["score"]))
    action_plan = generate_action_plan(
        match_result["score"],
        match_result["missing_keywords"],
    )
    skill_matcher_module = importlib.import_module("agents.skill_matcher")
    expected_output = {
        "matched_skills": match_result["matched_keywords"],
        "missing_skills": match_result["missing_keywords"],
        "match_score": match_result["score"],
        "priority": priority,
        "recommendation": action_plan,
    }
    observation = "\n".join(
        [
            "Task: Job Matching",
            "Difficulty: MEDIUM",
            "Evaluate the resume against the job description and return JSON.",
            "Return JSON with keys: matched_skills, missing_skills, match_score, priority, recommendation.",
            "Strict Rules:",
            "- Return raw JSON only.",
            "- Do not use markdown fences.",
            "- Use the exact keys shown above.",
            "- match_score must be an integer from 0 to 100.",
            "- matched_skills and missing_skills must be arrays of strings.",
            "",
            "Resume:",
            resume_text,
            "",
            "Job Description:",
            job_description,
        ]
    )
    return StandardTask(
        task_id="job_matching",
        difficulty="medium",
        title="Job Matching",
        observation=observation,
        expected_output=expected_output,
        metadata={
            "source_modules": ["utils.skill_scorer", "agents.skill_matcher"],
            "required_skills": required_skills,
            "resume_text": resume_text,
            "job_description": job_description,
            "skill_matcher_module": skill_matcher_module.__name__,
        },
    )


def _build_resume_optimization_task() -> StandardTask:
    resume_text = clean_text(
        """
        Neha Verma
        Software Developer

        Experience
        Worked on web application features for internal hiring tools.
        Responsible for improving resume upload flow and fixing bugs.
        Helped the team launch analytics dashboards for recruiters.

        Projects
        Built a resume parser.
        Created an interview preparation app.

        Skills
        Python, React, SQL, FastAPI
        """
    )
    optimizer_role = "Resume Analyzer"
    optimizer_goal = (
        "Analyze the candidate's resume and provide precise, actionable improvements "
        "to make it stand out to ATS systems and human recruiters."
    )
    analysis_contract = (
        "Valid JSON containing resume score, issues, improvements, and section feedback."
    )
    rewrite_contract = (
        "Valid JSON containing original and improved rewritten bullet points."
    )
    analysis_prompt = None
    rewrite_prompt = None
    has_litellm = importlib.util.find_spec("litellm") is not None
    if has_litellm:
        try:
            optimizer_agent = create_resume_optimizer()
            rewriter_agent = create_resume_rewriter()
            analysis_task = create_resume_analysis_task(
                optimizer_agent,
                resume_text,
                target_role="Software Engineer",
            )
            rewrite_task = create_bullet_rewriting_task(rewriter_agent, resume_text)
            optimizer_role = optimizer_agent.role
            optimizer_goal = optimizer_agent.goal
            analysis_contract = analysis_task.expected_output
            rewrite_contract = rewrite_task.expected_output
            analysis_prompt = analysis_task.description
            rewrite_prompt = rewrite_task.description
        except Exception:
            optimizer_agent = None
            rewriter_agent = None
    else:
        optimizer_agent = None
        rewriter_agent = None
    expected_output = {
        "issues": [
            "Weak action verbs in experience bullets",
            "Missing measurable impact in core achievements",
            "Project descriptions are too vague for ATS screening",
        ],
        "improvements": [
            "Use stronger action verbs such as developed, built, improved, and optimized",
            "Add measurable impact using percentages, counts, or timelines",
            "Clarify project scope, tools used, and business outcome",
        ],
        "rewritten_bullets": [
            "Developed web application features for hiring tools that improved recruiter workflow efficiency.",
            "Improved the resume upload flow by fixing reliability issues and reducing user friction.",
            "Built recruiter analytics dashboards that surfaced hiring pipeline trends for the team.",
        ],
    }
    observation = "\n".join(
        [
            "Task: Resume Optimization",
            "Difficulty: HARD",
            "Analyze the resume and provide strong, ATS-friendly improvements in JSON.",
            "Return JSON with keys: issues, improvements, rewritten_bullets.",
            "Strict Rules:",
            "- Return raw JSON only.",
            "- Do not use markdown fences.",
            "- Use the exact keys shown above.",
            "- rewritten_bullets must be an array of improved bullet strings.",
            "- Include strong action verbs and measurable impact where appropriate.",
            "",
            f"Optimizer Role: {optimizer_role}",
            f"Optimizer Goal: {optimizer_goal}",
            f"Analysis Task Output Contract: {analysis_contract}",
            f"Rewrite Task Output Contract: {rewrite_contract}",
            "",
            "Resume:",
            resume_text,
        ]
    )
    return StandardTask(
        task_id="resume_optimization",
        difficulty="hard",
        title="Resume Optimization",
        observation=observation,
        expected_output=expected_output,
        metadata={
            "source_modules": ["agents.resume_optimizer", "tasks.resume_task"],
            "resume_text": resume_text,
            "analysis_prompt": analysis_prompt,
            "rewrite_prompt": rewrite_prompt,
        },
    )


class TaskWrapper:
    _BUILDERS = {
        "skill_extraction": _build_skill_extraction_task,
        "job_matching": _build_job_matching_task,
        "resume_optimization": _build_resume_optimization_task,
    }

    @classmethod
    def get_tasks(cls) -> list[dict[str, Any]]:
        return [builder().to_dict() for builder in cls._BUILDERS.values()]

    @classmethod
    def get_task(cls, task_id: str) -> dict[str, Any]:
        if task_id not in cls._BUILDERS:
            raise KeyError(f"Unknown task_id: {task_id}")
        return cls._BUILDERS[task_id]().to_dict()

    @classmethod
    def get_task_ids(cls) -> list[str]:
        return list(cls._BUILDERS.keys())

    @classmethod
    def expected_output_text(cls, task_id: str) -> str:
        return _pretty_json(cls.get_task(task_id)["expected_output"])
