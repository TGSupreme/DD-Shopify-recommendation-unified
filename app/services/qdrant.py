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
        limit: int = 10
    ) -> List[models.ScoredPoint]:
        try:
            results = await self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=limit,
                score_threshold=0.1
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
        limit: int = 10
    ) -> List[models.ScoredPoint]:
        try:
            results = await self.client.recommend(
                collection_name=collection_name,
                positive=positive_ids,
                query_filter=query_filter,
                limit=limit,
                strategy=models.RecommendStrategy.AVERAGE_VECTOR
            )
            logger.info(f"Qdrant Recommend SUCCESS: Found {len(results)} matches")
            return results
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
        limit: int = 10
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
            limit=limit
        )

    async def get_point_by_id(self, store_id: str, product_id: str) -> Optional[models.Record]:
        """
        Retrieves a single point from Qdrant by calculating the internal UUID.
        Includes vectors for debugging purposes.
        """
        try:
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{store_id}_{product_id}"))
            
            points = await self.client.retrieve(
                collection_name=settings.COLLECTION_NAME,
                ids=[point_id],
                with_payload=True,
                with_vectors=True
            )
            
            return points[0] if points else None
        except Exception as e:
            logger.error(f"Failed to retrieve point for {product_id}: {str(e)}")
            raise

qdrant_service = QdrantService()
