from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Qdrant Configuration
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    
    # Jina AI Configuration
    JINA_API_KEY: Optional[str] = None
    JINA_EMBEDDING_URL: str = "https://api.jina.ai/v1/embeddings"
    JINA_EMBEDDING_MODEL: str = "jina-embeddings-v2-base-en"
    
    # Recommendation Weights
    WEIGHT_VIEW: float = 1.0
    WEIGHT_CART: float = 3.0
    WEIGHT_PURCHASE: float = 5.0
    
    # System Configuration
    VECTOR_DIMENSION: int = 768
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
