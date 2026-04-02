
import asyncio
import httpx
import uuid
import sys
import os

# Configuration
BASE_URL = "http://localhost:8000"
STORE_ID = "test-refactor-store"
ADMIN_KEY = os.getenv("ADMIN_API_KEY", "test_key")

async def test_ingestion():
    print(f"--- Testing Ingestion for {STORE_ID} ---")
    payload = [
        {
            "product_id": "prod-1",
            "title": "Refactored Blue Shirt",
            "description": "A high-quality blue shirt tested after refactoring.",
            "brand": "RefactorBrand",
            "category": "Shirts",
            "tags": ["blue", "cotton", "test"],
            "metadata": {
                "price": 29.99,
                "color": "Blue",
                "is_available": True
            }
        },
        {
            "product_id": "prod-2",
            "title": "Refactored Black Pants",
            "description": "Matching pants for the refactored shirt.",
            "brand": "RefactorBrand",
            "category": "Pants",
            "tags": ["black", "denim", "test"],
            "metadata": {
                "price": 49.99,
                "color": "Black",
                "is_available": True
            }
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/sync/{STORE_ID}/products",
                json=payload
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"Ingestion failed: {e}")
            return False

async def test_debug_and_stats():
    print(f"\n--- Testing Debug & Stats for {STORE_ID} ---")
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test Stats
        stats_res = await client.get(f"{BASE_URL}/sync/{STORE_ID}/stats")
        print(f"Stats Status: {stats_res.status_code}")
        print(f"Stats Output: {stats_res.json()}")
        
        # Test Debug (Raw Points)
        debug_payload = {"product_ids": ["prod-1"]}
        debug_res = await client.post(f"{BASE_URL}/sync/{STORE_ID}/debug", json=debug_payload)
        print(f"Debug Status: {debug_res.status_code}")
        if debug_res.status_code == 200:
            print("Debug: Successfully retrieved raw point.")
        else:
            print(f"Debug Error: {debug_res.text}")
            
        return stats_res.status_code == 200 and debug_res.status_code == 200

async def test_deletion():
    print(f"\n--- Testing Deletion for {STORE_ID} ---")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.delete(f"{BASE_URL}/sync/{STORE_ID}/products/prod-1")
        print(f"Delete Status: {response.status_code}")
        print(f"Delete Response: {response.json()}")
        
        # Verify deletion via stats
        stats_res = await client.get(f"{BASE_URL}/sync/{STORE_ID}/stats")
        count = stats_res.json().get("product_count", 0)
        print(f"Remaining Count: {count}")
        return response.status_code == 200 and count == 1

async def main():
    print("Starting Post-Refactor Health Check...")
    print("Ensure the server is running on http://localhost:8000")
    
    success = await test_ingestion()
    if success:
        success = await test_debug_and_stats()
    if success:
        success = await test_deletion()
        
    if success:
        print("\n✅ ALL REFACTOR TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED. CHECK LOGS.")

if __name__ == "__main__":
    asyncio.run(main())
