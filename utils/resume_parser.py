import re

import pypdf

from src.resume_lab import clean_resume_text


def extract_text_from_pdf(pdf_path):
    """
    Extracts raw text from a PDF file.
    """
    try:
        text = ""
        with open(pdf_path, "rb") as file:
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                raw_text = _extract_best_page_text(page)
                if raw_text:
                    text += raw_text + "\n"

        if not text.strip():
            raise ValueError("Empty text extracted from PDF.")

        return clean_text(text)

    except Exception as e:
        print(f"❌ Error extracting PDF text: {e}")
        return ""


def clean_text(text):
    """
    Cleans extracted text for better LLM processing.
    """
    return clean_resume_text(text)


def _extract_best_page_text(page) -> str:
    layout_text = ""
    plain_text = ""

    try:
        layout_text = page.extract_text(extraction_mode="layout") or ""
    except Exception:
        layout_text = ""

    try:
        plain_text = page.extract_text(extraction_mode="plain") or page.extract_text() or ""
    except Exception:
        plain_text = ""

    candidates = [candidate for candidate in (layout_text, plain_text) if candidate and candidate.strip()]
    if not candidates:
        return ""

    return max(candidates, key=_page_text_quality_score)


def _page_text_quality_score(text: str) -> float:
    spaces = text.count(" ")
    words = len(text.split())
    long_runs = len(re.findall(r"[A-Za-z]{18,}", text))
    glued_camel = len(re.findall(r"[a-z]{4,}[A-Z][a-z]{4,}", text))
    single_char_tokens = len(re.findall(r"\b[A-Za-z0-9]\b", text))
    character_spaced_sequences = len(
        re.findall(r"(?:\b[A-Za-z0-9&/(),.;:+-]\b\s+){6,}\b[A-Za-z0-9&/(),.;:+-]\b", text)
    )
    return (
        spaces
        + words * 0.5
        - long_runs * 12
        - glued_camel * 8
        - single_char_tokens * 2.5
        - character_spaced_sequences * 40
    )


def preview_text(text, length=500):
    """
    Returns a preview of extracted text (for debugging)
    """
    return text[:length] + "..." if len(text) > length else text


def validate_resume_text(text):
    """
    Basic validation to check if resume content looks valid
    """

    if not text or len(text) < 100:
        return False, "Resume content too short or unreadable."

    keywords = ["experience", "skills", "project", "education"]

    matches = sum(1 for word in keywords if word in text.lower())

    if matches < 2:
        return False, "Resume content seems incomplete or poorly extracted."

    return True, "Resume looks valid."
