# Implementation Plan: Unified Shopify Recommendation Engine

This document outlines the step-by-step roadmap for building the **Unified Shopify Recommendation Engine**.

---

## Phase 1: Foundation, Configuration & Observability [COMPLETED]
*   **Settings Management:** Use `pydantic-settings` for API keys and weights. (Implemented in `app/core/config.py`)
*   **Structured Logging:** 
    *   Configure the standard `logging` module with a consistent format (Timestamp, Level, Name, Message). (Implemented in `app/main.py`)
    *   Initialize a global logger for the application.
*   **Client Initialization:**
    *   `QdrantClient` (async) and `JinaEmbeddings` initialization. (Implemented in `app/services/`)

---

## Phase 2: Data Ingestion Pipeline (`/sync`)
*   **Model Definition:** `ProductUpsert`, `EmbeddingSource`.
*   **Logic & Logging:**
    1.  **LOG:** Start of ingestion for `{store_id}` with `{count}` products.
    2.  Vectorize text fields via Jina AI. **LOG:** Jina API latency and token usage (if available).
    3.  Upsert to Qdrant. **LOG:** Success/Failure of the vector storage operation.

---

## Phase 3: The Discovery Engine
### 1. Semantic Search (`/search`)
*   **Logic:** Vectorize query -> Query Qdrant -> Apply filters.
*   **LOG:** Search query text and number of results returned for `{store_id}`.

### 2. Similar Products (`/similar/{id}`)
*   **LOG:** Source `{product_id}` for similarity search.

### 3. Personalized Recommendations (`/recommend`)
*   **Logic:** Weighted ID Strategy (5, 3, 1).
*   **LOG:** The final `weighted_ids` list used for the `recommend` call to allow for manual logic verification during debugging.

---

## Phase 4: Dynamic Filtering Logic (BYOS)
*   **Utility:** Translate JSON filters to Qdrant `Filter` objects.
*   **LOG:** Any cases where a merchant's filter cannot be parsed or mapped correctly.

---

## Phase 5: Reliability & Observability (Ongoing)
*   **Error Handling:** Catch and log full stack traces for `500` errors while returning clean messages to the client.
*   **Performance Monitoring:** Use middleware to log the total execution time of every API request.


---

## Phase 6: Validation & Testing
1.  **Unit Tests:** Verify the weighted ID list generation and filter translation logic.
2.  **Integration Tests:** End-to-end flow from `/sync` to `/recommend` using a test Qdrant collection.
3.  **Load Testing:** Measure latency under concurrent recommendation requests.
