from crewai import Task

# Legacy implementation for /api/analyze UI
def create_resume_task(agent, resume_content):
    description = """
You are a Resume Optimizer.
Analyze the following resume:
---------------------
{resume}
---------------------
Provide EXACTLY 4 actionable improvement points to make this resume better.

Return ONLY JSON. Do not include any extra text.

OUTPUT FORMAT (STRICT JSON ONLY):
{{
  "improvements": ["improvement 1", "improvement 2", "improvement 3", "improvement 4"]
}}
""".format(resume=resume_content)
    return Task(
        description=description,
        expected_output="Valid JSON containing exactly 4 resume improvements.",
        agent=agent
    )

def create_resume_analysis_task(agent, resume_content, target_role=""):
    role_ctx = f"Target Role: {target_role}\n" if target_role else "Target Role: General Software Engineering\n"
    description = """
You are an expert Resume Analyzer and ATS Optimization Specialist.
Analyze the following resume deeply.

---------------------
{role_ctx}
RESUME:
{resume}
---------------------

Identify specific issues (e.g., weak verbs, lack of metrics, formatting errors).
Provide overall improvements and a qualitative score.
Provide feedback on specific sections: skills, experience, and projects.

Return ONLY JSON. Do not include any extra text.

OUTPUT FORMAT (STRICT JSON ONLY):
{{
  "score": 75,
  "issues": ["Weak verb in experience", "No metrics in projects"],
  "improvements": ["Use strong action verbs", "Quantify bullet points"],
  "section_feedback": {{
    "skills": "feedback here",
    "experience": "feedback here",
    "projects": "feedback here"
  }}
}}
""".format(role_ctx=role_ctx, resume=resume_content)

    return Task(
        description=description,
        expected_output="Valid JSON containing resume score, issues, improvements, and section feedback.",
        agent=agent
    )


def create_bullet_rewriting_task(agent, resume_content):
    description = """
You are a Resume Rewriter.
Read the following resume content and identify 3 to 5 weak, passive, or non-quantified bullet points.

---------------------
RESUME:
{resume}
---------------------

Rewrite them to be highly impactful, action-oriented, and ATS-friendly. 
CRITICAL: Do NOT add fake metrics, numbers, or achievements. Only improve the wording, verbs, and structure. Ensure you preserve their original meaning.

Return ONLY JSON. Do not include any extra text.

OUTPUT FORMAT (STRICT JSON ONLY):
{{
  "rewritten_lines": [
    {{
      "original": "original weak line 1",
      "improved": "Improved, action-oriented line 1"
    }},
    {{
      "original": "original weak line 2",
      "improved": "Improved, action-oriented line 2"
    }}
  ]
}}
""".format(resume=resume_content)

    return Task(
        description=description,
        expected_output="Valid JSON containing original and improved rewritten bullet points.",
        agent=agent
    )
