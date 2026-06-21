from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client
from src.services.citations import extract_citations
from dotenv import load_dotenv
import os
import json
import logging

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


class CitationsRequest(BaseModel):
    paper_id: str


@router.post("/notes/citations")
async def extract_citations_endpoint(body: CitationsRequest):
    paper_id = body.paper_id

    logger.info(f"Extracting citations for paper {paper_id}")

    result = supabase.table("papers") \
        .select("extracted_text") \
        .eq("id", paper_id) \
        .single() \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Paper not found")

    extracted_text = result.data.get("extracted_text")

    if not extracted_text:
        raise HTTPException(
            status_code=400,
            detail="Paper has no extracted text yet — has it finished processing?"
        )

    try:
        citations = extract_citations(extracted_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        raise HTTPException(status_code=502, detail="Model returned invalid JSON")
    except Exception as e:
        logger.error(f"Citation extraction failed for {paper_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    supabase.table("papers").update({
        "citations": citations
    }).eq("id", paper_id).execute()

    logger.info(f"Citations extracted for paper {paper_id} ✅")

    return {"paper_id": paper_id, "citations": citations}