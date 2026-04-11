import pypdf
import re

def extract_text_from_pdf(pdf_path):
    """
    Extracts raw text from a PDF file.
    """
    try:
        text = ""
        with open(pdf_path, "rb") as file:
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                raw_text = page.extract_text()
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

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    # Remove weird characters
    text = re.sub(r"[^\x00-\x7F]+", " ", text)

    # Normalize spacing
    text = text.strip()

    return text


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