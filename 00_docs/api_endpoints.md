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
      "title": "...",
      "description": "...",
      "tags": ["...", "..."]
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

## 2. Discovery Engine
High-performance endpoints for storefront integration.

### Semantic Search
`POST /{store_id}/search`

**Input:**
* `query_text`: (String) The user's search query.
* `filters`: (Object, Optional) Dynamic filters.
* `limit`: (Integer, Optional) Default 10.

### Similar Products
`POST /{store_id}/similar/{product_id}`

**Input:**
* `filters`: (Object, Optional) Dynamic filters.
* `limit`: (Integer, Optional) Default 10.

### Personalized Recommendations
`POST /{store_id}/recommend`

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

## 3. Advanced Filtering Syntax (BYOS)
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

---

## 4. System Configuration
The following parameters are managed via **Environment Variables** for global consistency:

| Variable | Description | Recommended Value |
| :--- | :--- | :--- |
| `COLLECTION_NAME` | The default Qdrant collection for products | `products` |
| `WEIGHT_VIEW` | Influence of viewed products | 1.0 |
| `WEIGHT_CART` | Influence of added-to-cart products | 3.0 |
| `WEIGHT_PURCHASE` | Influence of purchased products | 5.0 |
| `VECTOR_DIMENSION` | Dimension of the embedding model | (e.g., 384 or 768) |
| `TOP_K` | Default number of results for discovery | 10 |
| `JINA_API_KEY` | API key for Jina AI embeddings | (Required) |
| `QDRANT_URL` | URL for the Qdrant instance | (Required) |
