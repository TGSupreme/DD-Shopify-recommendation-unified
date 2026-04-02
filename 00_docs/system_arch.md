# System Architecture: Unified Shopify Recommendation Engine

This document provides a deep dive into the technical architecture, component interactions, and data processing logic of the **Unified Shopify Recommendation Engine**.

---

## 1. High-Level Architecture
The system is built as a high-performance microservice designed for real-time e-commerce personalization and discovery.

### Core Components
1.  **FastAPI Application:** Entry point for storefront and administrative requests. Handles request validation, orchestration, and business logic.
2.  **Embedding Service:** Transforms Search Core fields (`title`, `description`, `brand`, `category`, `tags`) into 768-dim vectors using Jina AI.
3.  **Qdrant Vector Database:** Manages high-dimensional vectors and associated standardized metadata, providing similarity searches via the unified **`query_points`** API.

---

## 2. Standardized Ingestion Pipeline (Tri-tier Schema)
To maintain a high-quality "Digital Fingerprint" for every product, the ingestion process follows a strict pipeline:

1.  **Identity:** Map `product_id`.
2.  **Search Core (Vectorization):** Extract root text fields (`title`, `description`, `brand`, `category`, `tags`) to generate a single normalized vector.
3.  **Commerce Metadata (Nested Payload):** Categorical, numeric, and state fields are stored within a nested `metadata` object in the Qdrant payload.

---

## 3. Personalization Logic (Weighted Intent)
The system represents a customer's current preference in the product vector space using a "User Interest Vector".

### Implementation: Weighted Recommendation
*   **Interaction Weights:** 
    *   **Purchased (High):** Weight 5.0
    *   **Cart (Medium):** Weight 3.0
    *   **Viewed (Low):** Weight 1.0
*   **Vector Search:** The system uses the Qdrant **`query_points`** API with a **`RecommendQuery`** and the `AVERAGE_VECTOR` strategy to find the closest products in the merchant's partition.
*   **Resiliency:** The engine pre-validates all interaction IDs against the index before generating recommendations.

---

## 4. Multi-tenancy & Nested Indexing
Security and speed are achieved through native Qdrant multi-tenancy and automatic indexing:

*   **Tenant Isolation:** `store_id` is used as a mandatory partition key.
*   **Automatic Startup Indexing:** On server startup, the system ensures all standardized commerce fields have corresponding payload indexes:
    *   **Root Keyword Indexes:** `brand`, `category`, `tags`, `product_id`.
    *   **Nested Keyword Indexes:** `metadata.color`, `metadata.size`, `metadata.material`, `metadata.gender`, `metadata.season`, `metadata.collection`.
    *   **Nested Range Indexes:** `metadata.price`, `metadata.discount`, `metadata.rating`, `metadata.weight`.
    *   **Nested Boolean Index:** `metadata.is_available`.

---

## 5. Filtering Strategy (Strict Schema)
The engine strictly enforces a standardized schema to guarantee performance:

*   **Logic Mapping:**
    *   **Arrays:** Treated as "Match Any" (OR) within a single field.
    *   **Objects (Min/Max):** Translated into range queries for numeric data.
    *   **Prefixing:** The `translate_filters` utility automatically prefixes non-root keys with `metadata.` to ensure correct indexing.

---

## 6. Diversity Re-ranking (MMR)
To prevent "result clustering" (e.g., showing only identical white t-shirts), the system implements a post-search re-ranking phase.

### Maximal Marginal Relevance (MMR)
*   **Algorithm:** When `diversity_penalty > 0` is requested, the engine fetches a larger candidate pool (Top 50) including their vectors.
*   **Objective:** Iteratively select items that balance high relevance (semantic score) with low redundancy (cosine similarity to already selected items).
*   **Equation:** `Score = (1 - λ) * Relevance - λ * MaxSimilarity(already_selected)`.

---

## 7. Health & Monitoring
The system provides a detailed `/health` endpoint for proactive monitoring of critical dependencies:

*   **Jina AI Latency:** Measures real-time round-trip latency for embedding generation.
*   **Qdrant Segment Health:** Monitors collection status (`green`/`yellow`/`red`), optimizer status, and segment fragmentation.

---

## 8. System Lifecycle Management
The application utilizes FastAPI's **lifespan** context to manage resources:
*   **Startup:** Pre-initializes the collection and all nested payload indexes. Validates Qdrant connectivity.
*   **Shutdown:** Gracefully closes the Qdrant client and other persistent connections.
