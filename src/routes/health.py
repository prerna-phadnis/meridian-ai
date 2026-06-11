from fastapi import APIRouter, Depends
from src.middleware.auth import get_current_user

router = APIRouter()

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "meridian-ai"
    }

@router.get("/health/protected")
async def protected_health(user = Depends(get_current_user)):
    return {
        "status": "ok",
        "message": f"Hello {user.email}"
    }