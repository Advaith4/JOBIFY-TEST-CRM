import json

from crewai import Task

# Legacy implementation for /api/analyze UI
def create_interview_task(agent, resume_content):
    description = """
You are an Interview Coach.
Analyze the following resume:
---------------------
{resume}
---------------------
Based on the candidate's experience and skills, generate EXACTLY 4 interview questions they are likely to face.
Include 2 technical questions (based on their tools/languages) and 2 behavioral questions. Provide a short tip on how to answer each.

OUTPUT FORMAT (STRICT JSON ONLY):
{{
  "questions": [
    {{
      "type": "Technical",
      "question": "string",
      "tip": "string"
    }},
    {{
      "type": "Behavioral",
      "question": "string",
      "tip": "string"
    }}
  ]
}}
""".format(resume=resume_content)
    return Task(
        description=description,
        expected_output="Valid JSON containing exactly 4 interview questions with tips.",
        agent=agent
    )

def _json_context(value):
    return json.dumps(value if value is not None else {}, ensure_ascii=False, indent=2)


def create_interview_start_task(
    agent,
    role,
    difficulty,
    weak_areas=None,
    resume_context=None,
    section_scores=None,
    focus_mode="weak_area",
    training_mode="adaptive",
    interviewer_persona=None,
    coach_memory=None,
    domain_focus="",
):
    weak_areas = weak_areas or []
    resume_context = resume_context or {}
    section_scores = section_scores or {}
    interviewer_persona = interviewer_persona or {}
    coach_memory = coach_memory or {}

    description = """
You are a real interviewer and personal coach combined into one system.
The candidate is applying for the role: {role}.
The current difficulty level is {difficulty}/10.
Training mode: {training_mode}.
Domain focus: {domain_focus}.
Current requested focus mode: {focus_mode}.

INTERVIEWER PERSONA:
{interviewer_persona}

LONG-TERM COACH MEMORY:
{coach_memory}

RESUME-DERIVED WEAK AREAS:
{weak_areas}

SECTION SCORES:
{section_scores}

RESUME CONTEXT:
{resume_context}

QUESTION MIX POLICY:
- Across the session, approximately 60% of questions must target weak areas from Resume Lab.
- Approximately 40% should test general role-critical knowledge.
- If training mode is weak_area_only, ask only from weak areas.
- If training mode is domain_specific, prioritize domain_focus and role-specific depth.
- If training mode is behavioral_only, ask behavioral/leadership/communication questions only.

Generate exactly ONE targeted interview question for this candidate.
If focus mode is "weak_area", ask about a real weak area or low-scoring section from the resume.
If focus mode is "domain_specific", ask a realistic domain-specific question.
If focus mode is "behavioral_only", ask a behavioral question tied to their resume.
If focus mode is "general", ask a role-critical question that still fits the candidate's background.
If the difficulty is high (7-10), make it a system design or deep architectural question.
If the difficulty is medium (4-6), make it a practical coding or scenario question.
If the difficulty is low (1-3), make it a basic conceptual or behavioral question.
Do not invent experience. If referencing resume content, use only the provided resume context.

HUMAN-LIKE INTERVIEW BEHAVIOR:
- Use a natural conversational tone matching the interviewer persona.
- You may briefly interrupt or add pressure only as text, e.g. "I'll pause you there..." or "Be specific here..."
- Ask one question only, but make it feel like a real interviewer setting expectations.
- Include the reason for the question internally in JSON fields, not as extra prose outside JSON.

Return ONLY JSON. Do not include any extra text.

OUTPUT FORMAT (STRICT JSON ONLY):
{{
  "question": "The interview question string",
  "focus_area": "specific weak area or general competency",
  "focus_type": "weak_area, general, domain, or behavioral",
  "interviewer_signal": "short realistic cue such as 'I will press for specifics here'",
  "pressure_level": "low, medium, or high"
}}
""".format(
        role=role,
        difficulty=difficulty,
        weak_areas=_json_context(weak_areas),
        section_scores=_json_context(section_scores),
        resume_context=_json_context(resume_context),
        focus_mode=focus_mode,
        training_mode=training_mode,
        interviewer_persona=_json_context(interviewer_persona),
        coach_memory=_json_context(coach_memory),
        domain_focus=domain_focus or "role fundamentals",
    )

    return Task(
        description=description,
        expected_output="Valid JSON with a single interview question.",
        agent=agent
    )

def create_evaluator_task(agent, question, answer):
    description = """
You are the Evaluator.
Review the candidate's answer to the following question:

Question: {question}
Candidate Answer: {answer}

Provide a strict score from 1 to 10. 
CRITICAL RULES FOR SCORING:
- If the question asked for code or steps and the answer is just one sentence, MAXIMUM score is 4.
- If the candidate says "I don't know", the score MUST be 1 or 2.
- Only award 8-10 for comprehensive, technically accurate, and well-structured answers.

List strengths (if any), weaknesses, and a concrete suggestion for improvement.

Return ONLY JSON. Do not include any extra text.

OUTPUT FORMAT (STRICT JSON ONLY):
{{
  "score": 8,
  "technical_depth": 7,
  "communication": 8,
  "missing_concepts": ["concept 1", "concept 2"],
  "improvement": "Concrete suggestion here."
}}
""".format(question=question, answer=answer)

    return Task(
        description=description,
        expected_output="Valid JSON with score, strengths, weaknesses, and improvements.",
        agent=agent
    )

def create_followup_task(
    agent,
    role,
    question,
    answer,
    difficulty,
    weak_areas=None,
    resume_context=None,
    section_scores=None,
    focus_mode="weak_area",
    training_mode="adaptive",
    interviewer_persona=None,
    coach_memory=None,
    domain_focus="",
):
    weak_areas = weak_areas or []
    resume_context = resume_context or {}
    section_scores = section_scores or {}
    interviewer_persona = interviewer_persona or {}
    coach_memory = coach_memory or {}
    description = """
You are the Follow-up Interviewer for a realistic AI career coach.
Role: {role}.
Difficulty: {difficulty}/10.
Training mode: {training_mode}.
Adaptive focus mode: {focus_mode}.
Domain focus: {domain_focus}.

INTERVIEWER PERSONA:
{interviewer_persona}

LONG-TERM COACH MEMORY:
{coach_memory}

RESUME-DERIVED WEAK AREAS:
{weak_areas}

SECTION SCORES:
{section_scores}

RESUME CONTEXT:
{resume_context}

Question Asked: {question}
Candidate Answer: {answer}

Based on the answer, generate exactly ONE follow-up question. 
- If the candidate gave a strong answer, increase depth and connect it to a resume weak area or a realistic job constraint.
- If the candidate struggled or said "I don't know", simplify and ask a more fundamental question about the weak topic.
- Preserve the 60/40 policy: 60% weak-area training, 40% general role coverage.
- Respect training mode: weak_area_only, domain_specific, behavioral_only, or adaptive.
- Use long-term memory to revisit recurring weak areas if relevant.
- Use human-like interviewer pressure. You may briefly interrupt: "Let me stop you there..." or "Give me a concrete example."
- Do not invent projects, tools, or achievements not present in the resume context.

Return ONLY JSON. Do not include any extra text.

OUTPUT FORMAT (STRICT JSON ONLY):
{{
  "question": "The follow-up interview question string",
  "focus_area": "specific weak area or general competency",
  "focus_type": "weak_area, general, domain, or behavioral",
  "interviewer_signal": "short realistic cue or coaching pressure",
  "pressure_level": "low, medium, or high"
}}
""".format(
        role=role,
        question=question,
        answer=answer,
        difficulty=difficulty,
        weak_areas=_json_context(weak_areas),
        section_scores=_json_context(section_scores),
        resume_context=_json_context(resume_context),
        focus_mode=focus_mode,
        training_mode=training_mode,
        interviewer_persona=_json_context(interviewer_persona),
        coach_memory=_json_context(coach_memory),
        domain_focus=domain_focus or "role fundamentals",
    )

    return Task(
        description=description,
        expected_output="Valid JSON with a single follow-up question.",
        agent=agent
    )

def create_difficulty_task(agent, current_difficulty, score):
    description = """
You are the Difficulty Controller.
Current Difficulty: {current_difficulty}/10
Last Answer Score: {score}/10

Adjust the difficulty for the next question.
Rule of thumb:
- If score >= 8: increase difficulty by 1.
- If score <= 4: decrease difficulty by 1.
- Else: keep it the same.
Difficulty must stay between 1 and 10.

Return ONLY JSON. Do not include any extra text.

OUTPUT FORMAT (STRICT JSON ONLY):
{{
  "new_difficulty": 5
}}
""".format(current_difficulty=current_difficulty, score=score)

    return Task(
        description=description,
        expected_output="Valid JSON with the new integer difficulty.",
        agent=agent
    )
