from fastapi import APIRouter, HTTPException, Request, Query, Header
from typing import List
from models.schemas import ProductUpsert, SyncResponse, StoreStatsResponse, DebugRequest
from services.indexer import product_indexer
from services.admin import admin_service
from core.config import settings
from utils.limiter import limiter, get_store_only_key
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

async def verify_admin(x_admin_token: str):
    if not x_admin_token or x_admin_token != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid Admin Token")

@router.post("/{store_id}/products", response_model=SyncResponse)
@limiter.limit(settings.RATE_LIMIT_SYNC, key_func=get_store_only_key)
async def sync_products(request: Request, store_id: str, products: List[ProductUpsert]):
    """
    Standardized Ingestion Entry Point.
    Offloads logic to product_indexer.ingest_products.
    """
    try:
        count = await product_indexer.ingest_products(store_id, products)
        return SyncResponse(
            status="success", 
            message=f"Successfully synced {count} products", 
            count=count
        )
    except Exception as e:
        logger.error(f"Sync API failed for store {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Data synchronization failed.")

@router.delete("/{store_id}/products/{product_id}", response_model=SyncResponse)
@limiter.limit(settings.RATE_LIMIT_SYNC, key_func=get_store_only_key)
async def delete_product(request: Request, store_id: str, product_id: str):
    """
    Standardized Deletion Entry Point.
    Offloads logic to product_indexer.delete_product.
    """
    try:
        await product_indexer.delete_product(store_id, product_id)
        return SyncResponse(status="success", message=f"Product {product_id} deleted")
    except Exception as e:
        logger.error(f"Deletion API failed for {product_id} in {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Product deletion failed.")

@router.post("/{store_id}/debug")
async def get_raw_products(store_id: str, debug_request: DebugRequest):
    """
    DEVELOPMENT ONLY: Fetches raw stored points via admin_service.
    """
    try:
        if not debug_request.product_ids:
            raise HTTPException(status_code=400, detail="At least one product_id is required.")

        results = await admin_service.get_debug_points(store_id, debug_request.product_ids)
        if not results:
            raise HTTPException(status_code=404, detail="No products found in Qdrant.")
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Debug API failed for {debug_request.product_ids}: {str(e)}")
        raise HTTPException(status_code=500, detail="Debug fetch failed.")

@router.get("/{store_id}/stats", response_model=StoreStatsResponse)
async def get_store_stats(store_id: str):
    """
    Returns high-level statistics for a specific store.
    """
    try:
        stats = await admin_service.get_store_stats(store_id)
        return StoreStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Stats API failed for {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve store statistics.")

@router.delete("/{store_id}/delete-store", response_model=SyncResponse)
@limiter.limit(settings.RATE_LIMIT_SYNC, key_func=get_store_only_key)
async def delete_store(request: Request, store_id: str, x_admin_token: str = Header(None)):
    """
    Securely removes all data for a specific store.
    Requires X-Admin-Token for security.
    """
    await verify_admin(x_admin_token)
    
    try:
        await product_indexer.delete_store(store_id)
        return SyncResponse(
            status="success", 
            message=f"Store '{store_id}' data has been completely removed."
        )
    except Exception as e:
        logger.error(f"Store deletion failed for {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete store data.")
