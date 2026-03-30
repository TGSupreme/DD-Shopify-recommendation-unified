# System Architecture: Unified Shopify Recommendation Engine

This document provides a deep dive into the technical architecture, component interactions, and data processing logic of the **Unified Shopify Recommendation Engine**.

---

## 1. High-Level Architecture
The system is built as a high-performance microservice designed for real-time e-commerce personalization and discovery.

### Core Components
1.  **FastAPI Application:** The entry point for all storefront and administrative requests. Handles request validation, orchestration, and business logic.
2.  **Embedding Service:** Transforms raw product text into high-dimensional vectors (768-dim) using Jina's API-based models.
3.  **Qdrant Vector Database:** The storage and search engine. Manages high-dimensional vectors and associated standardized metadata, providing extremely fast similarity searches via the `query_points` API.

---

## 2. Standardized Data Ingestion Pipeline
To maintain a high-quality "Digital Fingerprint" for every product, the ingestion process follows a strict, high-performance pipeline:

1.  **Request:** Merchant sends product data via `POST /sync/{store_id}/products` using a **Standardized Flat Schema**.
2.  **Vectorization:** The system extracts the core text fields (`title`, `description`, `brand`, `category`, `tags`) to generate a single normalized vector.
3.  **Standardized Payload:** Only the pre-defined categorical, numeric, and state fields are accepted and stored as root-level payload attributes.
4.  **Storage:** The vector and payload are upserted into the shared Qdrant collection, partitioned by `store_id`.

---

## 3. The Recommendation Logic (Weighted Vector Math)
The personalization engine represents a customer's current preference in the product vector space using a "User Interest Vector".

### Implementation: Weighted Recommendation
*   **Interaction Weights:** Interaction weights are applied based on customer behavior:
    *   **Purchased (High):** Weight 5.0
    *   **Cart (Medium):** Weight 3.0
    *   **Viewed (Low):** Weight 1.0
*   **Vector Search:** The system uses the Qdrant `recommend` API or custom vector averaging to find the closest products in the merchant's partition.

---

## 4. Multi-tenancy & Performance Indexing
Security and speed are achieved through native Qdrant multi-tenancy and automatic indexing:

*   **Tenant Isolation:** `store_id` is used as a mandatory partition key.
*   **Automatic Startup Indexing:** On server startup, the system ensures all standardized commerce fields have corresponding payload indexes:
    *   **Keyword Indexes:** `brand`, `category`, `color`, `size`, `material`, `gender`, `season`, `tags`.
    *   **Range Indexes:** `price`, `discount`, `rating`, `weight`.
    *   **Boolean Index:** `is_available`.
*   **HNSW Optimization:** Configured for sub-millisecond search times with per-tenant sub-indexes.

---

## 5. Filtering Strategy (Strict Schema)
The engine strictly enforces a standardized schema to guarantee performance:

*   **Logic Mapping:**
    *   **Arrays:** Treated as "Match Any" (OR) within a single field.
    *   **Objects (Min/Max):** Translated into range queries for numeric data.
    *   **Standard Fields:** All filters are executed against root-level indexed fields, avoiding slow JSON-traversal.

---

## 6. System Lifecycle Management
The application utilizes FastAPI's **lifespan** context to manage resources:
*   **Startup:** Pre-initializes the collection and all 15+ payload indexes. Validates Qdrant connectivity.
*   **Shutdown:** Gracefully closes the Qdrant client and other persistent connections.
