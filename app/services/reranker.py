import httpx
import logging
import time
from typing import List
from core.config import settings

logger = logging.getLogger(__name__)

class JinaReranker:
    """
    Implements a two-stage retrieval architecture using the Jina Reranker v2.
    Refines vector search results with a Cross-Encoder for higher precision.
    """
    def __init__(self):
        self.api_key = settings.JINA_API_KEY
        
        # Derive the reranker URL from the existing embedding URL
        # For example, "https://api.jina.ai/v1/embeddings" -> "https://api.jina.ai/v1/rerank"
        if settings.JINA_EMBEDDING_URL.endswith("/embeddings"):
            self.url = settings.JINA_EMBEDDING_URL[:-len("/embeddings")] + "/rerank"
        else:
            self.url = "https://api.jina.ai/v1/rerank"
            
        self.model = settings.JINA_RERANKER_MODEL
        
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            timeout=30.0
        )
        
        if not self.api_key:
            logger.warning("JINA_API_KEY is not set. Reranker requests will fail.")
        else:
            logger.info("Jina AI Reranker client initialized.")

    async def rerank(self, query: str, documents: List[str], top_n: int = 20) -> List[int]:
        """
        Reranks a list of documents against a query using Jina Reranker.
        Returns the original indices of the reranked documents in descending order of relevance.
        """
        if not self.api_key:
            logger.warning("JINA_API_KEY missing, skipping reranking.")
            # Fallback: keep original order up to top_n
            return list(range(min(len(documents), top_n)))
            
        if not documents:
            return []

        data = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "top_n": top_n
        }

        start_time = time.time()
        try:
            response = await self.client.post(self.url, json=data)
            response.raise_for_status()
            
            latency_ms = (time.time() - start_time) * 1000
            result = response.json()
            
            # The API returns an array of results with 'index' and 'relevance_score'
            # Sorted by relevance_score descending
            reranked_indices = [item["index"] for item in result.get("results", [])]
            
            usage = result.get("usage", {})
            logger.info(
                f"JINA RERANKER: "
                f"Latency={latency_ms:.2f}ms, "
                f"Tokens={usage.get('total_tokens', 'N/A')}, "
                f"Documents={len(documents)}"
            )
            
            return reranked_indices
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Jina AI Reranker API error ({e.response.status_code}): {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Jina reranking: {str(e)}")
            raise

    async def close(self):
        await self.client.aclose()

reranker_service = JinaReranker()
