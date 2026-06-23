from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.middleware.auth import get_current_user
from src.services.vector_store import delete_paper_chunks
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class DeleteRequest(BaseModel):
    paper_id: str


@router.delete("/vectors/{paper_id}")
async def delete_vectors(
    paper_id: str,
    current_user=Depends(get_current_user)
):
    """
    Deletes all vectors for a paper from Qdrant
    Called by meridian-api when user deletes a paper
    """
    try:
        logger.info(f"Deleting vectors for paper: {paper_id}")

        delete_paper_chunks(paper_id)

        logger.info(f"Vectors deleted ✅ paper: {paper_id}")

        return {
            "message": "Vectors deleted successfully",
            "paper_id": paper_id
        }

    except Exception as e:
        logger.error(f"Failed to delete vectors: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete vectors: {str(e)}"
        )