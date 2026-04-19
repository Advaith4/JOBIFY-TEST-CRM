"""
job_search.py - Fetches real job listings from external job APIs.

Provider strategy:
  - Primary: Jooble REST API
  - Fallback: JSearch via RapidAPI

Architecture:
  - All job data (title, company, URL, description) comes from live APIs.
  - The LLM's role is ONLY to rank/filter from this real data - never to invent jobs.
  - Zero hallucinated URLs. Every link is the direct apply link from the provider.
  - Query diversification prevents one recruiter/company from dominating results.
"""

import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"
_cache: dict[str, list[dict]] = {}


def _jooble_url(api_key: str) -> str:
    base_url = os.getenv("JOOBLE_API_BASE_URL", "https://in.jooble.org/api/{api_key}")
    return base_url.format(api_key=api_key)


def _jsearch_headers() -> dict:
    return {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY", ""),
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }


def _request(method: str, url: str, **kwargs) -> requests.Response:
    """
    Call external job APIs without inheriting broken system proxy variables.
    """
    with requests.Session() as session:
        session.trust_env = False
        return session.request(method=method, url=url, **kwargs)


def _normalize_job(job: dict) -> dict:
    return {
        "title": (job.get("title") or "").strip(),
        "company": (job.get("company") or "").strip(),
        "url": (job.get("url") or "").strip(),
        "location": (job.get("location") or "Remote").strip(),
        "description": (job.get("description") or "").strip()[:300],
    }


def _fetch_jobs_from_jooble(query: str, location: str = "", num_results: int = 10, page: int = 1) -> list[dict]:
    """
    Fetch real job listings from Jooble for a given query and location.
    """
    api_key = os.getenv("JOOBLE_API_KEY", "").strip()
    if not api_key:
        logger.info("JOOBLE_API_KEY is not set. Skipping Jooble lookup.")
        return []

    cache_key = f"jooble|{query}|{location}|{num_results}|{page}"
    if cache_key in _cache:
        logger.info("Jooble cache hit for query='%s' location='%s'", query, location)
        return _cache[cache_key]

    payload = {
        "keywords": query,
        "page": str(page),
        "ResultOnPage": str(min(max(num_results, 1), 10)),
        "companysearch": "false",
        "SearchMode": "0",
    }
    if location:
        payload["location"] = location

    data = None
    for attempt in range(2):
        try:
            response = _request("POST", _jooble_url(api_key), json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            break
        except requests.exceptions.Timeout:
            logger.warning("Jooble API timed out (attempt %d/2) for query='%s' location='%s'", attempt + 1, query, location)
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            logger.warning(
                "Jooble API HTTP error %s (attempt %d/2) for query='%s' location='%s'",
                status_code,
                attempt + 1,
                query,
                location,
            )
            if status_code in (403, 429):
                break
            break
        except Exception as exc:
            logger.warning("Jooble API unexpected error (attempt %d/2): %s", attempt + 1, exc)
            break

    if not data:
        logger.error("Jooble API failed to fetch data.")
        return []

    jobs = [
        _normalize_job({
            "title": job.get("title"),
            "company": job.get("company"),
            "url": job.get("link"),
            "location": job.get("location") or location or "Remote",
            "description": job.get("snippet"),
        })
        for job in data.get("jobs", [])
    ]

    logger.info("Fetched %d jobs from Jooble for query='%s' location='%s'", len(jobs), query, location)
    _cache[cache_key] = jobs
    return jobs


def _fetch_jobs_from_jsearch(query: str, location: str = "", num_results: int = 10, page: int = 1) -> list[dict]:
    """
    Fetch real job listings from JSearch for a given query string.
    """
    if not os.getenv("RAPIDAPI_KEY"):
        logger.info("RAPIDAPI_KEY is not set. Skipping JSearch lookup.")
        return []

    effective_query = f"{query} {location}".strip() if location and location.lower() not in query.lower() else query
    cache_key = f"jsearch|{effective_query}|{num_results}|{page}"
    if cache_key in _cache:
        logger.info("JSearch cache hit for query='%s'", effective_query)
        return _cache[cache_key]

    params = {
        "query": effective_query,
        "page": str(page),
        "num_pages": "1",
        "num_results_per_page": str(min(max(num_results, 1), 10)),
    }

    data = None
    for attempt in range(2):
        try:
            response = _request(
                "GET",
                _JSEARCH_URL,
                headers=_jsearch_headers(),
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            break
        except requests.exceptions.Timeout:
            logger.warning("JSearch API timed out (attempt %d/2) for query='%s'", attempt + 1, effective_query)
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            logger.warning("JSearch API HTTP error %s (attempt %d/2) for query='%s'", status_code, attempt + 1, effective_query)
            if status_code == 429:
                break
            break
        except Exception as exc:
            logger.warning("JSearch API unexpected error (attempt %d/2): %s", attempt + 1, exc)
            break

    if not data:
        logger.error("JSearch API failed to fetch data.")
        return []

    jobs = []
    for job in data.get("data", []):
        raw_desc = job.get("job_description") or ""
        apply_link = (job.get("job_apply_link") or "").strip()
        if not apply_link:
            apply_link = (job.get("job_google_link") or "").strip()

        jobs.append(_normalize_job({
            "title": job.get("job_title"),
            "company": job.get("employer_name"),
            "url": apply_link,
            "location": job.get("job_city") or job.get("job_state") or job.get("job_country") or location or "Remote",
            "description": raw_desc,
        }))

    logger.info("Fetched %d jobs from JSearch for query='%s'", len(jobs), effective_query)
    _cache[cache_key] = jobs
    return jobs


def fetch_jobs_from_api(query: str, location: str = "", num_results: int = 10, page: int = 1) -> list[dict]:
    """
    Fetch real jobs using Jooble first, then fall back to JSearch if needed.
    """
    jobs = _fetch_jobs_from_jooble(query=query, location=location, num_results=num_results, page=page)
    if jobs:
        return jobs

    if os.getenv("JOOBLE_API_KEY"):
        logger.warning("Jooble returned no jobs for query='%s'. Falling back to JSearch.", query)

    jobs = _fetch_jobs_from_jsearch(query=query, location=location, num_results=num_results, page=page)
    if jobs:
        return jobs

    logger.error("All configured job providers failed. Set JOOBLE_API_KEY or RAPIDAPI_KEY.")
    return []


_QUERY_TEMPLATES = [
    "{role}",
    "{role} entry level",
    "{role} junior remote",
    "{role} internship",
    "{role} fresher",
]


def fetch_jobs_for_roles(roles: list[str], prefs: dict = None, jobs_per_role: int = 3) -> list[dict]:
    """
    Fetch real job listings for a list of roles using query diversification.

    Strategy:
      - For each role, run up to 3 differently-phrased queries.
      - Deduplicate by (title, company, location).
      - Cap repeated companies so one employer does not dominate the result set.
    """
    seen_job_keys: set[tuple] = set()
    company_count: dict[str, int] = {}
    all_jobs: list[dict] = []

    max_jobs_per_company = 2
    target_total = max(len(roles) * jobs_per_role, 10)

    for role in roles:
        modifiers = []
        location = ""
        if prefs:
            location = (prefs.get("location") or "").strip()
            exp = (prefs.get("experience") or "").strip()
            mode = (prefs.get("work_mode") or "").strip()
            jtype = (prefs.get("job_type") or "").strip()

            if mode and mode.lower() != "any":
                modifiers.append(mode)
            if jtype and jtype.lower() != "any":
                modifiers.append(jtype)
            if exp and exp.lower() != "any":
                modifiers.append(exp)

        modifier_str = " ".join(modifiers).strip()
        templates = [f"{{role}} {modifier_str}", "{role}"] if modifier_str else _QUERY_TEMPLATES[:3]

        for tmpl in templates:
            if len(all_jobs) >= target_total:
                break

            query = tmpl.format(role=role).strip()
            logger.info("Fetching jobs - query='%s' location='%s'", query, location)
            results = fetch_jobs_from_api(query=query, location=location, num_results=5)

            for job in results:
                title = job["title"].strip().lower()
                company = job["company"].strip().lower()

                if not job["url"] or not job["url"].startswith("http"):
                    continue

                key = (title, company, job["location"].strip().lower())
                if key in seen_job_keys:
                    continue

                if company_count.get(company, 0) >= max_jobs_per_company:
                    logger.debug("Skipping duplicate company: %s", company)
                    continue

                seen_job_keys.add(key)
                company_count[company] = company_count.get(company, 0) + 1
                all_jobs.append(job)

    logger.info("Total unique jobs fetched (company-diverse): %d", len(all_jobs))
    return all_jobs
