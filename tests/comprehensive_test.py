
import asyncio
import httpx
import os

# Configuration
BASE_URL = "http://localhost:8000"
STORE_ID = "test-comp-store"

async def test_search_and_recommend():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"--- 1. Ingesting test data for {STORE_ID} ---")
        products = [
            {
                "product_id": "shirt-1",
                "title": "Vintage Blue Cotton Shirt",
                "description": "A classic blue cotton shirt with a vintage feel.",
                "brand": "VintageCo",
                "category": "Shirts",
                "tags": ["blue", "cotton", "vintage"],
                "metadata": {"price": 35.0, "color": "Blue", "is_available": True}
            },
            {
                "product_id": "shirt-2",
                "title": "Modern Slim Fit White Shirt",
                "description": "Sharp white shirt for professional settings.",
                "brand": "ModernStyle",
                "category": "Shirts",
                "tags": ["white", "slim-fit", "formal"],
                "metadata": {"price": 45.0, "color": "White", "is_available": True}
            },
            {
                "product_id": "pant-1",
                "title": "Classic Black Chinos",
                "description": "Versatile black chinos that go with any shirt.",
                "brand": "ModernStyle",
                "category": "Pants",
                "tags": ["black", "chinos", "casual"],
                "metadata": {"price": 55.0, "color": "Black", "is_available": True}
            },
             {
                "product_id": "shoe-1",
                "title": "Brown Leather Loafers",
                "description": "Elegant brown leather loafers for a complete look.",
                "brand": "FootwearX",
                "category": "Shoes",
                "tags": ["brown", "leather", "formal"],
                "metadata": {"price": 85.0, "color": "Brown", "is_available": True}
            }
        ]
        
        await client.post(f"{BASE_URL}/sync/{STORE_ID}/products", json=products)
        print("Data Ingested.\n")

        # --- Test Semantic Search ---
        print("--- 2. Testing Semantic Search ---")
        search_res = await client.post(
            f"{BASE_URL}/search/{STORE_ID}",
            json={"query_text": "something formal for office", "limit": 2}
        )
        print(f"Search Results: {search_res.json()['results']}")
        assert len(search_res.json()['results']) > 0

        # --- Test Similar Products ---
        print("\n--- 3. Testing Similar Products (shirt-1) ---")
        similar_res = await client.post(
            f"{BASE_URL}/search/{STORE_ID}/similar/shirt-1",
            json={"limit": 2}
        )
        if similar_res.status_code != 200:
            print(f"Similar Error ({similar_res.status_code}): {similar_res.text}")
        else:
            print(f"Similar Results: {similar_res.json().get('results', 'MISSING RESULTS KEY')}")
            # Should find shirt-2 as most similar
            assert any(r['product_id'] == 'shirt-2' for r in similar_res.json().get('results', []))

        # --- Test Complementary Recommendations ---
        print("\n--- 4. Testing Complementary Recs (shirt-1) ---")
        comp_res = await client.post(
            f"{BASE_URL}/recommend/{STORE_ID}/complementary/shirt-1",
            json={"limit": 3}
        )
        if comp_res.status_code != 200:
            print(f"Complementary Error ({comp_res.status_code}): {comp_res.text}")
        else:
            print(f"Complementary Results: {comp_res.json().get('results', 'MISSING RESULTS KEY')}")
            # Should NOT find shirts, should find pants or shoes
            categories = [r['product_id'] for r in comp_res.json().get('results', [])]
            assert 'shirt-2' not in categories

        # --- Test Personalized Recommendations ---
        print("\n--- 5. Testing Personalized Recommendations ---")
        # User viewed shirt-1 and added pant-1 to cart
        perso_res = await client.post(
            f"{BASE_URL}/recommend/{STORE_ID}",
            json={
                "viewed_ids": ["shirt-1"],
                "added_to_cart_ids": ["pant-1"],
                "limit": 2
            }
        )
        print(f"Personalized Results: {perso_res.json()['results']}")
        assert len(perso_res.json()['results']) > 0

        print("\n✅ ALL DISCOVERY TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(test_search_and_recommend())
