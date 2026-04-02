
import asyncio
import os
import sys

# MUST set env before importing anything that uses Settings
os.environ["ADMIN_API_KEY"] = "test_key"
sys.path.append(os.path.join(os.getcwd(), 'app'))

from services.discovery import product_discovery
from services.indexer import product_indexer
from models.schemas import ProductUpsert, ProductMetadata

async def debug_services():
    store_id = "debug-test-store"
    product_id = "test-item"
    
    print(f"--- 1. Testing Indexer for {store_id} ---")
    p = ProductUpsert(
        product_id=product_id,
        title="Debug Item",
        category="Test",
        metadata=ProductMetadata(is_available=True)
    )
    try:
        await product_indexer.ensure_collection()
        await product_indexer.ingest_products(store_id, [p])
        print("Ingested.")
    except Exception as e:
        print(f"Indexer failed: {e}")
        return

    print(f"\n--- 2. Testing Discovery.get_points_by_ids ---")
    try:
        points = await product_discovery.get_points_by_ids(store_id, [product_id])
        print(f"Points found: {len(points)}")
        if points:
            print(f"Point ID: {points[0].id}")
            print(f"Point Payload: {points[0].payload}")
        else:
            print("No points returned for ID lookup!")
    except Exception as e:
        print(f"Discovery helper failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_services())
