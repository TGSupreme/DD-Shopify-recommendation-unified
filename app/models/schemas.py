from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class EmbeddingSource(BaseModel):
    title: str
    brand: Optional[str] = ""
    category: Optional[str] = ""
    description: Optional[str] = ""
    tags: Optional[List[str]] = []

class ProductUpsert(BaseModel):
    product_id: str
    embedding_source: EmbeddingSource
    metadata: Optional[Dict[str, Any]] = {}

class SyncResponse(BaseModel):
    status: str
    message: str
    count: Optional[int] = 0

class SearchRequest(BaseModel):
    query_text: Optional[str] = None
    filters: Optional[Dict[str, Any]] = {}
    limit: Optional[int] = 10

class ProductResponse(BaseModel):
    product_id: str
    score: float

class SearchResponse(BaseModel):
    status: str
    results: List[ProductResponse]
