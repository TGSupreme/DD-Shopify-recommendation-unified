from fastapi import APIRouter, HTTPException, Request
from typing import List
from models.schemas import SearchRequest, SimilarRequest, SearchResponse, ProductResponse
from services.discovery import product_discovery
from core.config import settings
from utils.limiter import limiter, get_store_only_key
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{store_id}", response_model=SearchResponse)
@limiter.limit(settings.RATE_LIMIT_STOREFRONT, key_func=get_store_only_key)
async def semantic_search(request: Request, store_id: str, search_request: SearchRequest):
    """
    Standardized Semantic Search Entry Point.
    Offloads logic to product_discovery.search_by_text.
    """
    try:
        results = await product_discovery.search_by_text(
            store_id=store_id,
            query_text=search_request.query_text,
            filters=search_request.filters,
            limit=search_request.limit,
            diversity_penalty=search_request.diversity_penalty
        )
        return SearchResponse(status="success", results=results)
    except Exception as e:
        logger.error(f"Search API failed for store {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Search operation failed.")

@router.post("/{store_id}/similar/{product_id}", response_model=SearchResponse)
@limiter.limit(settings.RATE_LIMIT_STOREFRONT, key_func=get_store_only_key)
async def similar_products(request: Request, store_id: str, product_id: str, similar_request: SimilarRequest):
    """
    Standardized Similarity Entry Point.
    Offloads logic to product_discovery.search_by_similarity.
    """
    try:
        results = await product_discovery.search_by_similarity(
            store_id=store_id,
            product_id=product_id,
            filters=similar_request.filters,
            limit=similar_request.limit,
            diversity_penalty=similar_request.diversity_penalty
        )
        if not results and results != []: # Handle product not found
             raise HTTPException(status_code=404, detail="Target product not found.")
             
        return SearchResponse(status="success", results=results)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similarity API failed for {product_id} in {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Similarity search failed.")
