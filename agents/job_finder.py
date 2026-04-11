import os
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv()


def create_job_finder():
    """
    Job Finder agent.
    The real job search is done externally via DuckDuckGo (utils/job_search.py)
    before this agent runs. The agent's role is purely to:
      Phase 1 — infer the best matching job roles from the resume.
      Phase 3 — format pre-fetched real search results into clean JSON.
    """
    llm = LLM(
        model="groq/llama-3.1-8b-instant",
        temperature=0.2,
        api_key=os.getenv("GROQ_API_KEY")
    )

    job_finder = Agent(
        role="Job Finder and Career Strategist",
        goal=(
            "Accurately identify the best entry-level job roles for the candidate "
            "and format real, pre-fetched job search results into a clean, structured JSON output."
        ),
        backstory=(
            "You are an expert technical recruiter. You analyze resumes to identify "
            "the candidate's strongest skills and best-fit job roles. You are given real "
            "job search results fetched from the internet, and your task is to select and "
            "format the most relevant ones. You never invent URLs or company names."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm
    )

    return job_finder