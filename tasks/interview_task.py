import json

from crewai import Task


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
        agent=agent,
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
You are a realistic interviewer and career coach running a live interview.
Candidate role target: {role}
Difficulty: {difficulty}/10
Training mode: {training_mode}
Domain focus: {domain_focus}
Requested focus mode: {focus_mode}

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

INTERVIEW RULES:
- Ask exactly ONE question, but make it feel like a real interviewer turn.
- The question must be detailed and specific, not generic.
- If focus_mode is weak_area, anchor the question to a weak area or low-scoring section.
- If focus_mode is domain_specific, prioritize domain_focus and technical depth.
- If focus_mode is behavioral_only, ask a behavioral question tied to real resume evidence.
- If difficulty is 7-10, press on tradeoffs, architecture, or edge cases.
- If difficulty is 4-6, ask a practical scenario or implementation question.
- If difficulty is 1-3, ask a foundational conceptual or behavioral question.
- You may apply realistic pressure with phrases like "Let me stop you there" or "Be specific here".
- Do not invent projects, tools, or achievements not present in the provided context.

STYLE RULES:
- Make the interviewer sound human, direct, and emotionally believable.
- Include enough context so the candidate knows what level of detail is expected.
- Return a question that would naturally lead to a 5-10 line answer.

Return ONLY JSON.

OUTPUT FORMAT:
{{
  "question": "2-4 sentence interviewer turn with the actual question and realistic pressure",
  "focus_area": "specific weak area or general competency",
  "focus_type": "weak_area, general, domain, or behavioral",
  "interviewer_signal": "short realistic cue such as 'I will challenge vague claims here'",
  "pressure_level": "low, medium, or high",
  "answer_expectation": "short guidance on how the candidate should answer"
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
        expected_output="Valid JSON with a single realistic interview opening turn.",
        agent=agent,
    )


def create_evaluator_task(
    agent,
    question,
    answer,
    conversation_history=None,
    focus_area="",
    interviewer_persona=None,
):
    conversation_history = conversation_history or []
    interviewer_persona = interviewer_persona or {}
    description = f"""
You are the evaluator for a live mock interview. Evaluate the CANDIDATE ANSWER specifically against the QUESTION and RECENT CONVERSATION HISTORY. Be concrete and avoid generic, templated language.

INTERVIEWER PERSONA:
{interviewer_persona}

CURRENT FOCUS AREA:
{focus_area}

RECENT CONVERSATION HISTORY (most recent items):
{conversation_history}

QUESTION:
{question}

CANDIDATE ANSWER:
{answer}

STRICT INSTRUCTIONS (MUST FOLLOW):
- Return ONLY valid JSON matching the exact schema below. Do not include any extra text, commentary, or explanation.
- All array fields must contain at least 3 concise, specific items. If fewer than 3 real observations exist, synthesize additional precise suggestions tied to the candidate's answer (not generic filler).
- Use specific examples drawn from the provided answer where possible.
- Avoid phrases like "good job", "try to be more specific", or any vague stock feedback.

REQUIRED OUTPUT SCHEMA (STRICT JSON ONLY):
{{
    "score": number,                   // 0-10 integer; overall quality of this answer
    "confidence": number,              // 0-10 integer; evaluator confidence in this judgment
    "what_went_well": ["str"],       // min 3 short strings, specific strengths tied to the answer
    "what_was_missing": ["str"],     // min 3 short strings, concrete missing elements or weaknesses
    "how_to_improve": ["str"],       // min 3 short action-oriented suggestions (brief)
    "next_focus": "str",             // one concise focus for the candidate's next answer
    "final_verdict": "Not Ready" | "Borderline" | "Ready",
    "verdict_explanation": "str"     // 1-2 sentences explaining the verdict
}}

Be brief but specific in each array entry. Tailor every item to the candidate's answer.
""".format(
                interviewer_persona=_json_context(interviewer_persona),
                focus_area=focus_area or "general depth",
                conversation_history=_json_context(conversation_history[-6:]),
                question=question,
                answer=answer,
        )

    return Task(
        description=description,
        expected_output="Valid JSON with a strict interview evaluation.",
        agent=agent,
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
    conversation_history=None,
    last_score=None,
    current_focus_area="",
):
    weak_areas = weak_areas or []
    resume_context = resume_context or {}
    section_scores = section_scores or {}
    interviewer_persona = interviewer_persona or {}
    coach_memory = coach_memory or {}
    conversation_history = conversation_history or []

    description = """
You are the follow-up interviewer for a realistic AI career coach.
Role: {role}
Difficulty: {difficulty}/10
Training mode: {training_mode}
Adaptive focus mode: {focus_mode}
Domain focus: {domain_focus}
Last score: {last_score}/10
Current focus area: {current_focus_area}

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

RECENT CONVERSATION HISTORY:
{conversation_history}

LAST QUESTION:
{question}

CANDIDATE ANSWER:
{answer}

FOLLOW-UP RULES:
- Generate exactly ONE follow-up interviewer turn.
- Reference something the candidate just said or failed to say when useful.
- If the candidate was vague, interrupt them explicitly and ask for specifics.
- If the candidate was strong, increase depth with tradeoffs, constraints, edge cases, or decision-making.
- Respect training mode and focus mode.
- Use weak areas and coach memory when relevant.
- Do not invent experience not present in the resume context.
- The follow-up should naturally demand a 5-10 line answer.

Return ONLY JSON.

OUTPUT FORMAT:
{{
  "question": "2-4 sentence follow-up interviewer turn with realistic pressure",
  "focus_area": "specific weak area or general competency",
  "focus_type": "weak_area, general, domain, or behavioral",
  "interviewer_signal": "short realistic cue or pressure statement",
  "pressure_level": "low, medium, or high",
  "answer_expectation": "short guidance on how the candidate should answer"
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
        conversation_history=_json_context(conversation_history[-8:]),
        last_score=last_score if last_score is not None else 5,
        current_focus_area=current_focus_area or "general depth",
    )

    return Task(
        description=description,
        expected_output="Valid JSON with a single realistic follow-up interviewer turn.",
        agent=agent,
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
        agent=agent,
    )
