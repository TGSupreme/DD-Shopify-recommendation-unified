from fastapi import APIRouter, HTTPException, Request
from models.schemas import RecommendRequest, ComplementaryRequest, SearchResponse, ProductResponse
from services.qdrant import qdrant_service
from utils.filters import translate_filters
from utils.mmr import calculate_mmr
from core.config import settings
from utils.limiter import limiter, get_store_only_key
from qdrant_client.http import models as q_models
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
        
        apply_diversity = recommend_request.diversity_penalty > 0.0
        fetch_limit = recommend_request.limit or settings.TOP_K
        query_limit = fetch_limit * 5 if apply_diversity else fetch_limit
        
        # 2. Call specialized recommendation service
        hits = await qdrant_service.get_personalized_recommendations(
            store_id=store_id,
            viewed_ids=recommend_request.viewed_ids,
            cart_ids=recommend_request.added_to_cart_ids,
            purchase_ids=recommend_request.purchased_ids,
            query_filter=q_filter,
            limit=query_limit,
            include_vectors=apply_diversity
        )

        # 3. Apply MMR Diversity if requested
        if apply_diversity and hits:
            candidate_ids = [hit.payload.get("product_id") for hit in hits]
            candidate_vectors = [hit.vector for hit in hits]
            candidate_scores = [hit.score for hit in hits]
            
            diverse_results = calculate_mmr(
                candidate_ids=candidate_ids,
                candidate_vectors=candidate_vectors,
                candidate_scores=candidate_scores,
                limit=fetch_limit,
                diversity_penalty=recommend_request.diversity_penalty
            )
            
            results = [ProductResponse(product_id=pid, score=score) for pid, score in diverse_results]
        else:
            # 3. Format standard results
            results = [
                ProductResponse(
                    product_id=hit.payload.get("product_id"),
                    score=hit.score
                )
                for hit in hits
            ][:fetch_limit]

        return SearchResponse(status="success", results=results)

    except Exception as e:
        logger.error(f"Personalized recommendation failed for store {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Recommendation engine failed.")

@router.post("/{store_id}/complementary/{product_id}", response_model=SearchResponse)
@limiter.limit(settings.RATE_LIMIT_STOREFRONT, key_func=get_store_only_key)
async def complementary_recommendations(request: Request, store_id: str, product_id: str, complementary_request: ComplementaryRequest):
    """
    "Complete the Look": Finds products from different categories that complement the target product.
    Uses Qdrant's Grouping API to ensure variety (one item per category).
    """
    try:
        # 1. Retrieve the vector and category for the target product
        target_points = await qdrant_service.get_points_by_ids(store_id, [product_id])
        if not target_points:
            raise HTTPException(status_code=404, detail="Target product not found.")
        
        target_point = target_points[0]
        target_vector = target_point.vector
        target_category = target_point.payload.get("category")

        # 2. Build Filter (Tenant Isolation + Category Exclusion)
        q_filter = translate_filters(store_id, complementary_request.filters)
        
        if not q_filter.must_not:
            q_filter.must_not = []
        
        # Exclude the target product itself
        q_filter.must_not.append(
            q_models.FieldCondition(
                key="product_id",
                match=q_models.MatchValue(value=product_id)
            )
        )
        
        # Exclude the target category if it exists
        if target_category:
            q_filter.must_not.append(
                q_models.FieldCondition(
                    key="category",
                    match=q_models.MatchValue(value=target_category)
                )
            )

        # 3. Determine Search Parameters
        apply_diversity = complementary_request.diversity_penalty > 0.0
        fetch_limit = complementary_request.limit or settings.TOP_K
        query_limit = fetch_limit * 5 if apply_diversity else fetch_limit

        # 4. Execute Grouped Search (One item per category)
        hits = await qdrant_service.search_products(
            collection_name=settings.COLLECTION_NAME,
            query_vector=target_vector,
            query_filter=q_filter,
            limit=query_limit,
            include_vectors=apply_diversity,
            group_by="category", # Key field for "Complete the Look" variety
            group_size=1
        )

        # 5. Apply MMR Diversity if requested
        if apply_diversity and hits:
            candidate_ids = [hit.payload.get("product_id") for hit in hits]
            candidate_vectors = [hit.vector for hit in hits]
            candidate_scores = [hit.score for hit in hits]
            
            diverse_results = calculate_mmr(
                candidate_ids=candidate_ids,
                candidate_vectors=candidate_vectors,
                candidate_scores=candidate_scores,
                limit=fetch_limit,
                diversity_penalty=complementary_request.diversity_penalty
            )
            
            results = [ProductResponse(product_id=pid, score=score) for pid, score in diverse_results]
        else:
            # 5. Format standard results
            results = [
                ProductResponse(
                    product_id=hit.payload.get("product_id"),
                    score=hit.score
                )
                for hit in hits
            ][:fetch_limit]

        return SearchResponse(status="success", results=results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complementary recommendations failed for {product_id} in {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Complementary recommendation engine failed.")
