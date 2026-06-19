from src.lib.gemini import generate_text
from dotenv import load_dotenv
import json
import re
import logging

load_dotenv()

logger = logging.getLogger(__name__)


def extract_citations(extracted_text: str) -> list:
    """
    Finds references section
    Parses each citation into structured data
    """

    logger.info("Extracting citations...")

    references_text = find_references_section(extracted_text)

    if not references_text:
        logger.warning("No references section found")
        return []

    logger.info(f"Found references ({len(references_text)} chars)")

    citations = parse_citations_with_gemini(references_text)

    logger.info(f"Extracted {len(citations)} citations ✅")

    return citations


def find_references_section(text: str) -> str:
    """
    Tries multiple patterns to find references section
    """

    patterns = [
        r'(?:^|\n)\s*(?:References|REFERENCES)\s*\n(.*?)(?:\Z)',
        r'(?:^|\n)\s*(?:Bibliography|BIBLIOGRAPHY)\s*\n(.*?)(?:\Z)',
        r'(?:^|\n)\s*(?:Works Cited|WORKS CITED)\s*\n(.*?)(?:\Z)',
        r'(?:^|\n)\s*(?:Literature Cited)\s*\n(.*?)(?:\Z)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            # Max 6000 chars of references
            return match.group(1)[:6000].strip()

    # Fallback: last section of paper
    logger.info("Using fallback: last 3000 chars")
    return text[-3000:].strip()


def parse_citations_with_gemini(references_text: str) -> list:
    """
    Uses Gemini to parse raw reference text
    into structured citation objects
    """

    prompt = f"""Parse these academic references into structured JSON.

References:
{references_text}

Return a JSON object with a "citations" array.

Each item must have:
{{
  "citations": [
    {{
      "index": 1,
      "title": "Full paper or book title",
      "authors": ["Author One", "Author Two"],
      "year": "2023",
      "venue": "Journal, conference, or publisher name",
      "doi": "doi string or null",
      "url": "url string or null"
    }}
  ]
}}

Rules:
- Extract every reference you find
- authors must always be an array of strings
- year must be a string
- Use null for missing doi or url
- index starts at 1
- Clean up formatting artifacts like extra spaces
"""

    logger.info("Calling Gemini for citations...")

    raw = generate_text(
        prompt=prompt,
        temperature=0.1,
        max_tokens=4000,
        json_mode=True
    )

    logger.info("Citations received from Gemini ✅")

    data = json.loads(raw)
    citations = data.get("citations", [])

    # Clean up each citation
    cleaned = []

    for c in citations:

        # Ensure authors is always a list
        if not isinstance(c.get("authors"), list):
            authors = c.get("authors")
            c["authors"] = [authors] if authors else []

        # Ensure index exists
        if "index" not in c:
            c["index"] = len(cleaned) + 1

        cleaned.append(c)

    return cleaned