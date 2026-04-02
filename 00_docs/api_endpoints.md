# API Endpoint Specifications

This document outlines the available endpoints for the **Unified Shopify Recommendation Engine**.

## 1. Data Synchronization (`/sync`)
Endpoints for managing the product catalog and store lifecycle.

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

**Response:**
```json
{
  "status": "success",
  "message": "Successfully synced 1 products",
  "count": 1
}
```

### Delete Product
`DELETE /sync/{store_id}/products/{product_id}`

**Response:**
```json
{
  "status": "success",
  "message": "Product UT-001 deleted",
  "count": 0
}
```

### Delete Store Data
`DELETE /sync/{store_id}/delete-store`

**Security:**
* Requires `X-Admin-Token` header for authentication.
* Rate limited to 20 requests per minute.

**Response:**
```json
{
  "status": "success",
  "message": "Store 'store_name' data has been completely removed.",
  "count": 0
}
```

### Get Store Stats
`GET /sync/{store_id}/stats`

**Response:**
```json
{
  "store_id": "store_test_A",
  "product_count": 150,
  "status": "active"
}
```

### Debug Products (Development)
`POST /sync/{store_id}/debug`

**Payload:**
```json
{
  "product_ids": ["UT-001", "UT-002"]
}
```

**Response:**
Returns raw Qdrant points containing payload and internal metadata for the requested IDs.

---

## 2. Discovery Engine (`/search`)
High-performance endpoints for storefront integration.

### Semantic Search
`POST /search/{store_id}`

**Input:**
```json
{
  "query_text": "Vintage blue denim jackets",
  "filters": {
    "price": {"min": 50, "max": 150},
    "is_available": true
  },
  "limit": 10,
  "diversity_penalty": 0.3
}
```

**Response:**
```json
{
  "status": "success",
  "results": [
    { "product_id": "UT-001", "score": 0.892 },
    { "product_id": "UT-045", "score": 0.845 }
  ]
}
```

### Similar Products
`POST /search/{store_id}/similar/{product_id}`

**Input:**
```json
{
  "filters": { "is_available": true },
  "limit": 5,
  "diversity_penalty": 0.0
}
```

**Response:**
```json
{
  "status": "success",
  "results": [
    { "product_id": "UT-002", "score": 0.954 },
    { "product_id": "UT-009", "score": 0.912 }
  ]
}
```

---

## 3. Personalization Engine (`/recommend`)

### Personalized Recommendations
`POST /recommend/{store_id}`

**Input:**
```json
{
  "viewed_ids": ["UT-001", "UT-002"],
  "added_to_cart_ids": ["UT-003"],
  "purchased_ids": ["UT-004"],
  "filters": {
    "is_available": true
  },
  "limit": 10,
  "diversity_penalty": 0.5
}
```

**Response:**
```json
{
  "status": "success",
  "results": [
    { "product_id": "UT-010", "score": 0.887 },
    { "product_id": "UT-015", "score": 0.864 }
  ]
}
```

### Complementary Products ("Complete the Look")
`POST /recommend/{store_id}/complementary/{product_id}`

**Input:**
```json
{
  "filters": {},
  "limit": 3,
  "diversity_penalty": 0.1
}
```

**Response:**
```json
{
  "status": "success",
  "results": [
    { "product_id": "UT-ACC-01", "score": 0.782 },
    { "product_id": "UT-SHO-05", "score": 0.741 }
  ]
}
```

---

## 4. Health & Monitoring (`/health`)

### System Health
`GET /health/`

**Response:**
```json
{
  "system": "healthy",
  "dependencies": {
    "jina_ai": {
      "status": "healthy",
      "latency_ms": 124.5
    },
    "qdrant": {
      "status": "green",
      "optimizer_status": "ok",
      "segments_count": 4
    }
  }
}
```

---

## 5. Tenant-Based Rate Limiting
Enforced per **StoreID** to protect AI resources:

*   **Storefront Discovery (`/search`, `/recommend`):** 300 requests per minute.
*   **Synchronization API (`/sync`):** 20 requests per minute.
