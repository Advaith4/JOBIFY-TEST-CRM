import hashlib
import json
import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError


SECTION_ALIASES = {
    "summary": {"summary", "profile", "objective", "professional summary", "career objective", "about"},
    "experience": {"experience", "work experience", "professional experience", "employment", "internship", "internships"},
    "projects": {"projects", "project experience", "academic projects", "personal projects"},
    "skills": {"skills", "technical skills", "core skills", "technologies", "tools", "tech stack"},
    "education": {"education", "academics", "academic background"},
    "certifications": {"certifications", "certificates", "achievements", "awards"},
}

ACTION_VERBS = {
    "built", "developed", "designed", "implemented", "created", "led", "owned", "optimized",
    "automated", "deployed", "improved", "integrated", "analyzed", "delivered", "launched",
    "managed", "reduced", "increased", "trained", "tested", "maintained", "configured",
}

WEAK_STARTS = (
    "worked on", "responsible for", "helped with", "helped", "did", "made", "handled",
    "involved in", "participated in", "was part of", "used",
)

COMMON_SKILLS = {
    "python", "java", "javascript", "typescript", "react", "node", "fastapi", "flask",
    "django", "sql", "mysql", "postgresql", "mongodb", "firebase", "flutter", "dart",
    "android", "ios", "aws", "docker", "kubernetes", "git", "linux", "machine learning",
    "deep learning", "nlp", "llm", "rag", "tensorflow", "pytorch", "html", "css",
    "tailwind", "bootstrap", "rest api", "graphql", "supabase", "figma",
}


class ResumeBreakdown(BaseModel):
    impact: int = Field(ge=0, le=100)
    clarity: int = Field(ge=0, le=100)
    structure: int = Field(ge=0, le=100)
    ats: int = Field(ge=0, le=100)


class ResumeIssue(BaseModel):
    id: str = ""
    original: str
    problem: str
    improved: str
    action_type: Literal["replace"] = "replace"
    severity: Literal["high", "medium", "low"] = "medium"
    category: str = "clarity"
    status: Literal["open", "applied", "missing"] = "open"


class ResumeSectionAnalysis(BaseModel):
    section: str
    issues: list[ResumeIssue] = Field(default_factory=list)


class SummaryFeedback(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    priority_fixes: list[str] = Field(default_factory=list)


class ResumeAnalysisResult(BaseModel):
    score: int = Field(ge=0, le=100)
    breakdown: ResumeBreakdown
    sections: list[ResumeSectionAnalysis] = Field(default_factory=list)
    summary_feedback: SummaryFeedback


RESUME_ANALYSIS_JSON_SCHEMA = ResumeAnalysisResult.model_json_schema()


def clean_resume_text(text: str) -> str:
    """Normalize PDF text while preserving line breaks for section parsing."""
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)

    lines = []
    previous_blank = False
    for line in text.split("\n"):
        cleaned = line.strip()
        if not cleaned:
            if not previous_blank:
                lines.append("")
            previous_blank = True
            continue
        lines.append(cleaned)
        previous_blank = False

    return "\n".join(lines).strip()


def parse_resume(resume_text: str) -> dict[str, Any]:
    """
    Extract structured resume sections from raw text.

    Returns:
        {
            "summary": "...",
            "experience": ["bullet", ...],
            "projects": ["bullet", ...],
            "skills": ["Python", ...],
            "education": [...],
            "certifications": [...],
            "other": [...]
        }
    """
    cleaned = clean_resume_text(resume_text)
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    sections: dict[str, Any] = {
        "summary": "",
        "experience": [],
        "projects": [],
        "skills": [],
        "education": [],
        "certifications": [],
        "other": [],
    }

    current = "summary"
    summary_lines: list[str] = []

    for line in lines:
        section = _detect_section_heading(line)
        if section:
            current = section
            continue

        if _looks_like_contact_line(line):
            continue

        if current == "skills":
            sections["skills"].extend(_split_skills(line))
            continue

        if current == "summary":
            if len(summary_lines) < 4 and len(line) > 12:
                summary_lines.append(_strip_bullet(line))
            else:
                sections["other"].append(_strip_bullet(line))
            continue

        if current in {"experience", "projects"}:
            bullet = _strip_bullet(line)
            if _is_resume_bullet(line, current):
                sections[current].append(bullet)
            elif len(bullet) > 18:
                sections[current].append(bullet)
            continue

        if current in {"education", "certifications"}:
            sections[current].append(_strip_bullet(line))
        else:
            sections["other"].append(_strip_bullet(line))

    sections["summary"] = " ".join(summary_lines).strip()

    if not sections["summary"]:
        sections["summary"] = _fallback_summary(lines)

    if not sections["skills"]:
        sections["skills"] = _extract_skills_from_text(cleaned)

    sections["skills"] = _dedupe([s for s in sections["skills"] if len(s) > 1])
    for key in ("experience", "projects", "education", "certifications", "other"):
        sections[key] = _dedupe([item for item in sections[key] if len(item) > 3])

    return sections


def analyze_resume(resume_text: str, target_role: str = "") -> dict[str, Any]:
    """
    Run the LLM analysis and validate/repair the result.
    Falls back to deterministic analysis if the model returns invalid JSON.
    """
    parsed = parse_resume(resume_text)
    llm_payload: dict[str, Any] | None = None

    try:
        from crew import run_resume_analyzer

        llm_payload = run_resume_analyzer(resume_text, target_role)
    except Exception:
        llm_payload = None

    analysis = validate_resume_analysis(llm_payload, resume_text, parsed)
    return {
        "score": analysis["score"],
        "breakdown": analysis["breakdown"],
        "sections": analysis["sections"],
    }


def rescore_resume(resume_text: str, target_role: str = "") -> dict[str, Any]:
    return analyze_resume(resume_text, target_role)


def validate_resume_analysis(
    payload: Any,
    resume_text: str,
    parsed_resume: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate LLM output, repair shape where possible, and drop non-grounded issues."""
    parsed_resume = parsed_resume or parse_resume(resume_text)
    data = _coerce_payload_to_dict(payload)
    if not data:
        return _fallback_analysis(resume_text, parsed_resume, source="fallback")

    normalized = _normalize_analysis_shape(data, resume_text, parsed_resume)

    try:
        validated = ResumeAnalysisResult.model_validate(normalized).model_dump()
    except ValidationError:
        return _fallback_analysis(resume_text, parsed_resume, source="fallback")

    has_issues = any(section["issues"] for section in validated["sections"])
    if not has_issues:
        fallback = _fallback_analysis(resume_text, parsed_resume, source="fallback")
        if validated["score"] > 0:
            fallback["score"] = validated["score"]
            fallback["breakdown"] = validated["breakdown"]
        return fallback

    validated["_source"] = "llm"
    return validated


def apply_fix(
    current_resume: str,
    issue: dict[str, Any],
    applied_fixes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Replace the issue's exact original text with the improved version."""
    applied_fixes = list(applied_fixes or [])
    issue_id = issue.get("id") or _issue_id(issue.get("section", "resume"), issue.get("original", ""), issue.get("improved", ""))

    if any(item.get("issue_id") == issue_id for item in applied_fixes):
        return {
            "applied": False,
            "status": "applied",
            "current_resume": current_resume,
            "applied_fixes": applied_fixes,
            "message": "This fix was already applied.",
        }

    original = str(issue.get("original", "")).strip()
    improved = str(issue.get("improved", "")).strip()
    if not original or not improved:
        return {
            "applied": False,
            "status": "missing",
            "current_resume": current_resume,
            "applied_fixes": applied_fixes,
            "message": "Fix is missing original or improved text.",
        }

    if original not in current_resume:
        return {
            "applied": False,
            "status": "missing",
            "current_resume": current_resume,
            "applied_fixes": applied_fixes,
            "message": "Original text was not found. It may already have been edited.",
        }

    updated_resume = current_resume.replace(original, improved, 1)
    applied_fixes.append(
        {
            "issue_id": issue_id,
            "section": issue.get("section", "resume"),
            "original": original,
            "improved": improved,
            "applied_at": datetime.utcnow().isoformat(),
        }
    )

    return {
        "applied": True,
        "status": "applied",
        "current_resume": updated_resume,
        "applied_fixes": applied_fixes,
        "message": "Fix applied.",
    }


def apply_top_fixes(
    current_resume: str,
    analysis: dict[str, Any],
    applied_fixes: list[dict[str, Any]] | None = None,
    limit: int = 3,
) -> dict[str, Any]:
    applied_fixes = list(applied_fixes or [])
    applied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    issues = flatten_issues(analysis)
    issues.sort(key=lambda issue: {"high": 0, "medium": 1, "low": 2}.get(issue.get("severity", "medium"), 1))

    updated_resume = current_resume
    for issue in issues[: max(1, min(limit, 10))]:
        result = apply_fix(updated_resume, issue, applied_fixes)
        updated_resume = result["current_resume"]
        applied_fixes = result["applied_fixes"]
        if result["applied"]:
            applied.append(issue)
        else:
            skipped.append({**issue, "message": result["message"]})

    return {
        "current_resume": updated_resume,
        "applied_fixes": applied_fixes,
        "applied": applied,
        "skipped": skipped,
    }


def flatten_issues(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for section in analysis.get("sections", []) or []:
        section_name = section.get("section", "resume")
        for issue in section.get("issues", []) or []:
            issues.append({**issue, "section": section_name})
    return issues


def mark_issue_status(analysis: dict[str, Any], issue_id: str, status: str) -> dict[str, Any]:
    copied = json.loads(json.dumps(analysis or {}))
    for section in copied.get("sections", []) or []:
        for issue in section.get("issues", []) or []:
            if issue.get("id") == issue_id:
                issue["status"] = status
    return copied


def find_issue(analysis: dict[str, Any], issue_id: str) -> dict[str, Any] | None:
    for issue in flatten_issues(analysis):
        if issue.get("id") == issue_id:
            return issue
    return None


def load_json_field(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def dumps_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True)


def _coerce_payload_to_dict(payload: Any) -> dict[str, Any] | None:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        return extract_json_object(payload)
    return None


def extract_json_object(raw: str) -> dict[str, Any] | None:
    if not raw:
        return None

    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    for candidate in (cleaned, _extract_braced_block(cleaned)):
        if not candidate:
            continue
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            repaired = _repair_json(candidate)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                continue

    return None


def _extract_braced_block(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def _repair_json(text: str) -> str:
    repaired = text.strip()
    repaired = repaired.replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'")
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    open_braces = repaired.count("{") - repaired.count("}")
    open_brackets = repaired.count("[") - repaired.count("]")
    if open_brackets > 0:
        repaired += "]" * open_brackets
    if open_braces > 0:
        repaired += "}" * open_braces
    return repaired


def _normalize_analysis_shape(
    data: dict[str, Any],
    resume_text: str,
    parsed_resume: dict[str, Any],
) -> dict[str, Any]:
    score = _clamp_int(data.get("score"), default=_fallback_score(parsed_resume))
    breakdown_data = data.get("breakdown") if isinstance(data.get("breakdown"), dict) else {}
    breakdown = {
        "impact": _clamp_int(breakdown_data.get("impact"), default=max(0, score - 10)),
        "clarity": _clamp_int(breakdown_data.get("clarity"), default=score),
        "structure": _clamp_int(breakdown_data.get("structure"), default=min(100, score + 5)),
        "ats": _clamp_int(breakdown_data.get("ats"), default=score),
    }

    normalized_sections = _normalize_sections(data, resume_text, parsed_resume)
    summary_feedback = _normalize_summary_feedback(data.get("summary_feedback"), normalized_sections, score)

    return {
        "score": score,
        "breakdown": breakdown,
        "sections": normalized_sections,
        "summary_feedback": summary_feedback,
    }


def _normalize_sections(
    data: dict[str, Any],
    resume_text: str,
    parsed_resume: dict[str, Any],
) -> list[dict[str, Any]]:
    raw_sections = data.get("sections")
    if not isinstance(raw_sections, list):
        raw_issues = data.get("issues", [])
        raw_sections = [{"section": "resume", "issues": raw_issues if isinstance(raw_issues, list) else []}]

    sections: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw_section in raw_sections:
        if not isinstance(raw_section, dict):
            continue
        section_name = _normalize_section_name(raw_section.get("section", "resume"))
        raw_issues = raw_section.get("issues", [])
        if not isinstance(raw_issues, list):
            raw_issues = []

        issues: list[dict[str, Any]] = []
        for item in raw_issues:
            issue = _normalize_issue(item, section_name, resume_text, parsed_resume)
            if not issue:
                continue
            dedupe_key = issue["original"].lower()
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            issues.append(issue)

        sections.append({"section": section_name, "issues": issues})

    for key in ("summary", "experience", "projects", "skills"):
        if not any(section["section"] == key for section in sections):
            sections.append({"section": key, "issues": []})

    return sections


def _normalize_issue(
    item: Any,
    section_name: str,
    resume_text: str,
    parsed_resume: dict[str, Any],
) -> dict[str, Any] | None:
    if isinstance(item, str):
        original = _find_best_original(item, parsed_resume)
        if not original:
            return None
        problem = item
        improved = _rewrite_bullet(original)
    elif isinstance(item, dict):
        original = str(item.get("original", "")).strip()
        problem = str(item.get("problem", "")).strip()
        improved = str(item.get("improved", "")).strip()
        if original not in resume_text:
            original = _find_best_original(original or problem, parsed_resume) or ""
    else:
        return None

    if not original or original not in resume_text:
        return None

    improved = improved or _rewrite_bullet(original)
    if not improved or improved.strip().lower() == original.strip().lower():
        improved = _rewrite_bullet(original)

    severity = str(item.get("severity", "medium")).lower() if isinstance(item, dict) else "medium"
    if severity not in {"high", "medium", "low"}:
        severity = "medium"

    category = str(item.get("category", "clarity")).strip().lower() if isinstance(item, dict) else "clarity"
    issue = {
        "id": str(item.get("id") or _issue_id(section_name, original, improved)) if isinstance(item, dict) else _issue_id(section_name, original, improved),
        "original": original,
        "problem": problem or _problem_for_bullet(original),
        "improved": improved,
        "action_type": "replace",
        "severity": severity,
        "category": category or "clarity",
        "status": "open",
    }
    return issue


def _normalize_summary_feedback(value: Any, sections: list[dict[str, Any]], score: int) -> dict[str, list[str]]:
    if isinstance(value, dict):
        return {
            "strengths": _string_list(value.get("strengths")) or _default_strengths(score),
            "weaknesses": _string_list(value.get("weaknesses")) or _weaknesses_from_sections(sections),
            "priority_fixes": _string_list(value.get("priority_fixes")) or _priority_from_sections(sections),
        }

    return {
        "strengths": _default_strengths(score),
        "weaknesses": _weaknesses_from_sections(sections),
        "priority_fixes": _priority_from_sections(sections),
    }


def _fallback_analysis(resume_text: str, parsed_resume: dict[str, Any], source: str) -> dict[str, Any]:
    issues_by_section: dict[str, list[dict[str, Any]]] = {
        "summary": [],
        "experience": [],
        "projects": [],
        "skills": [],
    }

    for section_name in ("experience", "projects"):
        for bullet in parsed_resume.get(section_name, [])[:8]:
            problems = _detect_bullet_problems(bullet)
            if not problems:
                continue
            improved = _rewrite_bullet(bullet)
            if improved == bullet:
                continue
            severity = "high" if "measurable" in " ".join(problems).lower() else "medium"
            issues_by_section[section_name].append(
                {
                    "id": _issue_id(section_name, bullet, improved),
                    "original": bullet,
                    "problem": "; ".join(problems),
                    "improved": improved,
                    "action_type": "replace",
                    "severity": severity,
                    "category": "impact",
                    "status": "open",
                }
            )

    summary = parsed_resume.get("summary", "")
    if summary and len(summary.split()) < 18:
        improved = _rewrite_summary(summary)
        issues_by_section["summary"].append(
            {
                "id": _issue_id("summary", summary, improved),
                "original": summary,
                "problem": "Summary is too short to communicate role, strengths, and career direction.",
                "improved": improved,
                "action_type": "replace",
                "severity": "medium",
                "category": "clarity",
                "status": "open",
            }
        )

    if not parsed_resume.get("skills"):
        first_line = _fallback_summary(clean_resume_text(resume_text).splitlines())
        if first_line:
            improved = first_line + "\n\nSkills: Add your strongest tools, languages, frameworks, and platforms as comma-separated keywords."
            issues_by_section["skills"].append(
                {
                    "id": _issue_id("skills", first_line, improved),
                    "original": first_line,
                    "problem": "No clear skills section was detected, which can reduce ATS keyword matching.",
                    "improved": improved,
                    "action_type": "replace",
                    "severity": "high",
                    "category": "ats",
                    "status": "open",
                }
            )

    score = _fallback_score(parsed_resume)
    breakdown = _fallback_breakdown(parsed_resume, issues_by_section)
    sections = [{"section": key, "issues": value} for key, value in issues_by_section.items()]

    return {
        "score": score,
        "breakdown": breakdown,
        "sections": sections,
        "summary_feedback": {
            "strengths": _default_strengths(score),
            "weaknesses": _weaknesses_from_sections(sections),
            "priority_fixes": _priority_from_sections(sections),
        },
        "_source": source,
    }


def _detect_section_heading(line: str) -> str | None:
    normalized = _normalize_heading(line)
    if not normalized or len(normalized) > 45:
        return None
    for section, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section
    return None


def _normalize_heading(line: str) -> str:
    normalized = re.sub(r"[^a-zA-Z /&+-]", "", line).strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _strip_bullet(line: str) -> str:
    return re.sub(r"^\s*[-*•\u2022\u25E6\u25AA\u2013\u2014]+\s*", "", line).strip()


def _is_resume_bullet(line: str, section: str) -> bool:
    stripped = _strip_bullet(line)
    first_word = stripped.split(" ", 1)[0].lower() if stripped else ""
    return (
        bool(re.match(r"^\s*[-*•\u2022\u25E6\u25AA\u2013\u2014]", line))
        or first_word in ACTION_VERBS
        or section in {"experience", "projects"} and len(stripped) > 28
    )


def _looks_like_contact_line(line: str) -> bool:
    lowered = line.lower()
    return bool(re.search(r"\b[\w.-]+@[\w.-]+\.\w+\b", lowered)) or "linkedin.com" in lowered or "github.com" in lowered


def _split_skills(line: str) -> list[str]:
    line = _strip_bullet(line)
    if ":" in line and len(line.split(":", 1)[0]) < 28:
        line = line.split(":", 1)[1]
    return [part.strip(" .;|") for part in re.split(r"[,|;/]", line) if part.strip(" .;|")]


def _extract_skills_from_text(text: str) -> list[str]:
    lowered = text.lower()
    found = [skill for skill in sorted(COMMON_SKILLS) if re.search(rf"\b{re.escape(skill)}\b", lowered)]
    return [skill.upper() if skill in {"sql", "aws", "llm", "rag"} else skill.title() for skill in found]


def _fallback_summary(lines: list[str]) -> str:
    for line in lines:
        stripped = _strip_bullet(line)
        if len(stripped) > 25 and not _detect_section_heading(stripped) and not _looks_like_contact_line(stripped):
            return stripped
    return ""


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = re.sub(r"\s+", " ", item).strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(item.strip())
    return result


def _detect_bullet_problems(bullet: str) -> list[str]:
    problems: list[str] = []
    lowered = bullet.lower().strip()
    if lowered.startswith(WEAK_STARTS):
        problems.append("Weak opening verb")
    if not re.search(r"\d|%|\busers?\b|\bclients?\b|\brequests?\b|\bseconds?\b|\bhours?\b|\bteam\b", lowered):
        problems.append("No measurable scope or impact")
    if len(bullet.split()) < 8:
        problems.append("Too short to show context and outcome")
    if len(bullet.split()) > 32:
        problems.append("Too long; split or tighten for readability")
    return problems


def _problem_for_bullet(bullet: str) -> str:
    problems = _detect_bullet_problems(bullet)
    return "; ".join(problems) if problems else "Can be made more specific and outcome-oriented"


def _rewrite_bullet(bullet: str) -> str:
    stripped = _strip_bullet(bullet).rstrip(".")
    lowered = stripped.lower()

    replacements = {
        "worked on": "Developed",
        "responsible for": "Owned",
        "helped with": "Supported",
        "helped": "Supported",
        "did": "Completed",
        "made": "Built",
        "handled": "Managed",
        "involved in": "Contributed to",
        "participated in": "Contributed to",
        "was part of": "Contributed to",
        "used": "Applied",
    }

    rewritten = stripped
    for weak, strong in replacements.items():
        if lowered.startswith(weak):
            rewritten = strong + stripped[len(weak):]
            break

    first_word = rewritten.split(" ", 1)[0].lower() if rewritten else ""
    if first_word not in ACTION_VERBS and first_word not in {"supported", "owned", "completed", "contributed", "applied"}:
        rewritten = "Delivered " + rewritten[:1].lower() + rewritten[1:]

    if not re.search(r"\d|%|\busers?\b|\bclients?\b|\brequests?\b|\bseconds?\b|\bhours?\b|\bteam\b", rewritten.lower()):
        rewritten += ", clarifying the tools used, scope, and outcome"

    return rewritten.rstrip(".") + "."


def _rewrite_summary(summary: str) -> str:
    stripped = summary.rstrip(".")
    if len(stripped.split()) >= 18:
        return stripped + "."
    return (
        f"{stripped}. Software candidate with hands-on project experience, clear technical strengths, "
        "and a focus on building reliable, user-centered solutions."
    )


def _find_best_original(hint: str, parsed_resume: dict[str, Any]) -> str | None:
    candidates: list[str] = []
    if parsed_resume.get("summary"):
        candidates.append(parsed_resume["summary"])
    for key in ("experience", "projects", "skills", "education", "other"):
        values = parsed_resume.get(key, [])
        if isinstance(values, list):
            candidates.extend(str(v) for v in values)

    if not candidates:
        return None

    hint_words = set(re.findall(r"[a-zA-Z]{4,}", (hint or "").lower()))
    if not hint_words:
        return candidates[0]

    ranked = sorted(
        candidates,
        key=lambda item: len(hint_words.intersection(set(re.findall(r"[a-zA-Z]{4,}", item.lower())))),
        reverse=True,
    )
    return ranked[0] if ranked else None


def _fallback_score(parsed_resume: dict[str, Any]) -> int:
    breakdown = _fallback_breakdown(parsed_resume, {})
    return round(
        breakdown["impact"] * 0.35
        + breakdown["clarity"] * 0.25
        + breakdown["structure"] * 0.2
        + breakdown["ats"] * 0.2
    )


def _fallback_breakdown(parsed_resume: dict[str, Any], issues_by_section: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    bullets = parsed_resume.get("experience", []) + parsed_resume.get("projects", [])
    weak_count = sum(1 for bullet in bullets if _detect_bullet_problems(bullet))
    section_count = sum(1 for key in ("summary", "experience", "projects", "skills", "education") if parsed_resume.get(key))
    skills_count = len(parsed_resume.get("skills", []))
    issue_count = sum(len(items) for items in issues_by_section.values()) if issues_by_section else weak_count

    return {
        "impact": max(35, min(100, 86 - issue_count * 7)),
        "clarity": max(40, min(100, 84 - weak_count * 5)),
        "structure": max(45, min(100, 45 + section_count * 10)),
        "ats": max(35, min(100, 45 + min(skills_count, 12) * 4)),
    }


def _default_strengths(score: int) -> list[str]:
    if score >= 80:
        return ["Strong foundation with enough substance for targeted polishing."]
    if score >= 60:
        return ["Readable resume foundation with clear room for higher-impact bullets."]
    return ["Enough raw material exists to build a stronger resume with focused edits."]


def _weaknesses_from_sections(sections: list[dict[str, Any]]) -> list[str]:
    weaknesses = []
    for section in sections:
        if section.get("issues"):
            weaknesses.append(f"{section.get('section', 'resume').title()} needs more specific, outcome-driven wording.")
    return weaknesses[:4] or ["No major weaknesses detected in the validated issue set."]


def _priority_from_sections(sections: list[dict[str, Any]]) -> list[str]:
    priorities = []
    for issue in flatten_issues({"sections": sections}):
        priorities.append(f"Fix: {issue.get('problem', 'Improve weak resume text')}")
    return priorities[:5] or ["Re-score after making targeted role-specific edits."]


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _normalize_section_name(value: Any) -> str:
    normalized = str(value or "resume").strip().lower()
    if normalized in {"work", "employment", "internships", "internship"}:
        return "experience"
    if normalized in {"project", "portfolio"}:
        return "projects"
    if normalized in {"technical skills", "technologies", "tools"}:
        return "skills"
    return re.sub(r"[^a-z0-9_-]", "_", normalized)[:40] or "resume"


def _clamp_int(value: Any, default: int = 0) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        number = default
    return max(0, min(100, number))


def _issue_id(section: str, original: str, improved: str) -> str:
    digest = hashlib.sha1(f"{section}|{original}|{improved}".encode("utf-8")).hexdigest()
    return digest[:12]
