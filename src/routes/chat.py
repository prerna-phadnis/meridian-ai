from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.middleware.auth import get_current_user
from src.services.rag import answer_question

import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    question: str
    paper_id: str


@router.post("/chat")
async def chat(
    body: ChatRequest,
    current_user=Depends(get_current_user)
):
    """
    Takes a question + paper_id
    Returns answer + source chunks
    """

    if not body.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    if not body.paper_id:
        raise HTTPException(
            status_code=400,
            detail="paper_id is required"
        )

    logger.info(
        f"Chat request - paper: {body.paper_id}, "
        f"question: {body.question[:50]}"
    )

    result = answer_question(
        question=body.question,
        paper_id=body.paper_id
    )

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "paper_id": body.paper_id
    }