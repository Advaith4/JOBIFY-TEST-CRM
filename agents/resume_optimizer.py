from crewai import Agent, LLM
import os
from dotenv import load_dotenv

load_dotenv()

def create_resume_optimizer():
    llm = LLM(
        model="groq/llama-3.3-70b-versatile",
        temperature=0.4,
        api_key=os.getenv("GROQ_API_KEY")
    )

    return Agent(
        role="Resume Analyzer",
        goal="Analyze the candidate's resume and provide precise, actionable improvements to make it stand out to ATS systems and human recruiters.",
        backstory=(
            "You are a seasoned technical recruiter and expert resume writer. "
            "You know exactly what hiring managers look for—impact, metrics, and clarity. "
            "You find formatting gaps, weak verbs, and poor skills presentation, and give exact advice to fix them."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

def create_resume_rewriter():
    llm = LLM(
        model="groq/llama-3.3-70b-versatile",
        temperature=0.5,
        api_key=os.getenv("GROQ_API_KEY")
    )
    return Agent(
        role="Resume Rewriter",
        goal="Rewrite weak resume bullet points to improve impact, clarity, and ATS compatibility.",
        backstory=(
            "You are a professional resume resume writer who specializes in transforming weak, passive bullet points "
            "into powerful, action-oriented achievements with quantifiable metrics. You preserve the original meaning "
            "but drastically improve how it reads to recruiters."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
