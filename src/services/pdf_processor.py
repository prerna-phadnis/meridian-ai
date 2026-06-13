# src/services/pdf_processor.py
# Reads PDF and splits into chunks

import fitz  # PyMuPDF
import re
from typing import List


def extract_text_from_bytes(pdf_bytes: bytes) -> dict:
    """
    Takes PDF as raw bytes
    Returns full text + per page text + metadata
    """

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    pages = []
    full_text_parts = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()

        if text:  # skip empty pages
            pages.append({
                "page_number": page_num + 1,
                "text": text
            })
            full_text_parts.append(text)

    metadata = doc.metadata or {}
    full_text = "\n\n".join(full_text_parts)

    page_count = len(doc)
    doc.close()

    return {
        "full_text": full_text,
        "pages": pages,
        "page_count": page_count,
        "metadata": metadata
    }


def chunk_text(pages: list, chunk_size: int = 500) -> List[dict]:
    """
    Splits pages into smaller chunks.

    Why chunk?

    -> LLMs have token limits
    -> Smaller chunks = more precise search results
    -> We find the exact paragraph that answers
       the question, not the whole paper

    chunk_size = roughly how many words per chunk
    """

    chunks = []
    chunk_index = 0

    for page in pages:
        page_num = page["page_number"]
        text = page["text"]

        # Split page into paragraphs
        paragraphs = [
            p.strip()
            for p in re.split(r"\n\s*\n", text)
            if p.strip()
        ]

        current_chunk = ""
        current_word_count = 0

        for para in paragraphs:
            para_words = len(para.split())

            # If adding this paragraph exceeds chunk size,
            # save current chunk and start new one
            if current_word_count + para_words > chunk_size and current_chunk:

                chunks.append({
                    "index": chunk_index,
                    "text": current_chunk.strip(),
                    "page_number": page_num,
                    "word_count": current_word_count
                })

                chunk_index += 1

                # Start new chunk with overlap
                # Keep last paragraph for context continuity
                current_chunk = para + "\n\n"
                current_word_count = para_words

            else:
                current_chunk += para + "\n\n"
                current_word_count += para_words

        # Save remaining text as last chunk for this page
        if current_chunk.strip():
            chunks.append({
                "index": chunk_index,
                "text": current_chunk.strip(),
                "page_number": page_num,
                "word_count": current_word_count
            })

            chunk_index += 1

    return chunks