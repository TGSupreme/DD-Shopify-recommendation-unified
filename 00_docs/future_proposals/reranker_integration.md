# Future Proposal: Two-Stage Retrieval with Jina Reranker v2

> **STATUS: IMPLEMENTED** (As of April 2026)
> This architecture is now live and serves all semantic search requests.

## 1. Executive Summary
While the current vector-based search is excellent for broad retrieval, it occasionally misses fine-grained linguistic nuances (like negations or specific technical constraints). This proposal outlines a **Two-Stage Retrieval Architecture** that introduces a Cross-Encoder (Reranker) to surgically refine the top results before they reach the user.

---

## 2. The Problem: Vector "Blurriness"
Vector embeddings (Bi-Encoders) compress an entire product description into a single point in space. This is fast but leads to two specific issues:
*   **Loss of Detail**: Nuances like "Waterproof" vs. "Water-resistant" or "Includes batteries" vs. "Batteries not included" can be blurred.
*   **Keyword Negation**: A search for "Cotton but NOT blue" often returns blue cotton items because the vector contains both "blue" and "cotton."

---

## 3. The Solution: Two-Stage Funnel
Instead of showing the raw output of the vector search, we move to a high-precision funnel:

### Stage 1: Fast Retrieval (The Net)
*   **Tool**: Qdrant + Jina v2 Embeddings.
*   **Action**: Retrieve the **Top 50** candidates.
*   **Latency**: ~15ms.

### Stage 2: Neural Reranking (The Judge)
*   **Tool**: Jina Reranker v2 (Cross-Encoder).
*   **Action**: Perform token-to-token comparison between the Query and the 50 candidates.
*   **Latency**: ~80ms - 150ms.
*   **Outcome**: The most linguistically accurate result is moved to the #1 spot.

---

## 4. Architectural Flow
The Reranker sits between the initial database search and the final diversity re-ranking (MMR).

```text
[ User Query ] 
      |
      v
[ Qdrant Search ] ----> (Returns 50 candidates)
      |
      v
[ Jina Reranker ] ----> (Re-sorts 50 candidates for precision)
      |
      v
[ MMR Diversity ] ----> (Picks final 10 diverse items from top 20)
      |
      v
[ Final UI Result ]
```

---

## 5. Expected Impact
Based on industry benchmarks for Jina Reranker v2:
*   **Accuracy (NDCG@10)**: Expected increase of **20% to 30%**.
*   **Success Rate (MRR)**: Significant improvement in placing the "perfect" product at Rank #1.
*   **Conversion**: Higher precision leads to fewer "No results found" frustrations and increased click-through rates.

---

## 6. Technical Implementation Details
*   **Model**: `jina-reranker-v2-base-multilingual`
*   **API Endpoint**: `https://api.jina.ai/v1/rerank`
*   **Key Parameter**: `top_n=20` (Send 50 candidates, get back the sorted top 20).
*   **Resiliency**: If the Reranker API fails, the system should gracefully fall back to the raw Qdrant scores to ensure zero downtime.

---

## 7. Cost & Latency Trade-off
*   **Latency**: Increases total search time from ~30ms to ~130ms (well within the "instant" human perception threshold of 300ms).
*   **Cost**: Jina AI charges per-token for reranking, but because we only rerank the **Top 50** candidates, the cost remains highly manageable for production-scale Shopify stores.
