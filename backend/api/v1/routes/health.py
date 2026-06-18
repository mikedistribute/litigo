from fastapi import APIRouter

from config import GEMINI_MODEL, GOOGLE_API_KEY


router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
  return {
    "status": "ok",
    "app": "Litigo API",
    "version": "1.0.0",
    "gemini_configured": bool((GOOGLE_API_KEY or "").strip()),
    "model": GEMINI_MODEL,
  }
