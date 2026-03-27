from qdrant_client import AsyncQdrantClient
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class QdrantService:
    """
    Phase 1: Qdrant client initialization.
    """
    def __init__(self):
        self.client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        logger.info(f"Qdrant client initialized at {settings.QDRANT_URL}")

qdrant_service = QdrantService()
