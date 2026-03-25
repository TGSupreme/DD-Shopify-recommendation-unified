# Future Roadmap & Advanced Features

This document tracks features and technical requirements that are planned for future phases of the **Unified Shopify Recommendation Engine**. For the MVP, we are focusing on the core AI/Recommendation logic in an **"Auth-less/Trust Mode"** environment.

---

## 1. Security & Authentication
*   **API Key Management:** Implementation of a Two-Tier Key system (Public/Secret).
*   **OAuth Integration:** Handling the Shopify OAuth handshake to automatically register new stores.
*   **Account Management DB:** A relational database (PostgreSQL/SQLite) to store store metadata, API keys, and plan types.
*   **Request Middleware:** Validation of API keys for every request to ensure data isolation.

---

## 2. Shopify Platform Integration
*   **Webhook Listener:** Automated syncing of product data when a merchant adds, updates, or deletes an item in Shopify.
*   **App Proxy:** Securely routing storefront requests through Shopify to our FastAPI engine.
*   **Admin Dashboard:** A simple UI within the Shopify Admin for merchants to see their recommendation statistics.

---

## 3. Business & Monetization
*   **Subscription Logic:** Tiered access (e.g., Free, Basic, Pro) based on the number of products or monthly recommendation requests.
*   **Usage Analytics:** Tracking "Attributed Revenue" (how much money was made specifically from our recommendations).

---

## 4. Advanced AI Enhancements
*   **Image-Based Similarity:** Using Computer Vision (CLIP models) to recommend products that *look* similar, not just those with similar descriptions.
*   **A/B Testing Engine:** Allowing merchants to test different recommendation weights to see which performs better.
*   **Cold Start Logic:** Smart defaults for new visitors who have no interaction history.
