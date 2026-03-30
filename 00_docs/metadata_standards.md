# Standardized Metadata Schema (V1)

This document defines the transition from **Bring Your Own Schema (BYOS)** to a **Standardized Metadata** architecture. By using a fixed set of high-probability keys, the system can provide optimized indexing, faster filtering, and a more predictable API for Shopify merchants.

---

## 1. Core Objectives
*   **Performance:** Create native Qdrant payload indexes (Keyword, Range, Boolean) for all standard keys.
*   **Validation:** Use Pydantic to enforce data types (e.g., ensuring `price` is always a float).
*   **Predictability:** Provide a clear "contract" for frontend developers on which fields are available for filtering and sorting.

---

## 2. Standardized Field Definitions

These fields are considered **"First-Class"** attributes. If provided by the merchant during synchronization, they will be indexed at the root level of the product payload for maximum performance.

### A. Categorical Attributes (Keyword Indexing)
*Used for exact matches, "Match Any" (OR) logic, and dropdown filters.*

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `product_type` | String | e.g., "Sweatshirt", "Analog Watch" |
| `collection` | String | The primary collection name/handle |
| `color` | String | e.g., "Midnight Blue", "Forest Green" |
| `size` | String | e.g., "XL", "42", "6.5" |
| `material` | String | e.g., "100% Organic Cotton", "Stainless Steel" |
| `gender` | String | `Men`, `Women`, `Unisex`, `Kids` |
| `age_group` | String | `Adult`, `Toddler`, `Infant` |
| `season` | String | e.g., "Spring", "Summer", "Holiday 2026" |
| `tags` | List[String] | Array of Shopify tags for exact filtering |

### B. Numeric Attributes (Range Indexing)
*Used for "Greater Than", "Less Than", and Price Sliders.*

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `price` | Float | The current selling price |
| `discount` | Float | Percentage or absolute value (merchant-dependent) |
| `rating` | Float | 0.0 to 5.0 score |
| `weight` | Float | Product weight for shipping calculations |

### C. State Attributes (Boolean Indexing)
*Used for simple toggle filters.*

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `is_available` | Boolean | `True` if in stock, `False` otherwise |

---

## 3. Implementation Strategy (Next Phase)

1.  **Schema Update:** Update `ProductUpsert` in `app/models/schemas.py` to move these fields from the generic `metadata` dictionary to explicit optional fields.
2.  **Indexing:** Update `ensure_collection` in `app/services/qdrant.py` to automatically create `models.KeywordIndexParams` and `models.RangeIndexParams` for these specific keys.
3.  **Ingestion:** Update `sync_products` in `app/api/sync.py` to map incoming data to these root-level payload fields.
4.  **Filter Utility:** Simplify `translate_filters` in `app/utils/filters.py` to prioritize these standardized keys, eliminating the need for `metadata.` prefixing for core commerce data.

---

## 4. Strict Schema Enforcement
To ensure sub-millisecond performance across millions of products, the engine enforces a **Strict Schema**. 

*   **No Unindexed Data:** The `extra_metadata` bucket has been removed. Only the standardized fields defined in Section 2 are stored and searchable.
*   **Performance Guarantee:** Because every stored field has a corresponding native Qdrant index, the system avoids slow "full-scan" filtering, ensuring that every discovery request is executed against an optimized index.
*   **Merchant Mapping:** Merchants are responsible for mapping their store-specific attributes (e.g., custom Shopify metafields) to the most relevant standardized keys during the synchronization process.
