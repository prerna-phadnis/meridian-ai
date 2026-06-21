from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client
from src.services.notes import generate_notes
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


class NotesRequest(BaseModel):
    paper_id: str


@router.post("/notes/generate")
async def generate_notes_endpoint(body: NotesRequest):
    paper_id = body.paper_id

    logger.info(f"Generating notes for paper {paper_id}")

    result = supabase.table("papers") \
        .select("extracted_text, title") \
        .eq("id", paper_id) \
        .single() \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Paper not found")

    extracted_text = result.data.get("extracted_text")
    title = result.data.get("title") or ""

    if not extracted_text:
        raise HTTPException(
            status_code=400,
            detail="Paper has no extracted text yet — has it finished processing?"
        )

    try:
        notes = generate_notes(extracted_text=extracted_text, title=title)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        raise HTTPException(status_code=502, detail="Model returned invalid JSON")
    except Exception as e:
        logger.error(f"Notes generation failed for {paper_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    supabase.table("papers").update({
        "notes": notes
    }).eq("id", paper_id).execute()

    logger.info(f"Notes generated for paper {paper_id} ✅")

    return {"paper_id": paper_id, "notes": notes}