import httpx
import asyncio
import time

# Configuration
BASE_URL = "http://localhost:8000"
STORE_ID = "ratelimit"
SYNC_URL = f"{BASE_URL}/sync/{STORE_ID}/products"

# Sample product data
PRODUCT_DATA = [
    {
        "product_id": "test_prod_1",
        "title": "Rate Limit Test Product",
        "price": 10.0,
        "is_available": True
    }
]

async def test_rate_limit():
    async with httpx.AsyncClient() as client:
        print(f"Starting Rate Limit Test for Sync API (StoreID: {STORE_ID})...")
        print(f"Limit should be around 10 requests per minute.\n")
        
        for i in range(1, 13):
            start_time = time.time()
            try:
                response = await client.post(SYNC_URL, json=PRODUCT_DATA)
                latency = time.time() - start_time
                
                if response.status_code == 200:
                    print(f"Request {i:02d}: SUCCESS (200) - Latency: {latency:.2f}s")
                elif response.status_code == 429:
                    print(f"Request {i:02d}: BLOCKED (429 Too Many Requests) - Latency: {latency:.2f}s")
                else:
                    print(f"Request {i:02d}: FAILED ({response.status_code}) - {response.text}")
                    
            except Exception as e:
                print(f"Request {i:02d}: ERROR - {str(e)}")
            
            # Small delay to not overwhelm the network but fast enough to trigger the limit
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(test_rate_limit())
