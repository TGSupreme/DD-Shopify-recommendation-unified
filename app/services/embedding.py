import httpx
import logging
import time
from typing import List
from core.config import settings

logger = logging.getLogger(__name__)

class JinaEmbeddings:
    """
    Phase 2: Implementing vectorization via Jina AI API.
    """
    def __init__(self):
        self.api_key = settings.JINA_API_KEY
        self.url = settings.JINA_EMBEDDING_URL
        self.model = settings.JINA_EMBEDDING_MODEL
        
        # Persistent client with authentication headers
        self.client = httpx.AsyncClient(
            base_url=self.url,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            timeout=30.0
        )
        
        if not self.api_key:
            logger.warning("JINA_API_KEY is not set. Embedding service requests will fail.")
        else:
            logger.info("Jina AI Embedding client initialized.")

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Batch vectorizes text fields via Jina AI.
        LOG: Jina API latency and token usage.
        """
        if not self.api_key:
            raise ValueError("JINA_API_KEY is not configured.")

        data = {
            "model": self.model,
            "input": texts
        }

        start_time = time.time()
        try:
            # We use '/' as the base_url is the full URL in config, or we can adjust
            response = await self.client.post("/embeddings", json=data)
            response.raise_for_status()
            
            latency_ms = (time.time() - start_time) * 1000
            result = response.json()
            
            embeddings = [item["embedding"] for item in result["data"]]
            usage = result.get("usage", {})
            
            logger.info(
                f"JINA VECTORIZATION: "
                f"Latency={latency_ms:.2f}ms, "
                f"Tokens={usage.get('total_tokens', 'N/A')}, "
                f"Count={len(texts)}"
            )
            
            return embeddings
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Jina AI API error ({e.response.status_code}): {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Jina vectorization: {str(e)}")
            raise

    async def check_health(self) -> dict:
        """
        Checks Jina AI API health by measuring latency for a minimal request.
        """
        if not self.api_key:
            return {"status": "unhealthy", "latency_ms": 0.0, "error": "API Key missing"}
        
        start_time = time.time()
        try:
            data = {"model": self.model, "input": ["health_check"]}
            response = await self.client.post("/embeddings", json=data)
            response.raise_for_status()
            latency = (time.time() - start_time) * 1000
            return {"status": "healthy", "latency_ms": round(latency, 2)}
        except Exception as e:
            logger.error(f"Jina AI health check failed: {str(e)}")
            return {"status": "unhealthy", "latency_ms": 0.0, "error": str(e)}

    async def close(self):
        await self.client.aclose()

embedding_service = JinaEmbeddings()
