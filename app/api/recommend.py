from fastapi import APIRouter, HTTPException, Request
from models.schemas import RecommendRequest, ComplementaryRequest, SearchResponse, ProductResponse
from services.recommender import product_recommender
from services.discovery import product_discovery
from core.config import settings
from utils.limiter import limiter, get_store_only_key
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{store_id}", response_model=SearchResponse)
@limiter.limit(settings.RATE_LIMIT_STOREFRONT, key_func=get_store_only_key)
async def get_personalized_recommendations(request: Request, store_id: str, recommend_request: RecommendRequest):
    """
    Standardized Personalization Entry Point.
    Offloads logic to product_recommender.
    """
    try:
        results = await product_recommender.get_personalized_recommendations(
            store_id=store_id,
            viewed_ids=recommend_request.viewed_ids,
            cart_ids=recommend_request.added_to_cart_ids,
            purchase_ids=recommend_request.purchased_ids,
            filters=recommend_request.filters,
            limit=recommend_request.limit,
            diversity_penalty=recommend_request.diversity_penalty
        )
        return SearchResponse(status="success", results=results)
    except Exception as e:
        logger.error(f"Personalized recommendation failed for store {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Recommendation engine failed.")

@router.post("/{store_id}/complementary/{product_id}", response_model=SearchResponse)
@limiter.limit(settings.RATE_LIMIT_STOREFRONT, key_func=get_store_only_key)
async def complementary_recommendations(request: Request, store_id: str, product_id: str, complementary_request: ComplementaryRequest):
    """
    "Complete the Look": Finds products from different categories that complement the target product.
    Offloads logic to product_discovery.get_complementary_products.
    """
    try:
        results = await product_discovery.get_complementary_products(
            store_id=store_id,
            product_id=product_id,
            filters=complementary_request.filters,
            limit=complementary_request.limit,
            diversity_penalty=complementary_request.diversity_penalty
        )
        if not results and results != []: # Handle product not found
             raise HTTPException(status_code=404, detail="Target product not found.")
             
        return SearchResponse(status="success", results=results)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complementary recommendations failed for {product_id} in {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Complementary recommendation engine failed.")
