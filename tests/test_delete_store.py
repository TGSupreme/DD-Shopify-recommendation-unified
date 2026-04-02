import httpx
import asyncio
import uuid

BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "admin_secret_key_123"

STORE_A = "store_test_A"
STORE_B = "store_test_B"

test_product = {
    "product_id": "prod_1",
    "title": "Test Product",
    "description": "A test product for deletion verification",
    "brand": "TestBrand",
    "category": "TestCategory",
    "tags": ["test"],
    "metadata": {
        "price": 10.0,
        "is_available": True
    }
}

async def verify():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Ingest into Store A
        print(f"Ingesting into {STORE_A}...")
        res = await client.post(f"{BASE_URL}/sync/{STORE_A}/products", json=[test_product])
        print(f"Store A Ingestion: {res.status_code} - {res.json()}")

        # 2. Ingest into Store B
        print(f"Ingesting into {STORE_B}...")
        res = await client.post(f"{BASE_URL}/sync/{STORE_B}/products", json=[test_product])
        print(f"Store B Ingestion: {res.status_code} - {res.json()}")

        # 3. Check stats
        print("Checking initial stats...")
        res_a = await client.get(f"{BASE_URL}/sync/{STORE_A}/stats")
        res_b = await client.get(f"{BASE_URL}/sync/{STORE_B}/stats")
        print(f"Stats A: {res_a.json()}")
        print(f"Stats B: {res_b.json()}")

        # 4. Delete Store A (with wrong token first)
        print(f"Attempting to delete {STORE_A} with WRONG token...")
        res = await client.request("DELETE", f"{BASE_URL}/sync/{STORE_A}/delete-store", headers={"X-Admin-Token": "wrong"})
        print(f"Wrong Token Deletion: {res.status_code} - {res.json()}")

        # 5. Delete Store A (with correct token)
        print(f"Deleting {STORE_A} with CORRECT token...")
        res = await client.request("DELETE", f"{BASE_URL}/sync/{STORE_A}/delete-store", headers={"X-Admin-Token": ADMIN_TOKEN})
        print(f"Correct Token Deletion: {res.status_code} - {res.json()}")

        # 6. Verify Store A is empty and Store B remains
        print("Verifying results...")
        res_a = await client.get(f"{BASE_URL}/sync/{STORE_A}/stats")
        res_b = await client.get(f"{BASE_URL}/sync/{STORE_B}/stats")
        print(f"Final Stats A: {res_a.json()}")
        print(f"Final Stats B: {res_b.json()}")

        if res_a.json()["product_count"] == 0 and res_b.json()["product_count"] > 0:
            print("SUCCESS: Store A wiped, Store B intact.")
        else:
            print("FAILURE: Deletion logic or isolation failed.")

if __name__ == "__main__":
    asyncio.run(verify())
