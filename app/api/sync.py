from fastapi import APIRouter, HTTPException, Request
from typing import List
from models.schemas import ProductUpsert, SyncResponse
from services.embedding import embedding_service
from services.qdrant import qdrant_service
from qdrant_client.http import models as q_models
from core.config import settings
from utils.limiter import limiter, get_store_only_key
import logging
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{store_id}/products", response_model=SyncResponse)
@limiter.limit(settings.RATE_LIMIT_SYNC, key_func=get_store_only_key)
async def sync_products(request: Request, store_id: str, products: List[ProductUpsert]):
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
        # 1. Prepare text for vectorization (Using Search Core Fields)
        texts_to_embed = []
        for p in products:
            tags_str = ", ".join(p.tags) if p.tags else ""
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

            # A. Search Core Payload (Root Level)
            payload = {
                "store_id": store_id,
                "product_id": p.product_id,
                "title": p.title,
                "description": p.description,
                "brand": p.brand,
                "category": p.category,
                "tags": p.tags
            }

            # B. Commerce Metadata (Nested Object)
            # Only include non-None values to keep payload lean
            metadata_dict = p.metadata.model_dump(exclude_none=True)
            if metadata_dict:
                payload["metadata"] = metadata_dict

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
@limiter.limit(settings.RATE_LIMIT_SYNC, key_func=get_store_only_key)
async def delete_product(request: Request, store_id: str, product_id: str):
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

@router.get("/{store_id}/debug/{product_id}")
async def get_raw_product(store_id: str, product_id: str):
    """
    DEVELOPMENT ONLY: Fetches the raw stored point via QdrantService.
    """
    try:
        point = await qdrant_service.get_point_by_id(store_id, product_id)
        
        if not point:
            raise HTTPException(status_code=404, detail="Product not found in Qdrant.")

        return {
            "point_id": point.id,
            "payload": point.payload,
            "vector_preview": point.vector[:10] if point.vector else None,
            "vector_length": len(point.vector) if point.vector else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Debug fetch failed for {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Debug fetch failed.")
