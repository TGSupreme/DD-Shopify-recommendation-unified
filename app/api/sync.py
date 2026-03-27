from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import ProductUpsert, SyncResponse
from services.embedding import embedding_service
from services.qdrant import qdrant_service
from qdrant_client.http import models as q_models
from core.config import settings
import logging
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{store_id}/products", response_model=SyncResponse)
async def sync_products(store_id: str, products: List[ProductUpsert]):
    """
    Phase 2 Logic:
    1. LOG: Start of ingestion for {store_id} with {count} products.
    2. Vectorize text fields via Jina AI.
    3. Upsert to Qdrant.
    """
    if not products:
        return SyncResponse(status="success", message="No products to sync", count=0)

    # 1. LOG: Start of ingestion
    logger.info(f"INGESTION START: Store={store_id}, ProductCount={len(products)}")

    try:
        # 2. Extract and Prepare text for Jina AI
        texts_to_embed = []
        for p in products:
            source = p.embedding_source
            tags_str = " ".join(source.tags) if source.tags else ""
            # Combining fields for a semantic "fingerprint"
            combined_text = (
                f"Title: {source.title}. "
                f"Brand: {source.brand}. "
                f"Category: {source.category}. "
                f"Description: {source.description}. "
                f"Tags: {tags_str}"
            )
            texts_to_embed.append(combined_text)

        # 3. Vectorize text (Logging handled inside service)
        embeddings = await embedding_service.get_embeddings(texts_to_embed)

        # 4. Prepare Qdrant Points
        points = []
        for i, p in enumerate(products):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{store_id}_{p.product_id}"))
            
            # Enrich metadata with core fields for easier filtering/display
            payload = {
                "store_id": store_id,
                "product_id": p.product_id,
                "title": p.embedding_source.title,
                "brand": p.embedding_source.brand,
                "category": p.embedding_source.category,
                "metadata": p.metadata
            }
            
            points.append(
                q_models.PointStruct(
                    id=point_id,
                    vector=embeddings[i],
                    payload=payload
                )
            )

        # 5. Upsert to Qdrant (Logging handled inside service)
        collection_name = settings.COLLECTION_NAME
        await qdrant_service.ensure_collection(collection_name)
        await qdrant_service.upsert_products(collection_name, points)

        return SyncResponse(
            status="success", 
            message=f"Successfully synced {len(products)} products", 
            count=len(products)
        )

    except Exception as e:
        logger.error(f"INGESTION FAILED for store {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Data synchronization failed.")

@router.delete("/{store_id}/products/{product_id}", response_model=SyncResponse)
async def delete_product(store_id: str, product_id: str):
    """
    Phase 2: Remove a product from the vector space.
    """
    try:
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{store_id}_{product_id}"))
        await qdrant_service.client.delete(
            collection_name=settings.COLLECTION_NAME,
            points_selector=q_models.PointIdsList(
                points=[point_id]
            )
        )
        logger.info(f"Product {product_id} deleted for store {store_id}")
        return SyncResponse(status="success", message=f"Product {product_id} deleted")
    except Exception as e:
        logger.error(f"Deletion failed for product {product_id} in store {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Product deletion failed.")
