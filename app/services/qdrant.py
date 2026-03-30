from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from core.config import settings
from typing import List
import logging

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
                
                # 3. Categorical Keyword Indexes
                categorical_fields = [
                    "product_id", "brand", "category", "product_type", "collection", 
                    "color", "size", "material", "gender", "age_group", "season", "tags"
                ]
                for field in categorical_fields:
                    await self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field,
                        field_schema="keyword"
                    )
                
                # 4. Numeric Range Indexes
                numeric_fields = ["price", "discount", "rating", "weight"]
                for field in numeric_fields:
                    await self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field,
                        field_schema="integer" if field == "weight" else "float"
                    )
                
                # 5. Boolean State Index
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="is_available",
                    field_schema="bool"
                )

                logger.info(f"Successfully initialized collection {collection_name} with {len(categorical_fields)+len(numeric_fields)+2} indexes")
                
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

qdrant_service = QdrantService()
