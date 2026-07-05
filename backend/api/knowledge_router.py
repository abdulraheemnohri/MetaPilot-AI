from fastapi import APIRouter, Depends, UploadFile, File
from ..api.auth_router import get_current_user
from ..orchestrator import orchestrator

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    return await orchestrator.knowledge.get_statistics()

@router.post("/upload")
async def upload_doc(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    # Placeholder for actual upload and indexing
    return {"success": True, "filename": file.filename}
