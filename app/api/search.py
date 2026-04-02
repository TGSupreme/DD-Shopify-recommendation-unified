from fastapi import APIRouter, HTTPException, Request
from typing import List
from models.schemas import SearchRequest, SimilarRequest, SearchResponse, ProductResponse
from services.embedding import embedding_service
from services.qdrant import qdrant_service
from utils.filters import translate_filters
from utils.mmr import calculate_mmr
from core.config import settings
from utils.limiter import limiter, get_store_only_key
import logging
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{store_id}", response_model=SearchResponse)
@limiter.limit(settings.RATE_LIMIT_STOREFRONT, key_func=get_store_only_key)
async def semantic_search(request: Request, store_id: str, search_request: SearchRequest):
    """
    Executes a semantic search based on query text and optional filters.
    """
    if not search_request.query_text:
        return SearchResponse(status="success", results=[])

    try:
        # 1. Vectorize query text
        query_vectors = await embedding_service.get_embeddings([search_request.query_text])
        query_vector = query_vectors[0]

        # 2. Translate filters (including mandatory store_id)
        q_filter = translate_filters(store_id, search_request.filters)

        # Determine if we need diversity re-ranking
        apply_diversity = search_request.diversity_penalty > 0.0
        fetch_limit = search_request.limit or settings.TOP_K
        query_limit = fetch_limit * 5 if apply_diversity else fetch_limit

        # 3. Search in Qdrant
        hits = await qdrant_service.search_products(
            collection_name=settings.COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=q_filter,
            limit=query_limit,
            include_vectors=apply_diversity
        )

        # 4. Apply MMR Diversity if requested
        if apply_diversity and hits:
            candidate_ids = [hit.payload.get("product_id") for hit in hits]
            candidate_vectors = [hit.vector for hit in hits]
            candidate_scores = [hit.score for hit in hits]
            
            diverse_results = calculate_mmr(
                candidate_ids=candidate_ids,
                candidate_vectors=candidate_vectors,
                candidate_scores=candidate_scores,
                limit=fetch_limit,
                diversity_penalty=search_request.diversity_penalty
            )
            
            results = [ProductResponse(product_id=pid, score=score) for pid, score in diverse_results]
        else:
            # 4. Format standard results
            results = [
                ProductResponse(
                    product_id=hit.payload.get("product_id"),
                    score=hit.score
                )
                for hit in hits
            ][:fetch_limit]

        return SearchResponse(status="success", results=results)

    except Exception as e:
        logger.error(f"Semantic search failed for store {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Search operation failed.")

@router.post("/{store_id}/similar/{product_id}", response_model=SearchResponse)
@limiter.limit(settings.RATE_LIMIT_STOREFRONT, key_func=get_store_only_key)
async def similar_products(request: Request, store_id: str, product_id: str, similar_request: SimilarRequest):
    """
    Finds products similar to a specific product_id.
    """
    try:
        # 1. Retrieve the vector for the target product
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{store_id}_{product_id}"))
        
        target_points = await qdrant_service.client.retrieve(
            collection_name=settings.COLLECTION_NAME,
            ids=[point_id],
            with_vectors=True
        )

        if not target_points:
            raise HTTPException(status_code=404, detail="Target product not found in index.")

        target_vector = target_points[0].vector

        # 2. Translate filters
        q_filter = translate_filters(store_id, similar_request.filters)

        # Determine limits
        apply_diversity = similar_request.diversity_penalty > 0.0
        fetch_limit = similar_request.limit or settings.TOP_K
        query_limit = (fetch_limit * 5) + 1 if apply_diversity else fetch_limit + 1

        # 3. Search using product vector
        hits = await qdrant_service.search_products(
            collection_name=settings.COLLECTION_NAME,
            query_vector=target_vector,
            query_filter=q_filter,
            limit=query_limit,
            include_vectors=apply_diversity
        )

        # Filter out self
        filtered_hits = [hit for hit in hits if hit.payload.get("product_id") != product_id]

        # 4. Apply MMR Diversity if requested
        if apply_diversity and filtered_hits:
            candidate_ids = [hit.payload.get("product_id") for hit in filtered_hits]
            candidate_vectors = [hit.vector for hit in filtered_hits]
            candidate_scores = [hit.score for hit in filtered_hits]
            
            diverse_results = calculate_mmr(
                candidate_ids=candidate_ids,
                candidate_vectors=candidate_vectors,
                candidate_scores=candidate_scores,
                limit=fetch_limit,
                diversity_penalty=similar_request.diversity_penalty
            )
            
            results = [ProductResponse(product_id=pid, score=score) for pid, score in diverse_results]
        else:
            # 4. Format standard results
            results = [
                ProductResponse(
                    product_id=hit.payload.get("product_id"),
                    score=hit.score
                )
                for hit in filtered_hits
            ][:fetch_limit]

        return SearchResponse(status="success", results=results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similar products search failed for {product_id} in {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Similarity search failed.")
