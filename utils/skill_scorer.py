import re
from collections import Counter

TECH_KEYWORDS = {
    "python", "java", "javascript", "react", "node", "flutter", "aws", 
    "docker", "kubernetes", "sql", "machine learning", "data science", 
    "c++", "c#", "ruby", "php", "django", "fastapi", "spring", "android", "ios", "firebase"
}

def extract_keywords(text):
    text = text.lower()
    found = {}
    for skill in TECH_KEYWORDS:
        count = len(re.findall(rf"\b{re.escape(skill)}\b", text))
        if count > 0:
            found[skill] = count
    return Counter(found)

def normalize_text(text):
    return text.lower()

def compute_match_score(resume_text, required_skills):
    """
    Dynamically scores a resume against a list of required skills.
    No hardcoded whitelists.
    """
    resume_text = normalize_text(resume_text)
    
    matched_keywords = []
    missing_keywords = []
    
    # If the LLM failed to provide skills, provide a default graceful score
    if not required_skills:
        return {
            "score": 0,
            "matched_keywords": [],
            "missing_keywords": []
        }
        
    for skill in required_skills:
        clean_skill = normalize_text(skill)
        # Check if the skill exists as a word or phrase in the resume
        if clean_skill in resume_text:
            matched_keywords.append(skill)
        else:
            missing_keywords.append(skill)
            
    total = len(required_skills)
    score = int((len(matched_keywords) / total) * 100)
    
    return {
        "score": score,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
    }

def get_priority(score):
    if score >= 85:
        return "🔥 HIGH APPLY (Strong Fit)"
    elif score >= 70:
        return "⚡ APPLY (Good Fit)"
    elif score >= 50:
        return "🧠 PREPARE & APPLY"
    elif score >= 30:
        return "📚 UPSKILL BEFORE APPLYING"
    else:
        return "❌ LOW MATCH"

def generate_action_plan(score, missing_skills):
    if score >= 80:
        return "Focus on applying immediately and preparing for interviews."

    if not missing_skills:
        return "Strengthen your core concepts and apply confidently."

    top_skills = missing_skills[:3]
    return (
        f"Learn and practice: {', '.join(top_skills)}. "
        "Build at least 1 strong project and reapply."
    )