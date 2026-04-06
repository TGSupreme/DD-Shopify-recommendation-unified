# Future Proposal: Functional Complementary Logic (The "Semantic Donut")

## 1. Executive Summary
Current complementary recommendations rely on the `category` field to exclude substitutes (e.g., excluding other "Shoes" when looking at "Sneakers"). However, merchant category data is often inconsistent and ambiguous across different stores. This proposal introduces a **Vector-Based Functional Exclusion** strategy that identifies and filters out "Functional Redundancy" using semantic meaning rather than exact category names.

---

## 2. The Problem: The "Category Trap"
In a unified system, relying on categories fails for two reasons:
1.  **Linguistic Ambiguity**: One merchant uses "Footwear," another uses "Women-Shoes." The system fails to realize they are the same thing.
2.  **Flat Taxonomy**: Large stores often have thousands of low-level categories, making it impossible to maintain a "Universal Exclusion List."

---

## 3. The Solution: Two-Vector "Semantic Donut"
Instead of a single product vector, we introduce a second vector representing the **Functional Purpose** of the item.

### Stage A: The "Purpose Statement" (Sync Phase)
During ingestion, a Small Language Model (SLM) analyzes the product and generates a concise **Purpose Statement**:
*   *Example (Nike Sneakers)*: "Protective footwear used for support and mobility during physical activity."
*   *Example (Power Drill)*: "A hand-held tool used for creating holes and driving fasteners into materials."

### Stage B: Purpose Vectorization
This statement is converted into a 768-dim **Purpose Vector** and stored in Qdrant alongside the standard **Search Vector** (Title, Brand, Vibe).

---

## 4. The "Complementary" Query Logic
To "Complete the Look" or "Finish the Project," the engine executes a query with two mathematical rules:

1.  **Rule 1 (Contextual Match - POSITIVE)**: Find items where the **Search Vector** is similar to the target (Matches style, brand, and aesthetic).
2.  **Rule 2 (Functional Exclusion - NEGATIVE)**: Exclude or heavily penalize items where the **Purpose Vector** similarity is **> 0.85** (Filters out items that do the same thing).

### Expected Result:
*   **Target**: "Running Shoes"
*   **Matches**: "Gym Bag" (Similar Search Vector / Different Purpose Vector) -> **SHOWN**
*   **Matches**: "Running Shorts" (Similar Search Vector / Different Purpose Vector) -> **SHOWN**
*   **Matches**: "Tennis Shoes" (Similar Search Vector / **Identical Purpose Vector**) -> **EXCLUDED**

---

## 5. Technical Implementation Steps
1.  **Multi-Vector Support**: Update the Qdrant collection to support multiple named vectors (e.g., `search_vector` and `purpose_vector`).
2.  **Enrichment Step**: Add a step in `IndexerService` to call an SLM (e.g., Gemma 4) to generate the Purpose Statement.
3.  **Discovery Update**: Modify `get_complementary_products` to use the `query_points` API with a multi-vector query that balances similarity and functional diversity.

---

## 6. Key Advantages
*   **Store-Agnostic**: Works for Fashion, Electronics, Home Decor, or Industrial parts without any manual category mapping.
*   **Autonomous**: No more "Garbage In, Garbage Out" from merchant data; the AI defines the functional relationship.
*   **Unified Precision**: Solves the "Women-Shoes" vs. "Footwear" problem automatically through vector distance.
