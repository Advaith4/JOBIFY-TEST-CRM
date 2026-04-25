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
You are Jobify Resume Lab: a senior technical recruiter, ATS specialist, and resume coach.
Analyze the resume deeply and return ONLY strict JSON.

---------------------
{role_ctx}
RESUME:
{resume}
---------------------

CRITICAL RULES:
- Every issue MUST map to exact real text copied from the resume in the "original" field.
- Every issue MUST include a directly improved replacement in the "improved" field.
- Do not provide generic suggestions.
- Do not invent fake employers, fake metrics, fake tools, or fake achievements.
- If a metric is missing, improve action/clarity/scope without fabricating a number.
- Prefer high-value issues from summary, experience, projects, and skills.
- Return at most 8 total issues.
- Prefer issues that are immediately fixable and have visible recruiter impact.
- Summary feedback must feel like a real recruiter readout, not generic praise.
- action_type must be "replace".

Return ONLY JSON. Do not include any extra text.

OUTPUT FORMAT (STRICT JSON ONLY):
{{
  "score": 82,
  "breakdown": {{
    "impact": 60,
    "clarity": 75,
    "structure": 85,
    "ats": 80
  }},
  "sections": [
    {{
      "section": "experience",
      "issues": [
        {{
          "original": "Worked on chatbot project",
          "problem": "Weak verb and no clear ownership or outcome",
          "improved": "Developed a chatbot project, clarifying ownership, tools used, and project outcome.",
          "action_type": "replace",
          "severity": "high",
          "category": "impact"
        }}
      ]
    }}
  ],
  "summary_feedback": {{
    "strengths": ["specific strength"],
    "weaknesses": ["specific weakness"],
    "priority_fixes": ["specific next fix"]
  }}
}}
""".format(role_ctx=role_ctx, resume=resume_content)

    return Task(
        description=description,
        expected_output="Valid JSON matching Jobify Resume Lab schema with grounded issues and replacements.",
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
