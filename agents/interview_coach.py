from crewai import Agent, LLM
import os
from dotenv import load_dotenv

load_dotenv()

def _get_llm(temperature=0.5):
    return LLM(
        model="groq/llama-3.1-8b-instant",
        temperature=temperature,
        api_key=os.getenv("GROQ_API_KEY")
    )

def create_interviewer():
    return Agent(
        role="Interviewer",
        goal="Ask precisely ONE challenging but realistic interview question tailored to the candidate's resume and target role, considering the current difficulty level.",
        backstory="You are an elite technical interviewer at a top-tier tech company. You test candidates on problem-solving, system design, and behavioral adaptability.",
        verbose=True,
        allow_delegation=False,
        llm=_get_llm(0.6)
    )

def create_evaluator():
    return Agent(
        role="Evaluator",
        goal="Evaluate the user's interview answer and provide a strict score and constructive feedback.",
        backstory="You are a strict but fair interview panelist who looks for depth, clarity, and structural soundness in a candidate's answer.",
        verbose=True,
        allow_delegation=False,
        llm=_get_llm(0.3)
    )

def create_followup_coach():
    return Agent(
        role="Follow-up Interviewer",
        goal="Generate a deeper, specific follow-up question based on the user's previous answer.",
        backstory="You dig deep into a candidate's stated knowledge to test the edges of their understanding. You don't accept superficial answers.",
        verbose=True,
        allow_delegation=False,
        llm=_get_llm(0.6)
    )

def create_difficulty_controller():
    return Agent(
        role="Difficulty Controller",
        goal="Determine the new interview difficulty level (1-10) based on the current evaluation score.",
        backstory="You are a dynamic adaptive testing system that ensures the candidate remains in their 'zone of proximal development'.",
        verbose=True,
        allow_delegation=False,
        llm=_get_llm(0.2)
    )

def create_interview_coach():
    return Agent(
        role="Interview Coach",
        goal="Generate challenging but realistic technical and behavioral interview questions tailored to the candidate's core skills.",
        backstory=(
            "You are an elite technical interviewer at a top-tier tech company. "
            "You test candidates not just on syntax, but on problem-solving, system design, and behavioral adaptability based on their past experiences."
        ),
        verbose=True,
        allow_delegation=False,
        llm=_get_llm(0.4)
    )
