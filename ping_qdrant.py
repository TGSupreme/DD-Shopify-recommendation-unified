#!/usr/bin/env python3
"""
Qdrant Keep-Alive, Seeding, and Similarity Tester Script
------------------------------------------------------
This utility script helps keep your Qdrant instance warm (preventing it from
spinning down due to inactivity on cloud/free tiers) and tests similarity searches.

You can run this:
1. Once: `python ping_qdrant.py`
2. In a loop to keep-alive: `python ping_qdrant.py --loop --interval 300`
3. To seed mock data directly without Jina AI key: `python ping_qdrant.py --seed`
"""

import sys
import os
import time
import argparse
import httpx
from typing import Optional, Dict, Any

# Ensure we can load dotenv variables before configuring settings
try:
    from dotenv import load_dotenv
    # Load environment variables from both root and app directory paths
    load_dotenv(os.path.join(os.path.dirname(__file__), "app", ".env"))
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

# Add 'app' directory to sys.path to resolve imports correctly
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

# Prevent validation failure if ADMIN_API_KEY is not in .env or environment
os.environ.setdefault("ADMIN_API_KEY", "admin_secret_key")

from qdrant_client import QdrantClient
from qdrant_client.http import models
from core.config import settings


# ANSI Terminal Colors
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"
COLOR_RESET = "\033[0m"

def print_success(msg: str):
    print(f"{COLOR_GREEN}[✓] {msg}{COLOR_RESET}")

def print_warning(msg: str):
    print(f"{COLOR_YELLOW}[!] {msg}{COLOR_RESET}")

def print_error(msg: str):
    print(f"{COLOR_RED}[✗] {msg}{COLOR_RESET}")

def print_info(msg: str):
    print(f"{COLOR_BLUE}[*] {msg}{COLOR_RESET}")

def print_header(msg: str):
    print(f"\n{COLOR_CYAN}=== {msg} ==={COLOR_RESET}")

def seed_mock_data_directly(
    url: str,
    api_key: Optional[str],
    collection_name: str,
    store_id: str = "clothing-store"
) -> bool:
    """Seeds sample data directly into Qdrant using random vectors to bypass Jina AI embedding requirements."""
    import json
    import numpy as np
    import hashlib
    import uuid
    
    print_header("SEEDING MOCK DATA DIRECTLY TO QDRANT")
    
    # Locate clothing_store_data.json
    json_path = os.path.join(os.path.dirname(__file__), "test-data", "clothing_store_data.json")
    if not os.path.exists(json_path):
        print_error(f"Sample data file not found at: {json_path}")
        return False
        
    print_info(f"Reading sample data from: {json_path}")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            products = json.load(f)
    except Exception as e:
        print_error(f"Failed to parse JSON sample data: {str(e)}")
        return False
        
    print_info(f"Loaded {len(products)} products from JSON.")
    print_info(f"Connecting to Qdrant at: {url}...")
    
    try:
        client = QdrantClient(url=url, api_key=api_key)
        
        # Ensure collection exists
        exists = client.collection_exists(collection_name)
        if not exists:
            print_info(f"Creating collection '{collection_name}' with 768-dim vectors...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=768,
                    distance=models.Distance.COSINE
                )
            )
            # Create payload index for store_id
            client.create_payload_index(
                collection_name=collection_name,
                field_name="store_id",
                field_schema=models.KeywordIndexParams(type="keyword", is_tenant=True)
            )
            client.create_payload_index(
                collection_name=collection_name,
                field_name="product_id",
                field_schema="keyword"
            )
            print_success(f"Created collection '{collection_name}'")
            
        print_info(f"Upserting {len(products)} points with generated 768-dim random vectors...")
        
        points = []
        for item in products:
            # Generate a reproducible random vector based on product_id to ensure consistency
            seed_val = int(hashlib.md5(item["product_id"].encode()).hexdigest(), 16) % (2**32)
            rng = np.random.default_rng(seed_val)
            vector = rng.normal(size=768).tolist()
            
            # Form point ID (UUID based on store_id and product_id to match indexer.py)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{store_id}_{item['product_id']}"))
            
            payload = {
                "store_id": store_id,
                "product_id": item["product_id"],
                "title": item["title"],
                "description": item.get("description", ""),
                "brand": item.get("brand"),
                "category": item.get("category"),
                "tags": item.get("tags", []),
                "metadata": item.get("metadata", {})
            }
            
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            )
            
        # Upsert in batches of 100
        batch_size = 100
        for offset in range(0, len(points), batch_size):
            batch = points[offset:offset + batch_size]
            client.upsert(
                collection_name=collection_name,
                points=batch
            )
            
        print_success(f"Successfully seeded {len(points)} products to store '{store_id}' in Qdrant collection '{collection_name}'.")
        return True
    except Exception as e:
        print_error(f"Failed to seed data directly to Qdrant: {str(e)}")
        return False

def ping_qdrant_direct(
    url: str,
    api_key: Optional[str],
    collection_name: str,
    store_id: Optional[str] = None,
    product_id: Optional[str] = None,
    limit: int = 5
) -> bool:
    """Connects to Qdrant directly using QdrantClient to check health and run a similarity query."""
    print_header("DIRECT QDRANT HEALTH CHECK & TEST SEARCH")
    print_info(f"Connecting to Qdrant at: {url}")
    print_info(f"Target Collection: {collection_name}")
    
    start_time = time.time()
    try:
        # Initialize sync Qdrant Client
        client = QdrantClient(url=url, api_key=api_key)
        
        # 1. Fetch collection info (warm up / wake up call)
        print_info("Retrieving collection configuration...")
        exists = client.collection_exists(collection_name)
        if not exists:
            print_warning(f"Collection '{collection_name}' does not exist.")
            print_info("Use `--seed` to create and populate it with sample products.")
            return False
            
        collection_info = client.get_collection(collection_name)
        latency = (time.time() - start_time) * 1000
        print_success(f"Successfully reached Qdrant. Latency: {latency:.2f}ms")
        print_info(f"Collection status: {collection_info.status}")
        print_info(f"Total points: {collection_info.points_count}")
        print_info(f"Optimizer status: {collection_info.optimizer_status}")
        
        # 2. Try to get a product from payload to run a search on if product_id/store_id is not specified
        target_store_id = store_id
        target_product_id = product_id
        target_vector = None
        
        if not target_store_id or not target_product_id:
            print_info("Scanning collection for a sample product to run similarity search...")
            points, _ = client.scroll(
                collection_name=collection_name,
                limit=1,
                with_payload=True,
                with_vectors=True
            )
            
            if points:
                sample_point = points[0]
                target_store_id = sample_point.payload.get("store_id") if sample_point.payload else None
                target_product_id = sample_point.payload.get("product_id") if sample_point.payload else None
                target_vector = sample_point.vector
                print_info(f"Found sample product in database: Store={target_store_id}, Product ID={target_product_id}")
            else:
                print_warning("No points found in collection. Cannot run a similarity search test.")
                print_info("Use `--seed` to populate the collection with mock clothing store data.")
                return True
        else:
            # Look up the specified product to get its vector
            print_info(f"Looking up vector for Store={target_store_id}, Product={target_product_id}...")
            points, _ = client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="store_id", match=models.MatchValue(value=target_store_id)),
                        models.FieldCondition(key="product_id", match=models.MatchValue(value=target_product_id))
                    ]
                ),
                limit=1,
                with_vectors=True
            )
            if points:
                target_vector = points[0].vector
                print_info("Found target product vector.")
            else:
                print_warning(f"Product ID '{target_product_id}' for store '{target_store_id}' not found in Qdrant. "
                              "Cannot run a direct vector search.")
        
        # 3. Perform the similarity search
        if target_vector:
            print_info(f"Running similarity search query for similar products...")
            search_start = time.time()
            
            # Setup Filter for store isolation
            q_filter = models.Filter(
                must=[
                    models.FieldCondition(key="store_id", match=models.MatchValue(value=target_store_id))
                ],
                must_not=[
                    models.FieldCondition(key="product_id", match=models.MatchValue(value=target_product_id))
                ]
            )
            
            # Search
            search_results = client.search(
                collection_name=collection_name,
                query_vector=target_vector,
                query_filter=q_filter,
                limit=limit
            )
            
            search_latency = (time.time() - search_start) * 1000
            print_success(f"Similarity search completed in {search_latency:.2f}ms. Found {len(search_results)} results:")
            for i, res in enumerate(search_results, 1):
                payload = res.payload or {}
                title = payload.get("title", "Unknown Title")
                brand = payload.get("brand", "Unknown Brand")
                price = payload.get("metadata", {}).get("price", "N/A")
                print(f"   {i}. ID: {payload.get('product_id')} | Title: {title} | Brand: {brand} | Price: ${price} (Score: {res.score:.4f})")
        
        return True
    except Exception as e:
        print_error(f"Failed to query Qdrant directly: {str(e)}")
        return False

def ping_fastapi_server(
    api_url: str,
    store_id: Optional[str] = None,
    product_id: Optional[str] = None,
    limit: int = 5
) -> bool:
    """Hits the FastAPI recommendation server endpoints to verify API functionality and wake Qdrant."""
    print_header("FASTAPI SERVER ENDPOINTS TEST")
    print_info(f"FastAPI Server URL: {api_url}")
    
    client = httpx.Client(timeout=15.0)
    
    # 1. Test /health endpoint
    print_info("Testing FastAPI /health endpoint...")
    try:
        health_res = client.get(f"{api_url}/health/")
        if health_res.status_code == 200:
            health_data = health_res.json()
            sys_status = health_data.get("system", "unknown")
            dep = health_data.get("dependencies", {})
            qdrant_status = dep.get("qdrant", {}).get("status", "unknown")
            
            print_success(f"FastAPI /health returned 200. Overall system status: {sys_status}")
            print_info(f"Qdrant Dependency Status: {qdrant_status}")
        else:
            print_warning(f"FastAPI /health returned status code: {health_res.status_code}")
    except Exception as e:
        print_warning(f"Could not connect to FastAPI /health endpoint: {str(e)}")
        print_info("Note: Make sure your FastAPI server is running (`python app/main.py`) to test API routes.")
        return False
        
    # 2. Test Similar Products endpoint
    target_store_id = store_id or "clothing-store"
    target_product_id = product_id or "UT-001"
    
    print_info(f"Testing similarity API: POST /search/{target_store_id}/similar/{target_product_id}")
    try:
        payload = {
            "filters": {"is_available": True},
            "limit": limit,
            "diversity_penalty": 0.0
        }
        search_res = client.post(
            f"{api_url}/search/{target_store_id}/similar/{target_product_id}",
            json=payload
        )
        
        if search_res.status_code == 200:
            res_data = search_res.json()
            results = res_data.get("results", [])
            print_success(f"Similarity API call succeeded. Found {len(results)} similar products.")
            for i, prod in enumerate(results, 1):
                print(f"   {i}. Product ID: {prod.get('product_id')} | Score: {prod.get('score'):.4f}")
        elif search_res.status_code == 404:
            print_warning(f"Similarity API returned 404 (Target product '{target_product_id}' not found in store '{target_store_id}').")
            print_info("This is expected if your database is empty. You can ingest sample data first or run this script with `--seed`.")
        else:
            print_error(f"Similarity API returned status code {search_res.status_code}: {search_res.text}")
    except Exception as e:
        print_error(f"Failed to reach FastAPI similarity API: {str(e)}")
        return False
        
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Wake up Qdrant and run similar product searches to prevent inactivity spin-downs."
    )
    parser.add_argument(
        "--qdrant-url",
        default=settings.QDRANT_URL,
        help=f"Direct Qdrant database URL (default: {settings.QDRANT_URL})"
    )
    parser.add_argument(
        "--api-key",
        default=settings.QDRANT_API_KEY,
        help="Direct Qdrant API key (default: read from environment)"
    )
    parser.add_argument(
        "--collection",
        default=settings.COLLECTION_NAME,
        help=f"Collection name to test (default: {settings.COLLECTION_NAME})"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="FastAPI application base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--store-id",
        help="Store ID to run similar products search for (defaults to first store found, or 'clothing-store')"
    )
    parser.add_argument(
        "--product-id",
        help="Product ID to find similar items for (defaults to first product found, or 'UT-001')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Limit of similar products to return (default: 5)"
    )
    parser.add_argument(
        "--mode",
        choices=["direct", "api", "both"],
        default="both",
        help="Whether to test direct Qdrant connection ('direct'), test FastAPI server endpoints ('api'), or test both ('both')"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed Qdrant with mock clothing store data directly (bypassing Jina AI)"
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously in a loop to keep Qdrant warm"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Interval in seconds between pings in loop mode (default: 300 / 5 minutes)"
    )

    args = parser.parse_args()

    # Seed mode
    if args.seed:
        success = seed_mock_data_directly(
            url=args.qdrant_url,
            api_key=args.api_key,
            collection_name=args.collection,
            store_id=args.store_id or "clothing-store"
        )
        if not success:
            sys.exit(1)
        # If seed was specified without loop, we can just finish
        if not args.loop:
            sys.exit(0)

    if args.loop:
        print_info(f"Loop mode active. Will ping every {args.interval} seconds.")
        try:
            while True:
                print(f"\n--- Ping cycle started at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
                if args.mode in ["direct", "both"]:
                    ping_qdrant_direct(
                        url=args.qdrant_url,
                        api_key=args.api_key,
                        collection_name=args.collection,
                        store_id=args.store_id,
                        product_id=args.product_id,
                        limit=args.limit
                    )
                if args.mode in ["api", "both"]:
                    ping_fastapi_server(
                        api_url=args.api_url,
                        store_id=args.store_id,
                        product_id=args.product_id,
                        limit=args.limit
                    )
                print_info(f"Cycle completed. Sleeping for {args.interval} seconds... Press Ctrl+C to exit.")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n")
            print_warning("Loop mode terminated by user.")
    else:
        # Run once
        direct_success = True
        api_success = True
        
        if args.mode in ["direct", "both"]:
            direct_success = ping_qdrant_direct(
                url=args.qdrant_url,
                api_key=args.api_key,
                collection_name=args.collection,
                store_id=args.store_id,
                product_id=args.product_id,
                limit=args.limit
            )
        if args.mode in ["api", "both"]:
            api_success = ping_fastapi_server(
                api_url=args.api_url,
                store_id=args.store_id,
                product_id=args.product_id,
                limit=args.limit
            )
            
        print_header("FINAL STATUS SUMMARY")
        if args.mode == "direct":
            if direct_success:
                print_success("Direct Qdrant ping succeeded.")
            else:
                print_error("Direct Qdrant ping failed.")
        elif args.mode == "api":
            if api_success:
                print_success("FastAPI server endpoint ping succeeded.")
            else:
                print_error("FastAPI server endpoint ping failed.")
        else:
            if direct_success and api_success:
                print_success("Both direct Qdrant and FastAPI endpoint pings succeeded.")
            elif direct_success:
                print_warning("Direct Qdrant succeeded, but FastAPI server endpoint check failed (make sure your server is running).")
            elif api_success:
                print_warning("FastAPI endpoint check succeeded, but direct Qdrant check failed.")
            else:
                print_error("Both check modes failed. Verify connections and credentials.")

if __name__ == "__main__":
    main()
