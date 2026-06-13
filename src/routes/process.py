# src/routes/process.py
# Updated to include chunking + embeddings + vector storage

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from supabase import create_client
from src.services.pdf_processor import extract_text_from_bytes, chunk_text
from src.services.embeddings import generate_embeddings_batch
from src.services.vector_store import store_chunks, delete_paper_chunks
from dotenv import load_dotenv

import os
import logging

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


class ProcessRequest(BaseModel):
    paper_id: str
    file_path: str
    user_id: str


@router.post("/process")
async def trigger_processing(
    body: ProcessRequest,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(
        process_paper,
        paper_id=body.paper_id,
        file_path=body.file_path,
        user_id=body.user_id
    )

    return {
        "message": "Processing started",
        "paper_id": body.paper_id
    }


async def process_paper(paper_id: str, file_path: str, user_id: str):
    """
    Full processing pipeline:
    1. Download PDF
    2. Extract text
    3. Chunk text
    4. Generate embeddings
    5. Store in Qdrant
    6. Update DB status
    """

    logger.info(f"Processing paper {paper_id}")

    try:
        supabase.table("papers").update({
            "status": "processing"
        }).eq("id", paper_id).execute()

        logger.info("Downloading PDF...")
        pdf_bytes = supabase.storage \
            .from_("papers") \
            .download(file_path)

        if not pdf_bytes:
            raise Exception("Failed to download PDF")

        logger.info("Extracting text...")
        extracted = extract_text_from_bytes(pdf_bytes)

        pages = extracted["pages"]
        full_text = extracted["full_text"]
        page_count = extracted["page_count"]
        metadata = extracted["metadata"]

        logger.info(f"Extracted {len(full_text)} chars, {page_count} pages")

        logger.info("Chunking text...")
        chunks = chunk_text(pages, chunk_size=500)
        logger.info(f"Created {len(chunks)} chunks")

        logger.info("Generating embeddings...")
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = generate_embeddings_batch(chunk_texts)
        logger.info(f"Generated {len(embeddings)} embeddings")

        logger.info("Storing in vector DB...")
        store_chunks(
            paper_id=paper_id,
            user_id=user_id,
            chunks=chunks,
            embeddings=embeddings
        )

        pdf_title = (metadata.get("title") or "").strip()

        update_data = {
            "status": "ready",
            "page_count": page_count,
            "extracted_text": full_text[:50000],
            "chunk_count": len(chunks)
        }

        if pdf_title:
            update_data["title"] = pdf_title

        supabase.table("papers").update(
            update_data
        ).eq("id", paper_id).execute()

        logger.info(f"Paper {paper_id} ready ✅")

    except Exception as e:
        logger.error(f"Processing failed for {paper_id}: {str(e)}")

        supabase.table("papers").update({
            "status": "failed",
            "error_message": str(e)
        }).eq("id", paper_id).execute()