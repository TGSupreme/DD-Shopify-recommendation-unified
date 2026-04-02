from fastapi import APIRouter, HTTPException, Header
from models.schemas import SystemStatsResponse
from services.admin import admin_service
from core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

async def verify_admin(x_admin_token: str = Header(None)):
    if not x_admin_token or x_admin_token != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid Admin Token")

@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(x_admin_token: str = Header(None)):
    """
    GOD VIEW: Global stats across the entire recommendation microservice.
    Requires X-Admin-Token header.
    """
    await verify_admin(x_admin_token)
    
    try:
        stats = await admin_service.get_global_system_stats()
        return SystemStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to fetch global system stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system statistics.")
