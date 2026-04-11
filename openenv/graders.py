from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any


ACTION_VERBS = {
    "developed",
    "built",
    "improved",
    "optimized",
    "created",
    "designed",
    "implemented",
    "delivered",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _try_parse_json(text: str) -> Any | None:
    cleaned = _strip_code_fences(text)
    try:
        return json.loads(cleaned)
    except Exception:
        return None


def _normalize_match_score(value: Any) -> Any:
    if isinstance(value, float) and 0 <= value <= 1:
        return int(round(value * 100))
    return value


def _normalize_model_output(task_id: str, model_output: str) -> tuple[str, Any | None]:
    cleaned = _strip_code_fences(model_output)
    parsed = _try_parse_json(cleaned)
    if not isinstance(parsed, dict):
        return cleaned, parsed

    normalized = dict(parsed)
    if task_id == "skill_extraction" and isinstance(normalized.get("validation"), str):
        normalized["validation"] = {
            "is_valid_resume": True,
            "message": normalized["validation"],
        }
    if task_id == "job_matching" and "match_score" in normalized:
        normalized["match_score"] = _normalize_match_score(normalized["match_score"])
    if task_id == "resume_optimization":
        rewritten = normalized.get("rewritten_bullets")
        if isinstance(rewritten, dict):
            flattened: list[str] = []
            for value in rewritten.values():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and "improved" in item:
                            flattened.append(str(item["improved"]))
                        else:
                            flattened.append(str(item))
            normalized["rewritten_bullets"] = flattened
    return json.dumps(normalized, ensure_ascii=True, sort_keys=True), normalized


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9%+#.]+", _normalize(text)))


def _flatten(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        flattened: list[str] = []
        for key, item in value.items():
            flattened.append(str(key))
            flattened.extend(_flatten(item))
        return flattened
    if isinstance(value, Iterable):
        flattened = []
        for item in value:
            flattened.extend(_flatten(item))
        return flattened
    return [str(value)]


def _as_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _keyword_overlap_score(model_text: str, expected_text: str) -> float:
    expected_tokens = _tokenize(expected_text)
    if not expected_tokens:
        return 0.0
    model_tokens = _tokenize(model_text)
    overlap = expected_tokens.intersection(model_tokens)
    return len(overlap) / len(expected_tokens)


def _relevance_score(model_text: str, expected_output: Any, observation_text: str = "") -> float:
    expected_chunks = _flatten(expected_output)
    if observation_text:
        expected_chunks.extend([observation_text])
    matches = 0
    total = 0
    normalized_model = _normalize(model_text)
    for chunk in expected_chunks:
        normalized_chunk = _normalize(chunk)
        if not normalized_chunk:
            continue
        total += 1
        if normalized_chunk in normalized_model or any(
            token in normalized_model for token in _tokenize(normalized_chunk)
        ):
            matches += 1
    if total == 0:
        return 0.0
    return matches / total


def _clarity_score(model_text: str) -> float:
    normalized = _normalize(model_text)
    if not normalized:
        return 0.0
    score = 0.2
    if any(verb in normalized for verb in ACTION_VERBS):
        score += 0.35
    if re.search(r"\d", normalized) or "%" in normalized:
        score += 0.25
    if "{" in model_text and "}" in model_text:
        score += 0.1
    if len(normalized.split()) >= 15:
        score += 0.1
    return min(score, 1.0)


def _penalty(model_text: str, expected_text: str, observation_text: str = "") -> float:
    normalized = _normalize(model_text)
    if not normalized:
        return 1.0
    if len(normalized.split()) < 3:
        return 0.35
    if _keyword_overlap_score(normalized, expected_text) == 0 and _relevance_score(
        normalized,
        expected_text,
        observation_text,
    ) == 0:
        return 0.5
    return 0.0


def compute_reward(correctness: float, relevance: float, clarity: float) -> float:
    reward = (0.4 * correctness) + (0.3 * relevance) + (0.3 * clarity)
    return max(0.0, min(1.0, reward))


def grade_skill_extraction(model_output: str, expected_output: Any, observation_text: str = "") -> dict[str, float]:
    cleaned_output, parsed_output = _normalize_model_output("skill_extraction", model_output)
    expected_text = _as_text(expected_output)
    expected_skills = expected_output.get("skills", []) if isinstance(expected_output, dict) else []
    skill_bonus = 0.0
    if isinstance(parsed_output, dict):
        model_skills = parsed_output.get("skills", [])
        if isinstance(model_skills, list) and expected_skills:
            overlap = len(
                {str(skill).lower() for skill in model_skills}.intersection(
                    {str(skill).lower() for skill in expected_skills}
                )
            )
            skill_bonus = overlap / len(expected_skills)
    correctness = min(1.0, (_keyword_overlap_score(cleaned_output, expected_text) * 0.7) + (skill_bonus * 0.3))
    relevance = _relevance_score(cleaned_output, expected_output, observation_text)
    clarity = _clarity_score(cleaned_output)
    penalty = _penalty(cleaned_output, expected_text, observation_text)
    total = max(0.0, compute_reward(correctness, relevance, clarity) - penalty)
    return {
        "correctness": round(correctness, 4),
        "relevance": round(relevance, 4),
        "clarity": round(clarity, 4),
        "penalty": round(penalty, 4),
        "score": round(total, 4),
    }


def grade_job_matching(model_output: str, expected_output: Any, observation_text: str = "") -> dict[str, float]:
    cleaned_output, parsed_output = _normalize_model_output("job_matching", model_output)
    expected_text = _as_text(expected_output)
    correctness = _keyword_overlap_score(cleaned_output, expected_text)
    if isinstance(parsed_output, dict) and isinstance(expected_output, dict):
        expected_skills = {str(skill).lower() for skill in expected_output.get("matched_skills", [])}
        model_skills = parsed_output.get("matched_skills", [])
        if isinstance(model_skills, list) and expected_skills:
            overlap = len(expected_skills.intersection({str(skill).lower() for skill in model_skills}))
            correctness = min(1.0, (correctness * 0.7) + (0.3 * (overlap / len(expected_skills))))
    relevance = _relevance_score(cleaned_output, expected_output, observation_text)
    clarity = _clarity_score(cleaned_output)
    if "match_score" in _normalize(cleaned_output):
        clarity = min(1.0, clarity + 0.1)
    penalty = _penalty(cleaned_output, expected_text, observation_text)
    total = max(0.0, compute_reward(correctness, relevance, clarity) - penalty)
    return {
        "correctness": round(correctness, 4),
        "relevance": round(relevance, 4),
        "clarity": round(clarity, 4),
        "penalty": round(penalty, 4),
        "score": round(total, 4),
    }


def grade_resume_optimization(model_output: str, expected_output: Any, observation_text: str = "") -> dict[str, float]:
    cleaned_output, parsed_output = _normalize_model_output("resume_optimization", model_output)
    expected_text = _as_text(expected_output)
    correctness = _keyword_overlap_score(cleaned_output, expected_text)
    if isinstance(parsed_output, dict) and isinstance(expected_output, dict):
        expected_issues = {str(item).lower() for item in expected_output.get("issues", [])}
        model_issues = parsed_output.get("issues", [])
        if isinstance(model_issues, list) and expected_issues:
            overlap = len(expected_issues.intersection({str(item).lower() for item in model_issues}))
            correctness = min(1.0, (correctness * 0.75) + (0.25 * (overlap / len(expected_issues))))
    relevance = _relevance_score(cleaned_output, expected_output, observation_text)
    clarity = _clarity_score(cleaned_output)
    normalized = _normalize(cleaned_output)
    if any(verb in normalized for verb in ACTION_VERBS) and (
        re.search(r"\d", normalized) or "%" in normalized
    ):
        clarity = min(1.0, clarity + 0.15)
    penalty = _penalty(cleaned_output, expected_text, observation_text)
    total = max(0.0, compute_reward(correctness, relevance, clarity) - penalty)
    return {
        "correctness": round(correctness, 4),
        "relevance": round(relevance, 4),
        "clarity": round(clarity, 4),
        "penalty": round(penalty, 4),
        "score": round(total, 4),
    }


def grade_action(
    task_id: str,
    model_output: str,
    expected_output: Any,
    observation_text: str = "",
) -> dict[str, float]:
    graders = {
        "skill_extraction": grade_skill_extraction,
        "job_matching": grade_job_matching,
        "resume_optimization": grade_resume_optimization,
    }
    if task_id not in graders:
        raise KeyError(f"Unknown task_id: {task_id}")
    return graders[task_id](model_output, expected_output, observation_text)
