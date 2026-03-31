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

### 3. How It Works: The "Tri-tier" Schema
To ensure maximum performance and logical separation of concerns, the system uses a **Tri-tier Structured Design**.

#### A. Core Identity
*   `store_id`: The mandatory partition key for tenant isolation.
*   `product_id`: The unique identifier for the product within a store.

#### B. Search Core (Top-level Vector Basis)
These fields define the "Digital Fingerprint" of the product and are used to generate the **Product Vector** via Jina AI.
*   `title`, `description`, `brand`, `category`, and `tags`.

#### C. Commerce Metadata (Nested Filter Basis)
Attributes used for business logic, filtering, and real-time state management are grouped into a nested `metadata` object. This ensures the Search Core remains clean.
*   **Numeric:** `price`, `discount`, `rating`, `weight`.
*   **Categorical:** `color`, `size`, `material`, `gender`, `season`, `collection`.
*   **State:** `is_available`.

---

### 4. Technical Architecture Highlights
*   **Nested Indexing:** Qdrant utilizes native nested payload indexing (e.g., `metadata.price`) for sub-millisecond filtering.
*   **Weighted User Intent:** Calculates a **"User Interest Vector"** by weighting interactions (Purchased: 5.0, Cart: 3.0, Viewed: 1.0).
*   **High Performance:** Built on **FastAPI** and **Qdrant**, optimized for real-time storefront environments.
*   **Tenant Isolation:** Strict data separation using mandatory partition keys.
