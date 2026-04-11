"""
job_search.py – Fetches REAL job listings from JSearch API (RapidAPI).

Architecture:
  - All job data (title, company, URL, description) comes from the live API.
  - The LLM's role is ONLY to rank/filter from this real data — never to invent jobs.
  - Zero hallucinated URLs. Every link is the direct apply link from the API.
  - Query diversification prevents one recruiter/company from dominating results.
"""
import os
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"

# Headers are built dynamically so we pick up the key at call time (not import time)
def _headers() -> dict:
    return {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY", ""),
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

_cache = {}

def fetch_jobs_from_api(query: str, num_results: int = 10, page: int = 1) -> list[dict]:
    """
    Fetch REAL job listings from JSearch API for a given query string.

    Returns a list of structured job dicts:
      {title, company, url, location, description}

    On any failure, returns an empty list (caller handles fallback).
    """
    if not os.getenv("RAPIDAPI_KEY"):
        logger.error("RAPIDAPI_KEY is not set. Cannot fetch jobs from JSearch.")
        return []

    cache_key = f"{query}|{num_results}|{page}"
    if cache_key in _cache:
        logger.info("JSearch cache hit for query: '%s'", query)
        return _cache[cache_key]

    params = {
        "query": query,
        "page": str(page),
        "num_pages": "1",
        "num_results_per_page": str(min(num_results, 10)),  # API max = 10
    }

    data = None
    for attempt in range(3):
        try:
            response = requests.get(
                _JSEARCH_URL,
                headers=_headers(),
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            break  # success
        except requests.exceptions.Timeout:
            logger.warning("JSearch API timed out (attempt %d/3) for query: %s", attempt+1, query)
        except requests.exceptions.HTTPError as exc:
            logger.warning("JSearch API HTTP error %s (attempt %d/3) for query: %s", exc.response.status_code, attempt+1, query)
            if exc.response.status_code == 429:
                time.sleep(2 * (attempt + 1))
                continue
            break
        except Exception as exc:
            logger.warning("JSearch API unexpected error (attempt %d/3): %s", attempt+1, exc)
            break

    if not data:
        logger.error("JSearch API failed to fetch data.")
        return []

    jobs = []
    for job in data.get("data", []):
        raw_desc = job.get("job_description") or ""
        apply_link = job.get("job_apply_link", "").strip()
        if not apply_link:
            apply_link = job.get("job_google_link", "").strip()  # fallback
        jobs.append({
            "title": job.get("job_title", "").strip(),
            "company": job.get("employer_name", "").strip(),
            "url": apply_link,
            "location": (job.get("job_city") or job.get("job_state")
                         or job.get("job_country") or "Remote").strip(),
            "description": raw_desc[:300].strip(),
        })

    logger.info("Fetched %d jobs from JSearch for query: '%s'", len(jobs), query)
    _cache[cache_key] = jobs
    return jobs


# ── Query diversification templates ────────────────────────────────────────────
# Using varied queries for the same role prevents one recruiter / staffing
# agency (like SynergisticIT) from dominating the results list.
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
      - For each role, run up to 3 differently-phrased queries (entry level, remote, internship…)
      - Deduplicate by (title, company) — exact match
      - Also soft-deduplicate: if a company already appears ≥3 times, skip further listings
        from that company to prevent one recruiter from dominating.

    Returns a flat, deduplicated, company-diverse list of job dicts.
    """
    seen_job_keys: set[tuple] = set()
    company_count: dict[str, int] = {}
    all_jobs: list[dict] = []

    MAX_JOBS_PER_COMPANY = 2   # hard cap per employer across the full result set
    TARGET_TOTAL = max(len(roles) * jobs_per_role, 10)

    for role in roles:
        # Build query modifiers based on user preferences
        modifiers = []
        if prefs:
            loc = prefs.get('location', '').strip()
            exp = prefs.get('experience', '').strip()
            mode = prefs.get('work_mode', '').strip()
            jtype = prefs.get('job_type', '').strip()
            
            if loc and loc.lower() != 'any':
                modifiers.append(loc)
            if mode and mode.lower() != 'any':
                modifiers.append(mode)
            if jtype and jtype.lower() != 'any':
                modifiers.append(jtype)
            if exp and exp.lower() != 'any':
                modifiers.append(exp)

        modifier_str = " ".join(modifiers).strip()
        
        if modifier_str:
            # High specificity when preferences are provided
            templates = [
                f"{{role}} {modifier_str}",
                f"{{role}} {prefs.get('location', 'India')}",
            ]
        else:
            templates = _QUERY_TEMPLATES[:3]

        for tmpl in templates:
            if len(all_jobs) >= TARGET_TOTAL:
                break
            query = tmpl.format(role=role)
            logger.info("Fetching jobs — query: '%s'", query)
            results = fetch_jobs_from_api(query=query, num_results=5)

            for job in results:
                title   = job["title"].strip().lower()
                company = job["company"].strip().lower()

                # Filter Point 8: URL validation
                if not job["url"] or not job["url"].startswith("http"):
                    continue

                # Point 7: Deduplicate by (title + company + location)
                key = (title, company, job["location"].strip().lower())
                if key in seen_job_keys:
                    continue

                # Company diversity cap — skip if this employer is already well-represented
                if company_count.get(company, 0) >= MAX_JOBS_PER_COMPANY:
                    logger.debug("Skipping duplicate company: %s", company)
                    continue

                seen_job_keys.add(key)
                company_count[company] = company_count.get(company, 0) + 1
                all_jobs.append(job)

    logger.info("Total unique jobs fetched (company-diverse): %d", len(all_jobs))
    return all_jobs
