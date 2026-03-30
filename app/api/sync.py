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
    Standardized Ingestion Logic:
    1. Extract core text fields for vectorization.
    2. Prepare flat, indexed payload based on standardized metadata.
    3. Upsert to Qdrant.
    """
    if not products:
        return SyncResponse(status="success", message="No products to sync", count=0)

    logger.info(f"INGESTION START: Store={store_id}, ProductCount={len(products)}")

    try:
        # 1. Prepare text for vectorization
        texts_to_embed = []
        for p in products:
            tags_str = " ".join(p.tags) if p.tags else ""
            combined_text = (
                f"Title: {p.title}. "
                f"Brand: {p.brand or ''}. "
                f"Category: {p.category or ''}. "
                f"Description: {p.description or ''}. "
                f"Tags: {tags_str}"
            )
            texts_to_embed.append(combined_text)

        # 2. Get embeddings
        embeddings = await embedding_service.get_embeddings(texts_to_embed)

        # 3. Prepare Qdrant Points with Standardized Payload
        points = []
        for i, p in enumerate(products):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{store_id}_{p.product_id}"))
            
            # Map only non-None standardized fields to the root payload
            payload = {
                "store_id": store_id,
                "product_id": p.product_id,
                "title": p.title,
                "description": p.description,
            }

            # Add categorical, numeric, and boolean fields if they exist
            standard_keys = [
                "brand", "category", "product_type", "collection", "tags",
                "color", "size", "material", "gender", "age_group", "season",
                "price", "discount", "rating", "weight", "is_available"
            ]
            
            for key in standard_keys:
                val = getattr(p, key)
                if val is not None:
                    payload[key] = val
            
            points.append(
                q_models.PointStruct(
                    id=point_id,
                    vector=embeddings[i],
                    payload=payload
                )
            )

        # 4. Upsert
        collection_name = settings.COLLECTION_NAME
        await qdrant_service.upsert_products(collection_name, points)

        return SyncResponse(
            status="success", 
            message=f"Successfully synced {len(products)} products with standardized schema", 
            count=len(products)
        )

    except Exception as e:
        logger.error(f"INGESTION FAILED for store {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Data synchronization failed.")

@router.delete("/{store_id}/products/{product_id}", response_model=SyncResponse)
async def delete_product(store_id: str, product_id: str):
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
