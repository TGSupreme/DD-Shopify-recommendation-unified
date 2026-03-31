# API Endpoint Specifications

This document outlines the available endpoints for the **Unified Shopify Recommendation Engine**.

## 1. Data Synchronization (`/sync`)
Keep the product catalog up-to-date using the standardized Tri-tier schema.

### Upsert Products
`POST /sync/{store_id}/products`

**Payload (Tri-tier Schema):**
```json
[
  {
    "product_id": "UT-001",
    "title": "Maverick Denim Jacket",
    "description": "Classic denim...",
    "brand": "Urban Threadworks",
    "category": "Outerwear",
    "tags": ["denim", "vintage"],
    "metadata": {
      "price": 89.50,
      "color": "Indigo",
      "size": "L",
      "is_available": true
    }
  }
]
```

### Delete Product
`DELETE /sync/{store_id}/products/{product_id}`

### Debug Product (Development)
`GET /sync/{store_id}/debug/{product_id}`
Returns the full raw Qdrant point (payload + vector preview) for validation.

---

## 2. Discovery Engine (`/search`)
High-performance endpoints for storefront integration.

### Semantic Search
`POST /search/{store_id}`

**Input:**
* `query_text`: (String) The user's search query.
* `filters`: (Object, Optional) Standardized filters. Keys not in Search Core are automatically mapped to `metadata`.
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

---

## 3. Personalization Engine (`/recommend`)

### Personalized Recommendations
`POST /recommend/{store_id}`

**Input:**
```json
{
  "viewed_ids": ["id1", "id2"],
  "added_to_cart_ids": ["id3"],
  "purchased_ids": ["id4"],
  "filters": {
    "price": {"min": 10, "max": 500},
    "is_available": true
  },
  "limit": 12
}
```

---

## 4. Tenant-Based Rate Limiting
Enforced per **StoreID** to protect AI resources:

*   **Storefront Discovery (`/search`, `/recommend`):** 300 requests per minute.
*   **Synchronization API (`/sync`):** 20 requests per minute.
