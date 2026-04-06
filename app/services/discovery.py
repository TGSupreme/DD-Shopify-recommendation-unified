import logging
import uuid
import time
from typing import List, Dict, Any, Optional
from qdrant_client.http import models as q_models
from services.qdrant_base import QdrantBaseService
from services.embedding import embedding_service
from services.reranker import reranker_service
from utils.filters import translate_filters
from utils.mmr import calculate_mmr
from core.config import settings

logger = logging.getLogger(__name__)

class DiscoveryService(QdrantBaseService):
    """
    Handles all read-based discovery: Semantic Search, Similarity, and Complementary.
    Enforces variety and diversity re-ranking (MMR).
    """

    async def search_by_text(
        self, 
        store_id: str, 
        query_text: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        diversity_penalty: float = 0.0,
        rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """Executes semantic search from a text query."""
        # 1. Internal Vectorization (Track Latency)
        start_time = time.time()
        query_vectors = await embedding_service.get_embeddings([query_text])
        embed_ms = (time.time() - start_time) * 1000
        query_vector = query_vectors[0]

        # 2. Filter Translation
        q_filter = translate_filters(store_id, filters)

        # 3. Search & Re-rank
        return await self._execute_search_pipeline(
            query_vector=query_vector,
            q_filter=q_filter,
            limit=limit,
            diversity_penalty=diversity_penalty,
            query_text=query_text if rerank else None,
            embed_ms=embed_ms
        )

    async def search_by_similarity(
        self,
        store_id: str,
        product_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        diversity_penalty: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Finds items similar to a specific product_id."""
        # 1. Retrieve Target Vector
        target_points = await self.get_points_by_ids(store_id, [product_id])
        if not target_points:
            return []
        
        target_vector = target_points[0].vector
        q_filter = translate_filters(store_id, filters)

        # 2. Exclude Self
        if not q_filter.must_not: q_filter.must_not = []
        q_filter.must_not.append(q_models.FieldCondition(key="product_id", match=q_models.MatchValue(value=product_id)))

        return await self._execute_search_pipeline(
            query_vector=target_vector,
            q_filter=q_filter,
            limit=limit,
            diversity_penalty=diversity_penalty
        )

    async def get_complementary_products(
        self,
        store_id: str,
        product_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        diversity_penalty: float = 0.0
    ) -> List[Dict[str, Any]]:
        """'Complete the Look' - returns one item per complementary category."""
        target_points = await self.get_points_by_ids(store_id, [product_id])
        if not target_points: return []
        
        target_point = target_points[0]
        target_vector = target_point.vector
        target_category = target_point.payload.get("category")

        q_filter = translate_filters(store_id, filters)
        if not q_filter.must_not: q_filter.must_not = []
        
        # Exclude Self & Category
        q_filter.must_not.append(q_models.FieldCondition(key="product_id", match=q_models.MatchValue(value=product_id)))
        if target_category:
            q_filter.must_not.append(q_models.FieldCondition(key="category", match=q_models.MatchValue(value=target_category)))

        return await self._execute_search_pipeline(
            query_vector=target_vector,
            q_filter=q_filter,
            limit=limit,
            diversity_penalty=diversity_penalty,
            group_by="category" # Ensure variety
        )

    async def _execute_search_pipeline(
        self, 
        query_vector: List[float], 
        q_filter: q_models.Filter, 
        limit: int, 
        diversity_penalty: float,
        group_by: Optional[str] = None,
        query_text: Optional[str] = None,
        embed_ms: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Unified internal pipeline for search, grouping, and MMR."""
        apply_diversity = diversity_penalty > 0.0
        apply_reranker = query_text is not None

        fetch_limit = limit or settings.TOP_K
        
        if apply_reranker:
            query_limit = 50 # Stage 1 net for reranker
        elif apply_diversity:
            query_limit = fetch_limit * 5
        else:
            query_limit = fetch_limit

        # Need vectors if we are going to do diversity on reranked hits, 
        # or if apply_diversity is true
        with_vectors = apply_diversity or apply_reranker

        # Stage 1: Fast Retrieval (Track Latency)
        start_qdrant = time.time()
        if group_by:
            results = await self.client.query_points_groups(
                collection_name=self.collection_name,
                query=q_models.NearestQuery(nearest=query_vector),
                query_filter=q_filter,
                limit=query_limit,
                group_by=group_by,
                group_size=1,
                with_vectors=with_vectors
            )
            hits = [g.hits[0] for g in results.groups if g.hits]
        else:
            results = await self.client.query_points(
                collection_name=self.collection_name,
                query=q_models.NearestQuery(nearest=query_vector),
                query_filter=q_filter,
                limit=query_limit,
                with_vectors=with_vectors
            )
            hits = results.points
        qdrant_ms = (time.time() - start_qdrant) * 1000

        rerank_ms = 0.0
        if apply_reranker and hits:
            # Stage 2: Neural Reranking (Track Latency)
            start_rerank = time.time()
            try:
                documents = [
                    f"Title: {h.payload.get('title', '')}. "
                    f"Brand: {h.payload.get('brand', '')}. "
                    f"Category: {h.payload.get('category', '')}. "
                    f"Description: {h.payload.get('description', '')}."
                    for h in hits
                ]
                rerank_top_n = max(20, fetch_limit * 5) if apply_diversity else max(20, fetch_limit)
                
                reranked_indices = await reranker_service.rerank(query_text, documents, top_n=rerank_top_n)
                hits = [hits[i] for i in reranked_indices]
            except Exception as e:
                logger.error(f"Reranker failed, falling back to Qdrant scores: {e}")
                hits = hits[:20]
            rerank_ms = (time.time() - start_rerank) * 1000

        mmr_ms = 0.0
        if apply_diversity and hits:
            # Stage 3: MMR Diversity (Track Latency)
            start_mmr = time.time()
            diverse_results = calculate_mmr(
                candidate_ids=[h.payload.get("product_id") for h in hits],
                candidate_vectors=[h.vector for h in hits],
                candidate_scores=[h.score for h in hits],
                limit=fetch_limit,
                diversity_penalty=diversity_penalty
            )
            mmr_ms = (time.time() - start_mmr) * 1000
            
            if apply_reranker:
                logger.info(
                    f"SEARCH FLOW LATENCY: "
                    f"Embedding={embed_ms:.2f}ms, "
                    f"VectorFetch={qdrant_ms:.2f}ms, "
                    f"Reranker={rerank_ms:.2f}ms, "
                    f"MMR={mmr_ms:.2f}ms"
                )
            
            return [{"product_id": pid, "score": score} for pid, score in diverse_results]
        
        if apply_reranker:
            logger.info(
                f"SEARCH FLOW LATENCY: "
                f"Embedding={embed_ms:.2f}ms, "
                f"VectorFetch={qdrant_ms:.2f}ms, "
                f"Reranker={rerank_ms:.2f}ms, "
                f"MMR=0.00ms"
            )
        
        return [{"product_id": h.payload.get("product_id"), "score": h.score} for h in hits][:fetch_limit]

    async def get_points_by_ids(self, store_id: str, product_ids: List[str]):
        """Helper to fetch raw points for a set of product IDs."""
        internal_ids = [str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{store_id}_{pid}")) for pid in product_ids]
        return await self.client.retrieve(
            collection_name=self.collection_name,
            ids=internal_ids,
            with_payload=True,
            with_vectors=True
        )

product_discovery = DiscoveryService()
