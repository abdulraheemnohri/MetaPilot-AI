"""
Models Router for MetaPilot AI
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..api.auth_router import get_current_user
from ..utils.model_downloader import model_downloader
from ..local_ai import local_ai_manager

router = APIRouter(prefix="/models", tags=["Models"])

class DownloadRequest(BaseModel):
    repo_id: str
    filename: str

@router.get("/")
async def list_models(current_user: dict = Depends(get_current_user)):
    return local_ai_manager.list_models()

@router.post("/download")
async def download_model(request: DownloadRequest, current_user: dict = Depends(get_current_user)):
    try:
        path = await model_downloader.download_gguf(request.repo_id, request.filename)
        # Rescan models
        local_ai_manager._scan_models()
        return {"success": True, "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
