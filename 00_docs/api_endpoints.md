# API Endpoint Specifications

This document outlines the available endpoints for the **Unified Shopify Recommendation Engine**.

## 1. Data Synchronization (`/sync`)
These endpoints are used to keep the product catalog up-to-date.

### Upsert Products
`POST /sync/{store_id}/products`

**Payload:**
```json
[
  {
    "product_id": "gid://shopify/Product/123",
    "embedding_source": {
      "title": "Classic Cotton T-Shirt",
      "brand": "Urban Essentials",
      "category": "Apparel",
      "description": "Premium 100% organic cotton...",
      "tags": ["Essential", "Summer", "Cotton"]
    },
    "metadata": {
      "price": 45.00,
      "color": "Red",
      "available": true
    }
  }
]
```

### Delete Product
`DELETE /sync/{store_id}/products/{product_id}`

---

## 2. Discovery Engine (`/search`)
High-performance endpoints for storefront integration.

### Semantic Search
`POST /search/{store_id}`

**Input:**
* `query_text`: (String) The user's search query.
* `filters`: (Object, Optional) Dynamic filters (BYOS).
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
* `filters`: (Object, Optional) Dynamic filters.
* `limit`: (Integer, Optional) Default 10.

---

## 3. Personalization Engine (`/recommend`)
*(Phase 3 - In Progress)*

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
    "color": ["Blue", "Green"]
  },
  "limit": 12
}
```

---

## 4. Advanced Filtering Syntax (BYOS)
The `filters` object uses a **"Match Any, Satisfy All"** logic:
1.  **OR Logic (Within a Key):** Providing an array of values for a single key will match products that have *any* of those values.
2.  **AND Logic (Across Keys):** All keys provided in the `filters` object must be satisfied for a product to be returned.

**Example Filter:**
```json
"filters": {
  "color": ["Red", "Blue"],        // Logic: (Red OR Blue)
  "size": ["XL"],                  // Logic: AND (XL)
  "price": {"min": 20, "max": 100}  // Logic: AND (Price between 20 and 100)
}
```
*Resulting Query:* `(Color is Red OR Blue) AND (Size is XL) AND (Price is 20-100)`
