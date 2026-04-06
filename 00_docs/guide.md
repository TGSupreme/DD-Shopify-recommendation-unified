# SHAPIFY AI: Merchant Best Practices & Data Quality Guide

This guide outlines how to ensure your store delivers the best possible AI-driven recommendations and search results for your customers.

---

## 1. The “Digital Fingerprint”: What the AI Needs to See

Unlike traditional search engines that rely on exact keyword matches, our AI understands the *meaning* behind your products. To do this effectively, it creates a **Digital Fingerprint** using your core product data.

### Advisable (The “Gold Standard”)

* **Title:** Use clear, descriptive names.
  Example: “Men’s Lightweight Waterproof Trail Runner” is far better than “Trail Shoe v2.”

* **Description:** Provide at least 2–3 sentences.
  Include materials, use cases, and unique selling points. The AI uses this to identify conceptual matches.

* **Category & Brand:** Ensure accuracy.
  These help the AI understand context (e.g., distinguishing “Apple” the fruit from “Apple” the tech brand).

* **Tags:** Add stylistic or functional attributes not covered in the title.
  Examples: “minimalist,” “vintage,” “eco-friendly.”

### Required (Minimum Criteria)

* Every product must include:

  * A **Title**
  * A **unique Product ID**
    Without these, the product cannot be indexed or tracked.

---

## 2. Commerce Metadata: Powering Smart Filters

Metadata doesn’t define *what* a product is—it controls *when* and *how* it appears.

* **Price & Availability:** Essential for a good customer experience.
  Avoid recommending out-of-stock or irrelevant price-range items.

* **Attributes (Color, Size, Material):**
  These enable precise filtering.
  Example: “Show similar shoes, but only in Size 10.”

---

## 3. User Interactions: The Engine of Personalization

The system learns customer preferences by analyzing behavior using a weighted model:

* **Purchase (Weight: 5.0):** Strongest signal of intent
* **Add to Cart (Weight: 3.0):** High interest or consideration
* **View (Weight: 1.0):** General interest

As more interactions are tracked, the **User Interest Vector** evolves to better reflect individual preferences.

---

## 4. Why You Might Get “Bad” Recommendations

If recommendations appear irrelevant or repetitive, it’s usually due to one of these common data issues:

### A. The “Thin Content” Trap

* **Cause:** Titles are vague (e.g., “SKU-9921”) and descriptions are missing
* **Effect:** The AI lacks meaningful context and returns broad or random matches

### B. The “Cold Start” Problem

* **Cause:** New store or new product with no interaction data
* **Effect:** Recommendations remain generic until user activity is recorded

### C. The “Narrow Catalog” Cluster

* **Cause:** Very limited or highly similar product range
* **Effect:** Difficulty generating diverse recommendations
  (Note: MMR diversity helps, but requires variety to work effectively.)

### D. Stale Data

* **Cause:** Outdated product metadata (price, stock, etc.)
* **Effect:** Inaccurate recommendations (e.g., wrong price or unavailable items)

---

## 5. Summary Checklist for Merchants

* [ ] Are my product titles clear and descriptive?
* [ ] Do my key products have rich, detailed descriptions?
* [ ] Is availability updated in real time?
* [ ] Am I correctly tracking views, cart additions, and purchases?
