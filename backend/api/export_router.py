from fastapi import APIRouter, Depends
from ..api.auth_router import get_current_user
from ..export import export_manager, ExportFormat

router = APIRouter(prefix="/export", tags=["Export"])

@router.get("/formats")
async def list_formats(current_user: dict = Depends(get_current_user)):
    return {"formats": [f.value for f in export_manager.list_formats()]}
