# SLM Integration Strategy: Gemma 4 for Shopify Recommendation Engine

## 1. Executive Summary
As of April 2026, the release of the **Gemma 4** family (E2B/E4B) provides a high-efficiency path to solving the "Garbage In, Garbage Out" problem in vector search. By integrating these Small Language Models (SLMs) as a local side-car service, we can perform deep semantic data cleaning and "Stylist-grade" complementary logic during the ingestion phase with sub-100ms latency and zero per-token costs.

---

## 2. Proposed Models
| Model | Size | Role in System | Key Strength |
| :--- | :--- | :--- | :--- |
| **Gemma 4 E2B** | 2.3B | **Data Cleaning & Normalization** | Ultra-low latency on CPU/low-end GPU. |
| **Gemma 4 E4B** | 4.5B | **Stylist Logic (Complementary)** | Better reasoning for fashion/lifestyle pairings. |

---

## 3. The "In-Step" Enrichment Pipeline
Currently, the system vectorizes raw Shopify data. The new strategy introduces an **Enrichment Layer** inside the `IndexerService` during the `Sync` process.

### Phase A: Data Cleaning (E2B)
*   **Problem**: Shopify product descriptions often contain messy HTML, internal SKU codes, and irrelevant SEO keywords.
*   **Solution**: E2B strips noise and rewrites the product description into a "Search-Optimized Fingerprint."
*   **Outcome**: Jina AI generates higher-quality vectors, leading to more accurate search results.

### Phase B: Stylist Logic (E4B)
*   **Problem**: Complementary logic currently relies on "Similarity + Category Exclusion," which is a guess.
*   **Solution**: During sync, E4B analyzes the product and generates a list of `complementary_cues`.
    *   *Example*: For a "Navy Blazer," E4B generates: `["Tan Chinos", "White Oxford Shirt", "Loafers"]`.
*   **Outcome**: These cues are stored in the Qdrant metadata. At query time, the system performs a high-speed keyword filter instead of a speculative vector search.

---

## 4. Architectural Implementation
To ensure **Ultra-Low Latency**, the SLM must reside on the same server as the FastAPI application.

### Localhost Communication
1.  **FastAPI** receives products via `/sync`.
2.  **FastAPI** calls **Ollama** (Gemma 4) via `http://localhost:11434`.
3.  **FastAPI** sends cleaned text to **Jina AI** (External).
4.  **FastAPI** saves the final record to **Qdrant** (Localhost).

### Logic Flow
```python
# Pseudo-code for Enriched Ingestion
async def sync_products(products):
    for p in products:
        # 1. Clean & Extract Attributes (Gemma 4 E2B)
        p.cleaned_text = await gemma.clean(p.description)
        
        # 2. Generate Style Pairings (Gemma 4 E4B)
        p.metadata.style_pairings = await gemma.get_pairings(p.title)
        
        # 3. Vectorize ONLY the clean text
        p.vector = await jina.embed(p.cleaned_text)
        
    await qdrant.upsert(products)
```

---

## 5. Deployment & Hardware
*   **Runtime**: [Ollama](https://ollama.com) or `llama-cpp-python`.
*   **Memory Usage**: 
    *   E2B (4-bit): ~1.6 GB RAM.
    *   E4B (4-bit): ~3.1 GB RAM.
*   **Compute**: 
    *   *Minimum*: 4-core modern CPU.
    *   *Recommended*: Small NVIDIA GPU (T4, 3060) or Mac M-series for "instant" processing.

---

## 6. Key Benefits
1.  **Zero Cost Scaling**: No per-token fees for cleaning millions of products.
2.  **Privacy**: Sensitive product data/descriptions never leave the server for processing.
3.  **Deterministic Logic**: Merchants get "Amazon-level" Frequently Bought Together logic without needing massive purchase history.
4.  **Resiliency**: The cleaning layer acts as a buffer, ensuring only high-quality data enters the vector index.
