# Implementation Plan: Unified Shopify Recommendation Engine

This document outlines the step-by-step roadmap for building the **Unified Shopify Recommendation Engine**.

---

## Phase 1: Foundation & Configuration
*   **Settings Management:** Use `pydantic-settings` to manage API keys (Jina, Qdrant), weights, and system-wide constants.
*   **Client Initialization:**
    *   Initialize `QdrantClient` in `async` mode.
    *   Initialize a persistent `httpx.AsyncClient` for Jina AI API requests.
*   **Multi-tenancy Setup:** Logic to ensure a Qdrant "Collection" exists for each `store_id` (or using a single collection with partitioning).

---

## Phase 2: Data Ingestion Pipeline (`/sync`)
*   **Model Definition:**
    *   `ProductUpsert`: Validates incoming Shopify product data.
    *   `EmbeddingSource`: Specific fields used for vectorization.
*   **Logic:**
    1.  Concatenate `title`, `description`, and `tags`.
    2.  Generate embedding using direct `httpx` POST requests to Jina AI's `/v1/embeddings` endpoint.
    3.  Upsert to Qdrant with `product_id` as the point ID and the store's custom JSON as the payload.

---

## Phase 3: The Discovery Engine
### 1. Semantic Search (`/search`)
*   **Logic:** Vectorize the search query -> Query Qdrant using the generated vector -> Apply metadata filters.

### 2. Similar Products (`/similar/{id}`)
*   **Logic:** Retrieve the vector for the given `product_id` -> Query Qdrant for nearest neighbors excluding the source ID.

### 3. Personalized Recommendations (`/recommend`)
*   **Weighted ID Strategy:**
    1.  Collect IDs from `viewed_ids`, `added_to_cart_ids`, and `purchased_ids`.
    2.  Create the `positive` list for Qdrant:
        *   Each `purchased_id` appears 5 times.
        *   Each `added_to_cart_id` appears 3 times.
        *   Each `viewed_id` appears 1 time.
    3.  Call `client.recommend(collection_name, positive=weighted_ids, strategy="average_vector")`.

---

## Phase 4: Dynamic Filtering Logic (BYOS)
A dedicated utility to translate the API `filters` object into Qdrant `Filter` objects:
*   **`{"color": ["Red", "Blue"]}`** → `FieldCondition(key="metadata.color", match=MatchAny(any=["Red", "Blue"]))`
*   **`{"price": {"min": 10, "max": 100}}`** → `FieldCondition(key="metadata.price", range=Range(gt=10, lt=100))`
*   **Recursive Mapping:** Support nested logic for complex merchant schemas.

---

## Phase 5: Reliability & Performance
*   **Error Handling:** Graceful handling of Jina API rate limits and Qdrant connection issues.
*   **Caching (Optional):** Cache embeddings for frequently searched terms or popular products.
*   **Logging:** Structured logging for tracking recommendation quality and system health.

---

## Phase 6: Validation & Testing
1.  **Unit Tests:** Verify the weighted ID list generation and filter translation logic.
2.  **Integration Tests:** End-to-end flow from `/sync` to `/recommend` using a test Qdrant collection.
3.  **Load Testing:** Measure latency under concurrent recommendation requests.
