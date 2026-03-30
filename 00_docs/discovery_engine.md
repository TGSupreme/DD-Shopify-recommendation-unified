# Discovery Engine: Semantic Search & Similarity

This document explains the technical implementation of the **Discovery Engine** in the Unified Shopify Recommendation Engine.

---

## 1. High-Level Flow
The discovery engine uses **Vector-Based Retrieval** to find products conceptually related to a user's intent, rather than just matching keywords.

### A. Semantic Search Flow (`POST /search/{store_id}`)
1.  **Vectorization:** The user's query text (e.g., "warm winter coat") is converted into a 768-dimension vector using **Jina AI**.
2.  **Filter Application:** Mandatory `store_id` isolation is combined with any optional merchant-defined metadata filters (BYOS).
3.  **Vector Retrieval:** **Qdrant** identifies products whose "Digital Fingerprints" (vectors) are mathematically closest to the query vector.
4.  **Ranking:** Results are ranked by cosine similarity score.

### B. Similar Products Flow (`POST /search/{store_id}/similar/{product_id}`)
1.  **Vector Retrieval:** The existing vector for the target `product_id` is retrieved from the database.
2.  **Vector Search:** Qdrant finds other products with the highest similarity to the target vector, excluding the target product itself from the results.

---

## 2. "Bring Your Own Schema" (BYOS) Filtering
The engine supports dynamic, schema-less filtering on any JSON data provided during ingestion.

### Supported Filter Logic
| Logic Type | Input Example | Qdrant Translation |
| :--- | :--- | :--- |
| **Exact Match** | `"color": "Red"` | `MatchValue(value="Red")` |
| **Match Any (OR)** | `"size": ["M", "L"]` | `MatchAny(any=["M", "L"])` |
| **Range (AND)** | `"price": {"min": 10, "max": 50}` | `Range(gte=10, lte=50)` |

### Metadata Scoping
- **Core Fields:** `brand`, `category`, and `product_id` are indexed at the root level for maximum performance.
- **Custom Fields:** Any other fields provided in the `metadata` object are automatically scoped to `metadata.{field_key}` during filtering.

---

## 3. API Examples

### A. Simple Semantic Search
**Request:** `POST /search/store_123`
```json
{
  "query_text": "summer party dresses",
  "limit": 5
}
```
**Response:**
```json
{
  "status": "success",
  "results": [
    { "product_id": "dress_01", "score": 0.92 },
    { "product_id": "dress_05", "score": 0.88 }
  ]
}
```

### B. Search with Complex Filters
**Request:** `POST /search/store_123`
```json
{
  "query_text": "blue running shoes",
  "filters": {
    "brand": ["Nike", "Adidas"],
    "price": { "max": 120 }
  },
  "limit": 3
}
```

### C. Finding Similar Products
**Request:** `POST /search/store_123/similar/prod_abc123`
```json
{
  "limit": 5,
  "filters": {
    "available": true
  }
}
```

---

## 4. Performance Optimizations
- **Tenant Indexing:** All discovery operations use `store_id` as a partition key, ensuring searches only scan the relevant merchant's catalog.
- **Score Threshold:** A minimum threshold of `0.1` is applied to ensure that irrelevant results are not returned for vague queries.
- **Lean Responses:** Only `product_id` and `score` are returned to minimize payload size and improve latency for storefront rendering.
