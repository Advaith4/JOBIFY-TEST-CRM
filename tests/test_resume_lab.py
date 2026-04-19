from src.resume_lab import apply_fix, parse_resume, validate_resume_analysis


def test_parse_resume_extracts_core_sections():
    text = """
Summary
Flutter developer building mobile apps.
Skills
Flutter, Dart, Firebase
Projects
- Worked on chatbot project
Experience
- Responsible for app UI
"""

    parsed = parse_resume(text)

    assert "Flutter" in parsed["skills"]
    assert parsed["projects"] == ["Worked on chatbot project"]
    assert parsed["experience"] == ["Responsible for app UI"]


def test_invalid_analysis_falls_back_to_grounded_issue():
    text = """
Summary
Flutter developer building mobile apps.
Projects
Worked on chatbot project
"""
    parsed = parse_resume(text)

    analysis = validate_resume_analysis({}, text, parsed)
    issues = [issue for section in analysis["sections"] for issue in section["issues"]]

    assert analysis["score"] > 0
    assert issues
    assert all(issue["original"] in text for issue in issues)
    assert all(issue["improved"] for issue in issues)


def test_apply_fix_replaces_exact_text_once():
    current = "Projects\nWorked on chatbot project\nSkills\nFlutter"
    issue = {
        "id": "abc123",
        "section": "projects",
        "original": "Worked on chatbot project",
        "improved": "Developed a chatbot project, clarifying ownership, tools used, and project outcome.",
    }

    result = apply_fix(current, issue, [])

    assert result["applied"] is True
    assert "Worked on chatbot project" not in result["current_resume"]
    assert "Developed a chatbot project" in result["current_resume"]
    assert result["applied_fixes"][0]["issue_id"] == "abc123"
