import fitz  # PyMuPDF - reads PDFs
from supabase import create_client
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Supabase client for this service
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


async def process_paper(paper_id: str, file_path: str, user_id: str):
    """
    Main processing function.
    Called in background after PDF upload.

    For now:
    1. Download PDF from Supabase Storage
    2. Extract text
    3. Update paper status + save extracted text

    Later we'll add:
    4. Chunk text
    5. Generate embeddings
    6. Store in vector DB
    """

    logger.info(f"Starting processing for paper: {paper_id}")

    try:
        # Step 1: Update status to 'processing'
        supabase.table("papers").update({
            "status": "processing"
        }).eq("id", paper_id).execute()

        # Step 2: Download PDF from Supabase Storage
        logger.info(f"Downloading PDF: {file_path}")

        file_response = (
            supabase.storage
            .from_("papers")
            .download(file_path)
        )

        if not file_response:
            raise Exception("Failed to download PDF from storage")

        # Step 3: Extract text from PDF
        logger.info("Extracting text from PDF")

        extracted = extract_text_from_pdf(file_response)

        full_text = extracted["full_text"]
        page_count = extracted["page_count"]
        metadata = extracted["metadata"]

        logger.info(
            f"Extracted {len(full_text)} chars from {page_count} pages"
        )

        # Step 4: Try to get title from PDF metadata
        # PDFs often have title in metadata
        # Better than using filename

        pdf_title = metadata.get("title", "").strip()

        # Step 5: Save extracted text + update status

        update_data = {
            "status": "ready",
            "page_count": page_count,
            "extracted_text": full_text[:50000]  # store first 50k chars
        }

        # Only update title if PDF has one
        if pdf_title:
            update_data["title"] = pdf_title

        supabase.table("papers").update(
            update_data
        ).eq("id", paper_id).execute()

        logger.info(f"Paper {paper_id} processing complete ✅")

    except Exception as e:
        logger.error(f"Processing failed for {paper_id}: {str(e)}")

        # Update status to failed so user knows something went wrong
        supabase.table("papers").update({
            "status": "failed",
            "error_message": str(e)
        }).eq("id", paper_id).execute()


def extract_text_from_pdf(pdf_bytes: bytes) -> dict:
    """
    Takes PDF as bytes
    Returns extracted text per page + metadata
    """

    import io

    # Open PDF from bytes (no file needed)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    pages = []
    full_text_parts = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        pages.append({
            "page_number": page_num + 1,
            "text": text,
            "char_count": len(text)
        })

        full_text_parts.append(text)

    full_text = "\n".join(full_text_parts)

    # Get PDF metadata (title, author etc)
    metadata = doc.metadata or {}

    doc.close()

    return {
        "full_text": full_text,
        "pages": pages,
        "page_count": len(pages),
        "metadata": metadata,
        "total_chars": len(full_text)
    }
