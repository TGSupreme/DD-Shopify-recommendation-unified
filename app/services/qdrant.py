from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from core.config import settings
from typing import List
import logging

logger = logging.getLogger(__name__)

class QdrantService:
    """
    Phase 2: Implementing collection management with multi-tenancy optimizations.
    """
    def __init__(self):
        self.client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        self.vector_size = settings.VECTOR_DIMENSION

    async def ensure_collection(self, collection_name: str):
        """
        Ensures the shared Qdrant collection exists with optimizations for 
        multi-tenancy (Tenant Indexing) and guaranteed core fields.
        """
        try:
            collections = await self.client.get_collections()
            exists = any(c.name == collection_name for c in collections.collections)
            
            if not exists:
                logger.info(f"Creating shared collection: {collection_name}")
                
                # 1. Create collection with Optimized HNSW for multi-tenancy
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
                
                # 2. Create Tenant Payload Index (store_id)
                # This is the primary driver for multi-tenant performance.
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="store_id",
                    field_schema=models.KeywordIndexParams(
                        type="keyword",
                        is_tenant=True
                    )
                )
                
                # 3. Create Keyword Indexes for Guaranteed Core Fields
                # These fields are defined in our ProductUpsert model and are likely 
                # to be used for frequent filtering across all stores.
                core_fields = ["product_id", "brand", "category"]
                for field in core_fields:
                    logger.info(f"Creating keyword index for core field: '{field}'")
                    await self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field,
                        field_schema="keyword"
                    )
                
        except Exception as e:
            logger.error(f"Failed to ensure optimized Qdrant collection '{collection_name}': {str(e)}")
            raise

    async def upsert_products(self, collection_name: str, points: List[models.PointStruct]):
        """
        LOG: Success/Failure of the vector storage operation.
        """
        try:
            await self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info(f"Qdrant Upsert SUCCESS: {len(points)} products to '{collection_name}'")
        except Exception as e:
            logger.error(f"Qdrant Upsert FAILURE: {str(e)}")
            raise

qdrant_service = QdrantService()
