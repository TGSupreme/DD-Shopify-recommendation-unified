import logging
import uuid
from typing import List, Dict, Any
from qdrant_client.http import models as q_models
from services.qdrant_base import QdrantBaseService
from core.config import settings

logger = logging.getLogger(__name__)

class AdminService(QdrantBaseService):
    """
    Handles Global Statistics, Tenant Insights, and Debugging operations.
    """

    async def get_store_stats(self, store_id: str) -> Dict[str, Any]:
        """Retrieves product count and status for a specific tenant."""
        try:
            count_result = await self.client.count(
                collection_name=self.collection_name,
                count_filter=q_models.Filter(
                    must=[
                        q_models.FieldCondition(
                            key="store_id",
                            match=q_models.MatchValue(value=store_id)
                        )
                    ]
                ),
                exact=True
            )
            return {
                "store_id": store_id,
                "product_count": count_result.count,
                "status": "active" if count_result.count > 0 else "empty"
            }
        except Exception as e:
            logger.error(f"Failed to fetch stats for store {store_id}: {str(e)}")
            raise

    async def get_global_system_stats(self) -> Dict[str, Any]:
        """Gathers 'God View' metrics for the entire microservice."""
        try:
            collection_info = await self.client.get_collection(self.collection_name)
            
            # Discover Tenants via Scroll
            scroll_result = await self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=["store_id"],
                with_vectors=False
            )
            
            points = scroll_result[0]
            unique_stores = list(set(p.payload.get("store_id") for p in points if p.payload))
            
            # Calculate Top 5 Tenants
            top_5 = []
            for store_id in unique_stores[:10]:
                c = await self.client.count(
                    collection_name=self.collection_name,
                    count_filter=q_models.Filter(
                        must=[q_models.FieldCondition(key="store_id", match=q_models.MatchValue(value=store_id))]
                    )
                )
                top_5.append({"store_id": store_id, "count": c.count})

            top_5 = sorted(top_5, key=lambda x: x["count"], reverse=True)[:5]

            return {
                "system": {
                    "version": "1.1.0 (Refactored Core)",
                    "status": str(collection_info.status),
                    "uptime_status": "healthy"
                },
                "collection_metrics": {
                    "name": self.collection_name,
                    "total_points": collection_info.points_count,
                    "indexed_vectors": collection_info.indexed_vectors_count,
                    "segments_count": collection_info.segments_count,
                    "optimizer_status": str(collection_info.optimizer_status),
                    "vectors_config": collection_info.config.params.vectors
                },
                "tenant_insight": {
                    "total_active_stores": len(unique_stores),
                    "top_5_tenants": top_5
                }
            }
        except Exception as e:
            logger.error(f"Global stats fetch failed: {str(e)}")
            raise

    async def get_debug_points(self, store_id: str, product_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetches raw points including vector previews for development debugging."""
        try:
            internal_ids = [str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{store_id}_{pid}")) for pid in product_ids]
            points = await self.client.retrieve(
                collection_name=self.collection_name,
                ids=internal_ids,
                with_payload=True,
                with_vectors=True
            )
            
            results = []
            for point in points:
                results.append({
                    "product_id": point.payload.get("product_id") if point.payload else None,
                    "point_id": point.id,
                    "payload": point.payload,
                    "vector_preview": point.vector[:10] if point.vector else None,
                    "vector_length": len(point.vector) if point.vector else 0
                })
            return results
        except Exception as e:
            logger.error(f"Debug retrieval failed: {str(e)}")
            raise

    async def get_health_status(self) -> Dict[str, Any]:
        """Basic health check for Qdrant connectivity and collection state."""
        try:
            info = await self.client.get_collection(self.collection_name)
            return {
                "status": str(info.status),
                "optimizer_status": str(info.optimizer_status),
                "segments_count": info.segments_count
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}

admin_service = AdminService()
