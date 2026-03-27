import httpx
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class JinaEmbeddings:
    """
    Phase 1: Jina AI Embedding client initialization using HTTPX.
    Handles the lifecycle of the asynchronous HTTP client.
    """
    def __init__(self):
        self.api_key = settings.JINA_API_KEY
        self.url = settings.JINA_EMBEDDING_URL
        self.model = settings.JINA_EMBEDDING_MODEL
        
        # Initialize the AsyncClient but don't open it yet
        # In a real FastAPI app, you might manage this in lifespan events
        self.client = httpx.AsyncClient(
            base_url=self.url,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            timeout=30.0
        )
        
        if not self.api_key:
            logger.warning("JINA_API_KEY is not set. Embedding service requests will fail.")
        else:
            logger.info("Jina AI Embedding (HTTPX) client initialized.")

    async def close(self):
        """Close the underlying HTTPX client."""
        await self.client.aclose()

embedding_service = JinaEmbeddings()
