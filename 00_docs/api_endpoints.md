# API Endpoint Specifications

This document outlines the available endpoints for the **Unified Shopify Recommendation Engine**.

## 1. Data Synchronization (`/sync`)
These endpoints are used to keep the product catalog up-to-date using a standardized, high-performance schema.

### Upsert Products
`POST /sync/{store_id}/products`

**Payload (Flat Schema):**
```json
[
  {
    "product_id": "gid://shopify/Product/123",
    "title": "Classic Denim Jacket",
    "description": "Premium vintage denim...",
    "brand": "Levi's",
    "category": "Outerwear",
    "product_type": "Trucker Jacket",
    "collection": "Spring 2026",
    "tags": ["denim", "blue"],
    "price": 89.50,
    "is_available": true,
    "color": "Indigo",
    "size": "L"
  }
]
```
*Note: All fields except `product_id` and `title` are optional.*

### Delete Product
`DELETE /sync/{store_id}/products/{product_id}`

---

## 2. Discovery Engine (`/search`)
High-performance endpoints for storefront integration.

### Semantic Search
`POST /search/{store_id}`

**Input:**
* `query_text`: (String) The user's search query.
* `filters`: (Object, Optional) Standardized filters (e.g., `{"brand": ["Nike"], "price": {"max": 100}}`).
* `limit`: (Integer, Optional) Default 10.

**Response:**
```json
{
  "status": "success",
  "results": [
    { "product_id": "id1", "score": 0.89 }
  ]
}
```

### Similar Products
`POST /search/{store_id}/similar/{product_id}`

**Input:**
* `filters`: (Object, Optional) Standardized filters.
* `limit`: (Integer, Optional) Default 10.

---

## 3. Personalization Engine (`/recommend`)
*(Phase 3 - Implementation Pending)*

### Personalized Recommendations
`POST /recommend/{store_id}`

**Input:**
```json
{
  "viewed_ids": ["id1", "id2"],
  "added_to_cart_ids": ["id3"],
  "purchased_ids": ["id4", "id5"],
  "filters": {
    "price": {"min": 10, "max": 500},
    "color": ["Blue"]
  },
  "limit": 12
}
```

---

## 5. Tenant-Based Rate Limiting
To ensure fair resource allocation and protect against abuse, the system enforces a tenant-based rate-limiting policy:

*   **Storefront Discovery (`/search`, `/recommend`):**
    *   **Rate:** 300 requests per minute (Default).
    *   **Enforcement:** Per **StoreID**.
    *   **Goal:** Protects AI resources while allowing high-volume traffic from central backends.
*   **Synchronization API (`/sync`):**
    *   **Rate:** 20 requests per minute (Default).
    *   **Enforcement:** Per **StoreID**.
    *   **Goal:** Regulates merchant-level batch ingestion.

When a limit is exceeded, the API returns a `429 Too Many Requests` status code.
