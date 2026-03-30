# Implementation Plan V2: Standardized Discovery & Personalization

This document outlines the high-performance roadmap for the **Unified Shopify Recommendation Engine**, built on a **Strict Metadata Schema** and **Vector-Based Retrieval**.

---

## Phase 1: Foundation & Infrastructure [COMPLETED]
*   **Settings & Config:** Standardized environment management via `pydantic-settings`.
*   **Lifespan Management:** Server-side startup/shutdown hooks for Qdrant connection validation.
*   **Shared Collection Strategy:** Multi-tenant isolation using the `store_id` partition key.
*   **Automatic Indexing:** Creation of 15+ Keyword, Range, and Boolean indexes at startup.

---

## Phase 2: Standardized Ingestion Pipeline (`/sync`) [COMPLETED]
*   **Flat Schema Model:** Transitioned from nested BYOS to a validated, flat `ProductUpsert` model.
*   **Optimized Vectorization:** Extraction of core text fields for Jina AI embeddings.
*   **Native Payload Storage:** Direct mapping of commerce attributes (price, color, availability) to the root payload.

---

## Phase 3: The Discovery Engine (`/search`) [COMPLETED]
*   **Semantic Search:** Vector-based retrieval using the `query_points` API.
*   **Standardized Filtering:** Implementation of the `translate_filters` utility for sub-millisecond commerce filtering.
*   **Product Similarity:** ID-to-Vector lookup for "Similar Products" discovery.
*   **Lean Responses:** Optimized payloads returning only `product_id` and `score`.

---

## Phase 4: Personalization Engine (`/recommend`) [IN PROGRESS]
*   **Weighted Intent Logic:** Implementing the "User Interest Vector" calculation:
    *   **Purchased:** Weight 5.0
    *   **Add to Cart:** Weight 3.0
    *   **Viewed:** Weight 1.0
*   **Qdrant Recommend API:** Leveraging the native `recommend` endpoint for real-time, weighted vector averaging.
*   **Interaction-Based Filtering:** Ensuring recommendations exclude products the user has already purchased (Optional toggle).

---

## Phase 5: Tenant-Only Rate Limiting [COMPLETED]
*   **Central Backend Support:** Shifted from hybrid to **StoreID-only** limiting to support requests from a single central backend.
*   **Storefront Quota:** Increased to **300 req/min** to handle high shopper traffic across stores.
*   **Sync API Quota:** Increased to **20 req/min** for faster bulk data synchronization.
*   **Middleware Integration:** Global exception handling for `429` errors.

---

## Phase 6: Advanced Ranking & Sorting [PLANNED]
*   **Dynamic Sorting:** Adding the ability to sort discovery results by:
    *   `price` (ASC/DESC)
    *   `rating` (DESC)
    *   `created_at` (DESC - for New Arrivals)
*   **Score Boosting:** Applying business logic (e.g., boosting products with a high `discount` or `is_available=True`) on top of semantic relevance.

---

## Phase 6: Production Readiness & Validation [PLANNED]
*   **Comprehensive Integration Tests:** End-to-end validation of the synchronized discovery flow.
*   **Performance Benchmarking:** Measuring latency under high-concurrency for multi-tenant search.
*   **Documentation Finalization:** Final review of API contracts and merchant integration guides.
