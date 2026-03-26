from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def recommend_health():
    return {"status": "Recommend router is active"}
