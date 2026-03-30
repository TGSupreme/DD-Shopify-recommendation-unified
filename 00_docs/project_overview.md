# Unified Shopify Recommendation Engine
## Project Overview & Technical Vision

### 1. The Vision
The **Unified Shopify Recommendation Engine** is a next-generation AI-driven platform designed to provide "intelligent" product discovery and personalization for any Shopify store. Unlike traditional keyword-based systems, this engine uses **Vector-Based Semantic Search** to understand the *meaning* and *intent* behind products and customer behavior.

### 2. Core Capabilities
The system provides three primary entry points for merchants to enhance their store's user experience:

*   **Semantic Search:** Allows customers to find products based on concepts and descriptions rather than exact keyword matches.
*   **Similar Products:** Automatically identifies and displays products that are conceptually related to the one a customer is currently viewing.
*   **Personalized Recommendations:** Generates a unique list of products for every visitor based on their specific interaction history (Views, Cart Additions, and Purchases).

---

### 3. How It Works: The "Semantic" Advantage

#### A. Structured Ingestion with Standardized Metadata
To ensure maximum performance and predictable filtering, the system uses a **Standardized Flat Schema**. Merchants map their product data to a set of "First-Class" attributes that are natively indexed for sub-millisecond retrieval.

1.  **Core Identity:** `store_id` and `product_id`.
2.  **Core Product Attributes (Mandatory):** Text fields used to generate the **Product Vector** (Title, Description, Brand, Category, and Tags).
3.  **Standardized Commerce Attributes (Optional):** High-probability keys like `price`, `discount`, `color`, `size`, `material`, `gender`, `season`, and `is_available`.

*   **Performance First:** Every standardized field has a dedicated Qdrant payload index (Keyword, Range, or Boolean), ensuring that filtering never requires a slow "full-scan" of the data.
*   **Data Privacy & Isolation:** Every store’s data is kept within a shared collection but isolated using a unique Store ID as a **partition key** (Tenant Indexing). This ensures strict separation and superior database performance at scale.

#### B. The Weighted Recommendation Logic
Our "User Interest" engine calculates what a customer wants by looking at their journey across three tiers of intent:

1.  **Purchased Products (High Weight):** The strongest signal of long-term preference.
2.  **Added to Cart (Medium Weight):** High intent for immediate purchase.
3.  **Viewed Products (Low Weight):** General interest and browsing "vibe."

By combining the vectors of these products, the system calculates a **"User Interest Vector"** to find the most relevant matches in the store's catalog.

---

### 4. Technical Architecture Highlights
*   **High Performance:** Built on **FastAPI**, ensuring ultra-low latency for real-time recommendations.
*   **Vector Engine (Qdrant):** Uses native **Tenant Indexing** and **Query Points** API for optimized multi-tenant search.
*   **Embedding Service:** Leverages **Jina AI** for high-quality semantic representations of product data.
*   **Hybrid Rate Limiting:** Implements specialized quotas for shoppers (IP + StoreID) and merchants (StoreID-only), protecting expensive AI resources from abuse.
*   **Startup Initialization:** The system pre-validates connections and initializes all required indexes at server startup, ensuring immediate readiness.

---

### 5. Business Impact
*   **Increased Conversion:** By showing customers exactly what they are looking for through semantic understanding.
*   **Higher Average Order Value (AOV):** Through relevant "Similar Product" and personalized suggestions.
*   **Scalable & Reliable:** Optimized for high-throughput environments with a strict, high-performance schema.
