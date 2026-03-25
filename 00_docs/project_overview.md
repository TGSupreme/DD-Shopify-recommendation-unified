# Unified Shopify Recommendation Engine
## Project Overview & Technical Vision

### 1. The Vision
The **Unified Shopify Recommendation Engine** is a next-generation AI-driven platform designed to provide "intelligent" product discovery and personalization for any Shopify store. Unlike traditional keyword-based systems, this engine uses **Vector-Based Semantic Search** to understand the *meaning* and *intent* behind products and customer behavior.

### 2. Core Capabilities
The system provides three primary entry points for merchants to enhance their store's user experience:

*   **Semantic Search:** Allows customers to find products based on concepts and descriptions rather than exact keyword matches (e.g., searching for "summer party outfit" and finding relevant floral dresses and sandals).
*   **Similar Products:** Automatically identifies and displays products that are conceptually related to the one a customer is currently viewing.
*   **Personalized Recommendations:** Generates a unique list of products for every visitor based on their specific interaction history (Views, Cart Additions, and Purchases).

---

### 3. How It Works: The "Semantic" Advantage

#### A. Structured Ingestion with Flexible Metadata
To integrate a store, the system requires a hybrid data approach to ensure both high-quality AI understanding and maximum merchant flexibility:

1.  **Core Identity:** `store_id` and `product_id`.
2.  **Core Product Attributes (Mandatory):** Text fields used as input to generate the **Product Vector** (Title, Description, Category, Brand, and Tags). These are processed by a pre-trained AI model to create the mathematical representation of the product.
3.  **Extended Metadata (Optional & Schema-less):** Any additional JSON data the store wishes to provide (Price, Discount, Availability, Material, etc.).

*   **Semantic Intelligence:** By requiring core text fields, the system ensures that every product has a high-quality "Digital Fingerprint" in the vector space.
*   **"Bring Your Own Schema" (BYOS) Filtering:** Because the extended metadata is treated as an opaque object, merchants can filter recommendations using their own custom attributes (e.g., "Filter by `color: 'Red'`") without any backend configuration changes.
*   **Data Privacy & Isolation:** Every store’s data is kept in a strictly separated "Collection," identified by a unique Store ID, ensuring no data leakage between merchants.

#### B. The Weighted Recommendation Logic
Our "User Interest" engine calculates what a customer wants by looking at their journey across three tiers of intent:

1.  **Purchased Products (High Weight):** The strongest signal of long-term preference.
2.  **Added to Cart (Medium Weight):** High intent for immediate purchase.
3.  **Viewed Products (Low Weight):** General interest and browsing "vibe."

By combining the vectors of these products, the system calculates a **"User Interest Vector."** It then finds the products in the store's catalog that are mathematically closest to this vector, delivering a highly personalized shopping experience.

---

### 4. Technical Architecture Highlights
*   **High Performance:** Built on **FastAPI**, ensuring ultra-low latency for real-time recommendations even during high-traffic sales events.
*   **Vector Engine (Qdrant):** We use **Qdrant** as our core vector database. It was chosen for its:
    *   **Advanced Payload Filtering:** Allows for extremely fast filtering using the store's custom JSON metadata (BYOS) without sacrificing search performance.
    *   **Native Multi-tenancy:** Uses a dedicated **Tenant Index** to ensure that every Shopify store's data is strictly isolated and secure.
    *   **Scalability:** Optimized for high-throughput environments, making it ideal for the high-volume traffic patterns of e-commerce.
*   **Seamless Integration:** Designed as a "plug-and-play" system that can be integrated into any Shopify storefront via a standard API.

---

### 5. Business Impact
*   **Increased Conversion:** By showing customers exactly what they are looking for (even if they don't know the name of it).
*   **Higher Average Order Value (AOV):** Through "Frequently Bought Together" and "Similar Product" suggestions that feel relevant, not random.
*   **Future-Proof:** As the store grows and more data is added, the semantic model becomes even more accurate without requiring manual rule-tuning.
