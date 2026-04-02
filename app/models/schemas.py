from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ProductMetadata(BaseModel):
    # Numeric Attributes (Indexed as Range)
    price: Optional[float] = None
    discount: Optional[float] = None
    rating: Optional[float] = None
    weight: Optional[float] = None
    
    # Variant / Physical Attributes (Indexed as Keyword)
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None
    gender: Optional[str] = None
    age_group: Optional[str] = None
    season: Optional[str] = None
    collection: Optional[str] = None
    
    # State Attributes (Indexed as Boolean)
    is_available: bool = True

class ProductUpsert(BaseModel):
    # 1. Core Identity
    product_id: str
    
    # 2. Search Core (Top-level fields used for Vectorization)
    title: str
    description: Optional[str] = ""
    brand: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # 3. Commerce Metadata (Nested object for Filtering)
    metadata: ProductMetadata

class SyncResponse(BaseModel):
    status: str
    message: str
    count: Optional[int] = 0

class DebugRequest(BaseModel):
    product_ids: List[str]

class SearchRequest(BaseModel):
    query_text: str # Query text is required for semantic search
    filters: Optional[Dict[str, Any]] = {}
    limit: Optional[int] = 10
    diversity_penalty: float = Field(default=0.0, ge=0.0, le=1.0)

class SimilarRequest(BaseModel):
    filters: Optional[Dict[str, Any]] = {}
    limit: Optional[int] = 10
    diversity_penalty: float = Field(default=0.0, ge=0.0, le=1.0)

class RecommendRequest(BaseModel):
    viewed_ids: Optional[List[str]] = Field(default_factory=list)
    added_to_cart_ids: Optional[List[str]] = Field(default_factory=list)
    purchased_ids: Optional[List[str]] = Field(default_factory=list)
    filters: Optional[Dict[str, Any]] = {}
    limit: Optional[int] = 10
    diversity_penalty: float = Field(default=0.0, ge=0.0, le=1.0)

class ProductResponse(BaseModel):
    product_id: str
    score: float

class SearchResponse(BaseModel):
    status: str
    results: List[ProductResponse]

class StoreStatsResponse(BaseModel):
    store_id: str
    product_count: int
    status: str = "active"

class SystemInfo(BaseModel):
    version: str
    status: str
    uptime_status: str

class CollectionMetrics(BaseModel):
    name: str
    total_points: int
    indexed_vectors: int
    segments_count: int
    optimizer_status: str
    vectors_config: Dict[str, Any]

class TenantInsight(BaseModel):
    total_active_stores: int
    top_5_tenants: List[Dict[str, Any]]

class SystemStatsResponse(BaseModel):
    system: SystemInfo
    collection_metrics: CollectionMetrics
    tenant_insight: TenantInsight

class JinaHealth(BaseModel):
    status: str
    latency_ms: float

class QdrantHealth(BaseModel):
    status: str
    optimizer_status: str
    segments_count: int

class DependenciesHealth(BaseModel):
    jina_ai: JinaHealth
    qdrant: QdrantHealth

class HealthResponse(BaseModel):
    system: str
    dependencies: DependenciesHealth
