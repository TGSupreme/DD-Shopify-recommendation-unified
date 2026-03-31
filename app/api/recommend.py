from fastapi import APIRouter, HTTPException, Request
from models.schemas import RecommendRequest, SearchResponse, ProductResponse
from services.qdrant import qdrant_service
from utils.filters import translate_filters
from core.config import settings
from utils.limiter import limiter, get_store_only_key
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{store_id}", response_model=SearchResponse)
@limiter.limit(settings.RATE_LIMIT_STOREFRONT, key_func=get_store_only_key)
async def get_recommendations(request: Request, store_id: str, recommend_request: RecommendRequest):
    """
    Thin wrapper for the Personalization Engine.
    All business logic resides in QdrantService.get_personalized_recommendations.
    """
    try:
        # 1. Translate filters
        q_filter = translate_filters(store_id, recommend_request.filters)
        
        # 2. Call specialized recommendation service
        hits = await qdrant_service.get_personalized_recommendations(
            store_id=store_id,
            viewed_ids=recommend_request.viewed_ids,
            cart_ids=recommend_request.added_to_cart_ids,
            purchase_ids=recommend_request.purchased_ids,
            query_filter=q_filter,
            limit=recommend_request.limit or settings.TOP_K
        )

        # 3. Format results
        results = [
            ProductResponse(
                product_id=hit.payload.get("product_id"),
                score=hit.score
            )
            for hit in hits
        ]

        return SearchResponse(status="success", results=results)

    except Exception as e:
        logger.error(f"Personalized recommendation failed for store {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Recommendation engine failed.")
