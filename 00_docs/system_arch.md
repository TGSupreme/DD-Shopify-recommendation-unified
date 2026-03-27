# System Architecture: Unified Shopify Recommendation Engine

This document provides a deep dive into the technical architecture, component interactions, and data processing logic of the **Unified Shopify Recommendation Engine**.

---

## 1. High-Level Architecture
The system is built as a cloud-native, high-performance microservice designed for real-time e-commerce personalization.

### Core Components
1.  **FastAPI Application:** The entry point for all storefront and administrative requests. Handles request validation, orchestration, and business logic.
2.  **Embedding Service (Direct API via `httpx`):** Transforms raw product text (Title, Description, etc.) into high-dimensional vectors (embeddings). This uses Jina's API-based models (e.g., `jina-embeddings-v2-base-en`) via direct HTTP requests, ensuring high-quality semantic representations with minimal overhead and maximum scalability.
3.  **Qdrant Vector Database:** The storage and search engine. Manages high-dimensional vectors and associated metadata, providing extremely fast similarity searches.
4.  **Shopify Integration Layer:** Future component (planned) to handle OAuth and Webhook-based data synchronization.

---

## 2. Data Ingestion & Synchronization Flow
To maintain a high-quality "Digital Fingerprint" for every product, the ingestion process follows a strict pipeline:

1.  **Request:** Merchant sends product data via `POST /sync/{store_id}/products`.
2.  **Vectorization:** The system extracts the `embedding_source` fields (Title, Description, Tags) and generates a single normalized vector.
3.  **Payload Preparation:** The vector is paired with the product ID and the "opaque" `metadata` object (Price, Color, etc.).
4.  **Storage:** The vector and payload are upserted into the Qdrant collection associated with the `store_id`.

---

## 3. The Recommendation Logic (Weighted Vector Math)
The "User Interest Vector" ($\vec{V}_{user}$) is the heart of the personalization engine. It represents a customer's current preference in the product vector space.

### Implementation: Qdrant Recommend API
The system leverages Qdrant's native `recommend` endpoint with the `average_vector` strategy:
*   **Weighted Input:** Interaction weights (5, 3, 1) are applied by repeating product IDs in the `positive` points list.
*   **Efficiency:** This approach offloads the vector averaging and similarity search to the database engine, ensuring sub-millisecond response times and native support for dynamic payload filters.

---

## 4. Multi-tenancy & Data Isolation
Security is a primary concern. The system ensures that Store A can never access Store B's data:

*   **Logical Isolation:** Every request requires a `store_id`.
*   **Vector Isolation:** Qdrant is configured to use a single collection (defined by `COLLECTION_NAME`) with the `store_id` as a partition key (Tenant Indexing). This ensures that searches are strictly scoped to a single merchant's catalog at the database level while maintaining high efficiency across many stores.
*   **Performance Indexing:** To ensure sub-millisecond filtering, the following payload indexes are automatically created upon collection initialization:
    *   **Tenant Index:** `store_id` (Keyword index with `is_tenant=True`).
    *   **Core Keyword Indexes:** `product_id`, `brand`, and `category`.
    *   **Metadata Filtering:** Opaque `metadata` fields are filtered dynamically after the tenant partition is applied.

---

## 5. Filtering Strategy (BYOS - Bring Your Own Schema)
The engine supports dynamic filtering on merchant-defined metadata without requiring pre-defined database schemas:

*   **Dynamic Payload Filtering:** Filters provided in the API request (e.g., `color: ["Blue"]`) are translated directly into Qdrant payload filters.
*   **Logic:**
    *   **Arrays:** Treated as an "OR" operation (match any value in the list).
    *   **Objects (Min/Max):** Translated into range queries for numerical data.
    *   **Multiple Keys:** Treated as an "AND" operation (all conditions must be met).

---

## 6. Performance & Scalability
*   **Asynchronous Processing:** FastAPI utilizes Python's `async/await` for non-blocking I/O operations with Qdrant.
*   **Horizontal Scaling:** The API layer is stateless and can be scaled horizontally behind a load balancer.
*   **Vector Indexing:** Qdrant uses HNSW (Hierarchical Navigable Small World) indexing to provide sub-millisecond search times even with millions of products.
