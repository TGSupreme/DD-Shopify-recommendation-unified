import logging
import uuid
import time
from typing import List
from qdrant_client.http import models as q_models
from services.qdrant_base import QdrantBaseService
from services.embedding import embedding_service
from models.schemas import ProductUpsert
from core.config import settings

logger = logging.getLogger(__name__)

class IndexerService(QdrantBaseService):
    """
    Handles all write-based operations: Ingestion, Deletion, and Collection Setup.
    Enforces the Tri-tier Schema Standard.
    """
    
    async def ensure_collection(self):
        """Ensures the shared collection exists with optimized indexes."""
        try:
            collections = await self.client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)
            
            if not exists:
                logger.info(f"Initializing collection: {self.collection_name}")
                
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=q_models.VectorParams(
                        size=self.vector_size,
                        distance=q_models.Distance.COSINE
                    ),
                    hnsw_config=q_models.HnswConfigDiff(
                        m=0,           
                        payload_m=16   
                    )
                )
                
                # Setup Payload Indexes
                await self._setup_payload_indexes()
                logger.info(f"Collection {self.collection_name} ready with commerce indexes.")
                
        except Exception as e:
            logger.error(f"Failed to ensure collection: {str(e)}")
            raise

    async def _setup_payload_indexes(self):
        """Standardized payload indexing for high-performance filtering."""
        # 1. Mandatory Tenant Index
        await self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="store_id",
            field_schema=q_models.KeywordIndexParams(type="keyword", is_tenant=True)
        )
        
        # 2. Categorical Root & Metadata Indexes
        categorical_fields = [
            "product_id", "brand", "category", "tags",
            "metadata.color", "metadata.size", "metadata.material", 
            "metadata.gender", "metadata.age_group", "metadata.season", "metadata.collection"
        ]
        for field in categorical_fields:
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name=field,
                field_schema="keyword"
            )
            
        # 3. Numeric & Boolean Metadata Indexes
        numeric_fields = ["metadata.price", "metadata.discount", "metadata.rating", "metadata.weight"]
        for field in numeric_fields:
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name=field,
                field_schema="integer" if "weight" in field else "float"
            )
            
        await self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="metadata.is_available",
            field_schema="bool"
        )

    async def ingest_products(self, store_id: str, products: List[ProductUpsert]):
        """
        The Unified Ingestion Pipeline.
        Moves complex logic from the API layer to the service layer.
        """
        if not products:
            return 0

        start_total = time.time()
        logger.info(f"INGESTION PIPELINE: Store={store_id}, Count={len(products)}")

        # 1. Extract Core Text for Vectorization
        texts = []
        for p in products:
            tags_str = ", ".join(p.tags) if p.tags else ""
            texts.append(
                f"Title: {p.title}. Brand: {p.brand or ''}. "
                f"Category: {p.category or ''}. Description: {p.description or ''}. "
                f"Tags: {tags_str}"
            )

        # 2. Generate Embeddings (Embedding latency is already logged in service)
        embeddings = await embedding_service.get_embeddings(texts)

        # 3. Build Point Structs
        points = []
        for i, p in enumerate(products):
            # Deterministic UUID based on store + product pair
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{store_id}_{p.product_id}"))
            
            payload = {
                "store_id": store_id,
                "product_id": p.product_id,
                "title": p.title,
                "description": p.description,
                "brand": p.brand,
                "category": p.category,
                "tags": p.tags,
                "metadata": p.metadata.model_dump(exclude_none=True)
            }
            
            points.append(
                q_models.PointStruct(
                    id=point_id,
                    vector=embeddings[i],
                    payload=payload
                )
            )

        # 4. Upsert to Qdrant
        start_upsert = time.time()
        await self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        upsert_ms = (time.time() - start_upsert) * 1000
        total_ms = (time.time() - start_total) * 1000
        
        logger.info(
            f"INGESTION COMPLETED: "
            f"Store={store_id}, "
            f"Count={len(products)}, "
            f"UpsertLatency={upsert_ms:.2f}ms, "
            f"TotalLatency={total_ms:.2f}ms"
        )
        return len(products)

    async def delete_product(self, store_id: str, product_id: str):
        """Removes a single product from the index."""
        start_time = time.time()
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{store_id}_{product_id}"))
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=q_models.PointIdsList(points=[point_id])
        )
        latency_ms = (time.time() - start_time) * 1000
        logger.info(f"DELETE PRODUCT: Store={store_id}, Product={product_id}, Latency={latency_ms:.2f}ms")

    async def delete_store(self, store_id: str):
        """
        Securely removes all product data associated with a specific store.
        Uses a filter selector to ensure only the target store's data is removed.
        """
        start_time = time.time()
        logger.info(f"DELETION PIPELINE: Wiping entire store data for '{store_id}'")
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=q_models.FilterSelector(
                filter=q_models.Filter(
                    must=[
                        q_models.FieldCondition(
                            key="store_id",
                            match=q_models.MatchValue(value=store_id)
                        )
                    ]
                )
            )
        )
        latency_ms = (time.time() - start_time) * 1000
        logger.info(f"DELETE STORE: Store={store_id}, Latency={latency_ms:.2f}ms")

product_indexer = IndexerService()
