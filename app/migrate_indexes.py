import asyncio
import logging
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from core.config import settings

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

async def migrate():
    client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    collection_name = settings.COLLECTION_NAME

    logger.info(f"Starting index migration for collection: {collection_name}")

    # 1. Old indexes to REMOVE (Flattened ones)
    old_fields = [
        "product_type", "collection", "color", "size", "material", "gender", 
        "age_group", "season", "price", "discount", "rating", "weight", "is_available"
    ]
    
    for field in old_fields:
        try:
            await client.delete_payload_index(collection_name, field)
            logger.info(f"Deleted old index: {field}")
        except Exception:
            logger.debug(f"Old index {field} did not exist or could not be deleted.")

    # 2. NEW Nested Metadata Indexes to CREATE
    
    # Categorical Metadata
    meta_categorical = [
        "color", "size", "material", "gender", "age_group", "season", "collection"
    ]
    for field in meta_categorical:
        logger.info(f"Creating nested index: metadata.{field}")
        await client.create_payload_index(
            collection_name=collection_name,
            field_name=f"metadata.{field}",
            field_schema="keyword"
        )
    
    # Numeric Metadata
    meta_numeric = ["price", "discount", "rating", "weight"]
    for field in meta_numeric:
        logger.info(f"Creating nested index: metadata.{field}")
        await client.create_payload_index(
            collection_name=collection_name,
            field_name=f"metadata.{field}",
            field_schema="integer" if field == "weight" else "float"
        )
    
    # Boolean Metadata
    logger.info("Creating nested index: metadata.is_available")
    await client.create_payload_index(
        collection_name=collection_name,
        field_name="metadata.is_available",
        field_schema="bool"
    )

    # 3. Ensure Root Search Core Indexes (Idempotent)
    root_categorical = ["product_id", "brand", "category", "tags"]
    for field in root_categorical:
        logger.info(f"Ensuring root index: {field}")
        await client.create_payload_index(
            collection_name=collection_name,
            field_name=field,
            field_schema="keyword"
        )

    logger.info("Migration COMPLETED successfully.")
    await client.close()

if __name__ == "__main__":
    import sys
    import os
    # Add app directory to sys.path to import settings
    sys.path.append(os.path.join(os.getcwd(), "app"))
    asyncio.run(migrate())
