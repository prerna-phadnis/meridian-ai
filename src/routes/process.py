from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from src.services.pdf_processor import process_paper
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Shape of data Node sends us
class ProcessRequest(BaseModel):
    paper_id: str
    file_path: str
    user_id: str


@router.post("/process")
async def trigger_processing(
    body: ProcessRequest,
    background_tasks: BackgroundTasks
):
    """
    Node calls this after PDF is uploaded.
    We start processing in the background
    so Node gets an instant response back.
    """

    # Add to background tasks
    # Returns 200 immediately, processes after
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