from src.lib.gemini import generate_text
from dotenv import load_dotenv
import json
import logging

load_dotenv()

logger = logging.getLogger(__name__)


def generate_notes(extracted_text: str, title: str = "") -> dict:
    """
    Takes full paper text
    Returns structured notes as JSON using Gemini
    """

    logger.info(f"Generating notes for: {title}")

    # Smart truncation
    # First 7000 chars = abstract + intro
    # Last 3000 chars = conclusion
    if len(extracted_text) > 12000:
        first_part = extracted_text[:7000]
        last_part = extracted_text[-3000:]
        text_to_analyze = first_part + "\n\n...\n\n" + last_part
    else:
        text_to_analyze = extracted_text

    prompt = f"""You are an expert research analyst.
Analyze this research paper and extract structured information.

Paper Title: {title or "Unknown"}

Paper Text:
{text_to_analyze}

Return a JSON object with EXACTLY these keys:
{{
  "main_claim": "One sentence: what is the core argument or contribution",
  "problem_solved": "What problem or gap does this paper address",
  "methodology": "How did they conduct the research",
  "key_findings": [
    "Finding 1",
    "Finding 2",
    "Finding 3",
    "Finding 4",
    "Finding 5"
  ],
  "limitations": [
    "Limitation 1",
    "Limitation 2"
  ],
  "future_work": "What future research directions do authors suggest",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "one_line_summary": "Explain this paper to a non-expert in one sentence"
}}

Rules:
- Be specific, not vague
- Use simple clear language
- If information not found use "Not mentioned in paper"
- key_findings must be array of strings
- keywords must be array of strings
- limitations must be array of strings
"""

    logger.info("Calling Gemini for notes...")

    raw = generate_text(
        prompt=prompt,
        temperature=0.2,
        max_tokens=2000,
        json_mode=True
    )

    logger.info("Notes received from Gemini ✅")
    logger.debug(f"Raw response: {raw[:200]}")

    notes = json.loads(raw)

    # Ensure arrays exist and are correct type
    if not isinstance(notes.get("key_findings"), list):
        notes["key_findings"] = [str(notes.get("key_findings", "Not found"))]

    if not isinstance(notes.get("keywords"), list):
        notes["keywords"] = []

    if not isinstance(notes.get("limitations"), list):
        notes["limitations"] = [str(notes.get("limitations", "Not mentioned"))]

    return notes