from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def sync_health():
    return {"status": "Sync router is active"}
