import logging
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from core.config import settings

logger = logging.getLogger(__name__)

class QdrantService:
    """
    Standardized Qdrant Service with optimized indexing for first-class commerce fields.
    """
    def __init__(self):
        self.client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        self.vector_size = settings.VECTOR_DIMENSION

    async def ensure_collection(self, collection_name: str):
        """
        Ensures the shared Qdrant collection exists with optimized indexes
        for the standardized commerce schema.
        """
        try:
            collections = await self.client.get_collections()
            exists = any(c.name == collection_name for c in collections.collections)
            
            if not exists:
                logger.info(f"Creating shared standardized collection: {collection_name}")
                
                # 1. Create collection with Optimized HNSW
                await self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE
                    ),
                    hnsw_config=models.HnswConfigDiff(
                        m=0,           # Disable global index
                        payload_m=16   # Enable per-tenant sub-indexes
                    )
                )
                
                # 2. Mandatory Tenant Index (store_id)
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="store_id",
                    field_schema=models.KeywordIndexParams(
                        type="keyword",
                        is_tenant=True
                    )
                )
                
                # 3. Categorical Keyword Indexes (Root Level - Search Core)
                root_categorical = ["product_id", "brand", "category", "tags"]
                for field in root_categorical:
                    await self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field,
                        field_schema="keyword"
                    )

                # 4. Categorical Metadata Indexes (Nested Level)
                meta_categorical = [
                    "color", "size", "material", "gender", "age_group", "season", "collection"
                ]
                for field in meta_categorical:
                    await self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=f"metadata.{field}",
                        field_schema="keyword"
                    )
                
                # 5. Numeric Metadata Indexes (Nested Range)
                meta_numeric = ["price", "discount", "rating", "weight"]
                for field in meta_numeric:
                    await self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=f"metadata.{field}",
                        field_schema="integer" if field == "weight" else "float"
                    )
                
                # 6. Boolean Metadata Index
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="metadata.is_available",
                    field_schema="bool"
                )

                logger.info(f"Successfully initialized collection {collection_name} with optimized nested indexes")
                
        except Exception as e:
            logger.error(f"Failed to ensure optimized Qdrant collection '{collection_name}': {str(e)}")
            raise

    async def upsert_products(self, collection_name: str, points: List[models.PointStruct]):
        try:
            await self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info(f"Qdrant Upsert SUCCESS: {len(points)} products")
        except Exception as e:
            logger.error(f"Qdrant Upsert FAILURE: {str(e)}")
            raise

    async def search_products(
        self, 
        collection_name: str, 
        query_vector: List[float], 
        query_filter: models.Filter,
        limit: int = 10,
        include_vectors: bool = False,
        group_by: Optional[str] = None,
        group_size: int = 1
    ) -> List[models.ScoredPoint]:
        try:
            if group_by:
                # Use query_points_groups for grouping
                results = await self.client.query_points_groups(
                    collection_name=collection_name,
                    query=models.NearestQuery(
                        nearest=query_vector
                    ),
                    query_filter=query_filter,
                    limit=limit,
                    group_by=group_by,
                    group_size=group_size,
                    score_threshold=0.1,
                    with_vectors=include_vectors
                )
                
                # Extract the top hit from each group
                scored_points = []
                for group in results.groups:
                    if group.hits:
                        scored_points.append(group.hits[0])
                logger.info(f"Qdrant Grouped Query SUCCESS: Found {len(scored_points)} groups")
                return scored_points
            else:
                # Use standard query_points
                results = await self.client.query_points(
                    collection_name=collection_name,
                    query=models.NearestQuery(
                        nearest=query_vector
                    ),
                    query_filter=query_filter,
                    limit=limit,
                    score_threshold=0.1,
                    with_vectors=include_vectors
                )
                logger.info(f"Qdrant Query SUCCESS: Found {len(results.points)} matches")
                return results.points
        except Exception as e:
            logger.error(f"Qdrant Query FAILURE: {str(e)}")
            raise

    async def recommend_products(
        self, 
        collection_name: str, 
        positive_ids: List[str], 
        query_filter: models.Filter,
        limit: int = 10,
        include_vectors: bool = False
    ) -> List[models.ScoredPoint]:
        try:
            results = await self.client.query_points(
                collection_name=collection_name,
                query=models.RecommendQuery(
                    recommend=models.RecommendInput(
                        positive=positive_ids,
                        strategy=models.RecommendStrategy.AVERAGE_VECTOR
                    )
                ),
                query_filter=query_filter,
                limit=limit,
                with_vectors=include_vectors
            )
            logger.info(f"Qdrant Recommend SUCCESS: Found {len(results.points)} matches")
            return results.points
        except Exception as e:
            logger.error(f"Qdrant Recommend FAILURE: {str(e)}")
            raise

    async def get_personalized_recommendations(
        self,
        store_id: str,
        viewed_ids: List[str],
        cart_ids: List[str],
        purchase_ids: List[str],
        query_filter: models.Filter,
        limit: int = 10,
        include_vectors: bool = False
    ) -> List[models.ScoredPoint]:
        """
        Business Logic:
        1. Deduplicate & Validate IDs (internal lookup)
        2. Apply weights from settings
        3. Execute recommendation search
        """
        # 1. Deduplicate and validate existence of IDs
        all_pids = list(set(viewed_ids + cart_ids + purchase_ids))
        if not all_pids:
            return []

        id_map = {pid: str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{store_id}_{pid}")) for pid in all_pids}
        internal_ids = list(id_map.values())

        # Check which IDs actually exist in Qdrant
        existing_points = await self.client.retrieve(
            collection_name=settings.COLLECTION_NAME,
            ids=internal_ids,
            with_payload=False,
            with_vectors=False
        )
        
        existing_internal_ids = {str(p.id) for p in existing_points}

        # 2. Build Weighted Positive IDs list
        positive_ids = []
        w_view = int(settings.WEIGHT_VIEW)
        w_cart = int(settings.WEIGHT_CART)
        w_purchase = int(settings.WEIGHT_PURCHASE)

        def add_weighted_ids(pids, weight):
            for pid in pids:
                internal_id = id_map[pid]
                if internal_id in existing_internal_ids:
                    positive_ids.extend([internal_id] * weight)

        add_weighted_ids(viewed_ids, w_view)
        add_weighted_ids(cart_ids, w_cart)
        add_weighted_ids(purchase_ids, w_purchase)

        if not positive_ids:
            return []

        # 3. Search using Qdrant Recommend API
        return await self.recommend_products(
            collection_name=settings.COLLECTION_NAME,
            positive_ids=positive_ids,
            query_filter=query_filter,
            limit=limit,
            include_vectors=include_vectors
        )

    async def get_points_by_ids(self, store_id: str, product_ids: List[str]) -> List[models.Record]:
        """
        Retrieves multiple points from Qdrant by calculating their internal UUIDs.
        Includes vectors for debugging purposes.
        """
        try:
            internal_ids = [
                str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{store_id}_{pid}")) 
                for pid in product_ids
            ]
            
            points = await self.client.retrieve(
                collection_name=settings.COLLECTION_NAME,
                ids=internal_ids,
                with_payload=True,
                with_vectors=True
            )
            
            return points
        except Exception as e:
            logger.error(f"Failed to retrieve points for {product_ids}: {str(e)}")
            raise

    async def get_store_stats(self, store_id: str) -> Dict[str, Any]:
        """
        Retrieves store-specific statistics using indexed filters.
        """
        try:
            # Calculate counts based on tenant partition key
            count_result = await self.client.count(
                collection_name=settings.COLLECTION_NAME,
                count_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="store_id",
                            match=models.MatchValue(value=store_id)
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
            logger.error(f"Failed to get stats for store {store_id}: {str(e)}")
            raise

    async def get_global_stats(self) -> Dict[str, Any]:
        """
        Gathers 'God View' metrics for the entire recommendation microservice.
        """
        try:
            # 1. Get Collection & System Info
            collection_info = await self.client.get_collection(settings.COLLECTION_NAME)
            
            # 2. Discover Tenants via Scroll (Fetch unique store_ids)
            # We scroll through points to find unique store_ids in the payload
            scroll_result = await self.client.scroll(
                collection_name=settings.COLLECTION_NAME,
                limit=1000, # Adjust based on expected number of stores
                with_payload=["store_id"],
                with_vectors=False
            )
            
            points = scroll_result[0]
            unique_stores = list(set(p.payload.get("store_id") for p in points if p.payload))
            
            # 3. Calculate Top Tenants (Manual count for the first few discovered stores)
            top_5 = []
            for store_id in unique_stores[:10]: # Check first 10 discovered stores
                c = await self.client.count(
                    collection_name=settings.COLLECTION_NAME,
                    count_filter=models.Filter(
                        must=[models.FieldCondition(key="store_id", match=models.MatchValue(value=store_id))]
                    )
                )
                top_5.append({"store_id": store_id, "count": c.count})

            # Sort to get the actual Top 5 from our sample
            top_5 = sorted(top_5, key=lambda x: x["count"], reverse=True)[:5]

            return {
                "system": {
                    "version": "1.0.0 (Unified Core)",
                    "status": str(collection_info.status),
                    "uptime_status": "healthy"
                },
                "collection_metrics": {
                    "name": settings.COLLECTION_NAME,
                    "total_points": collection_info.points_count,
                    "indexed_vectors": collection_info.indexed_vectors_count,
                    "segments_count": collection_info.segments_count,
                    "optimizer_status": str(collection_info.optimizer_status),
                    "vectors_config": {
                        "size": settings.VECTOR_DIMENSION,
                        "distance": "Cosine",
                        "hnsw_config": {
                            "m": collection_info.config.hnsw_config.m if hasattr(collection_info.config.hnsw_config, 'm') else 0
                        }
                    }
                },
                "tenant_insight": {
                    "total_active_stores": len(unique_stores),
                    "top_5_tenants": top_5
                }
            }
        except Exception as e:
            logger.error(f"Global stats fetch failed: {str(e)}")
            raise

    async def check_health(self) -> dict:
        """
        Checks Qdrant segment health and collection status.
        """
        try:
            collection_info = await self.client.get_collection(settings.COLLECTION_NAME)
            return {
                "status": str(collection_info.status),
                "optimizer_status": str(collection_info.optimizer_status),
                "segments_count": collection_info.segments_count
            }
        except Exception as e:
            logger.error(f"Qdrant health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "optimizer_status": "unknown",
                "segments_count": 0
            }

qdrant_service = QdrantService()
