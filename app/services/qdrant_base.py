import logging
from typing import Optional
from qdrant_client import AsyncQdrantClient
from core.config import settings

logger = logging.getLogger(__name__)

class QdrantBaseService:
    """
    Base service for Qdrant operations. 
    Manages a shared singleton AsyncQdrantClient to optimize connection pooling.
    """
    _client: Optional[AsyncQdrantClient] = None

    def __init__(self):
        self.collection_name = settings.COLLECTION_NAME
        self.vector_size = settings.VECTOR_DIMENSION

    @property
    def client(self) -> AsyncQdrantClient:
        """Returns the shared singleton Qdrant client."""
        if QdrantBaseService._client is None:
            logger.info("Initializing shared AsyncQdrantClient singleton...")
            QdrantBaseService._client = AsyncQdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )
        return QdrantBaseService._client

    async def close(self):
        """Gracefully close the shared Qdrant client connection."""
        if QdrantBaseService._client:
            logger.info("Closing shared AsyncQdrantClient singleton...")
            await QdrantBaseService._client.close()
            QdrantBaseService._client = None
