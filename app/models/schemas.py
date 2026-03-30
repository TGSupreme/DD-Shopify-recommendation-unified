from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ProductUpsert(BaseModel):
    product_id: str
    title: str
    description: Optional[str] = ""
    
    # Categorical Attributes (Indexed as Keyword)
    brand: Optional[str] = None
    category: Optional[str] = None
    product_type: Optional[str] = None
    collection: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None
    gender: Optional[str] = None
    age_group: Optional[str] = None
    season: Optional[str] = None
    
    # Numeric Attributes (Indexed as Range)
    price: Optional[float] = None
    discount: Optional[float] = None
    rating: Optional[float] = None
    weight: Optional[float] = None
    
    # State Attributes (Indexed as Boolean)
    is_available: Optional[bool] = True

class SyncResponse(BaseModel):
    status: str
    message: str
    count: Optional[int] = 0

class SearchRequest(BaseModel):
    query_text: str # Query text is required for semantic search
    filters: Optional[Dict[str, Any]] = {}
    limit: Optional[int] = 10

class SimilarRequest(BaseModel):
    filters: Optional[Dict[str, Any]] = {}
    limit: Optional[int] = 10

class ProductResponse(BaseModel):
    product_id: str
    score: float

class SearchResponse(BaseModel):
    status: str
    results: List[ProductResponse]
