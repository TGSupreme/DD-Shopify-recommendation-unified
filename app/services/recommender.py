import logging
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client.http import models as q_models
from services.qdrant_base import QdrantBaseService
from services.discovery import product_discovery
from core.config import settings

logger = logging.getLogger(__name__)

class RecommenderService(QdrantBaseService):
    """
    Handles Personalized Recommendations using Weighted User Intent.
    """

    async def get_personalized_recommendations(
        self,
        store_id: str,
        viewed_ids: List[str] = None,
        cart_ids: List[str] = None,
        purchase_ids: List[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        diversity_penalty: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Calculates a 'User Interest Vector' by weighting interactions.
        """
        start_total = time.time()
        # 1. Deduplicate & Validate IDs (internal lookup)
        all_pids = list(set((viewed_ids or []) + (cart_ids or []) + (purchase_ids or [])))
        if not all_pids:
            return []

        # 2. Retrieve existing points to get their vectors
        existing_points = await product_discovery.get_points_by_ids(store_id, all_pids)
        if not existing_points:
            return []

        existing_internal_ids = {str(p.id) for p in existing_points}
        
        # Mapping for easy lookup
        id_to_internal = {
            pid: str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{store_id}_{pid}")) 
            for pid in all_pids
        }

        # 3. Build Weighted Positive IDs list for Qdrant Recommend API
        positive_ids = []
        
        def add_weighted_ids(pids, weight):
            if not pids: return
            for pid in pids:
                internal_id = id_to_internal.get(pid)
                if internal_id in existing_internal_ids:
                    positive_ids.extend([internal_id] * int(weight))

        add_weighted_ids(viewed_ids, settings.WEIGHT_VIEW)
        add_weighted_ids(cart_ids, settings.WEIGHT_CART)
        add_weighted_ids(purchase_ids, settings.WEIGHT_PURCHASE)

        if not positive_ids:
            return []

        # 4. Prepare Filter & Pipeline Params
        from utils.filters import translate_filters
        q_filter = translate_filters(store_id, filters)
        
        apply_diversity = diversity_penalty > 0.0
        fetch_limit = limit or settings.TOP_K
        query_limit = fetch_limit * 5 if apply_diversity else fetch_limit

        # 5. Execute Recommendation via Qdrant
        start_qdrant = time.time()
        results = await self.client.query_points(
            collection_name=self.collection_name,
            query=q_models.RecommendQuery(
                recommend=q_models.RecommendInput(
                    positive=positive_ids,
                    strategy=q_models.RecommendStrategy.AVERAGE_VECTOR
                )
            ),
            query_filter=q_filter,
            limit=query_limit,
            with_vectors=apply_diversity
        )
        qdrant_ms = (time.time() - start_qdrant) * 1000
        
        hits = results.points

        # 6. Apply MMR Diversity if requested
        mmr_ms = 0.0
        if apply_diversity and hits:
            start_mmr = time.time()
            from utils.mmr import calculate_mmr
            diverse_results = calculate_mmr(
                candidate_ids=[h.payload.get("product_id") for h in hits],
                candidate_vectors=[h.vector for h in hits],
                candidate_scores=[h.score for h in hits],
                limit=fetch_limit,
                diversity_penalty=diversity_penalty
            )
            mmr_ms = (time.time() - start_mmr) * 1000
            
            total_ms = (time.time() - start_total) * 1000
            logger.info(
                f"PERSONALIZED RECOMMENDATION: "
                f"Store={store_id}, "
                f"Qdrant={qdrant_ms:.2f}ms, "
                f"MMR={mmr_ms:.2f}ms, "
                f"Total={total_ms:.2f}ms"
            )
            return [{"product_id": pid, "score": score} for pid, score in diverse_results]

        total_ms = (time.time() - start_total) * 1000
        logger.info(
            f"PERSONALIZED RECOMMENDATION: "
            f"Store={store_id}, "
            f"Qdrant={qdrant_ms:.2f}ms, "
            f"MMR=0.00ms, "
            f"Total={total_ms:.2f}ms"
        )
        return [{"product_id": h.payload.get("product_id"), "score": h.score} for h in hits][:fetch_limit]

product_recommender = RecommenderService()
