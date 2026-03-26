from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def search_health():
    return {"status": "Search router is active"}
