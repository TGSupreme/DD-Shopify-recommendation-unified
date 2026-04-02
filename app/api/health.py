from fastapi import APIRouter
from models.schemas import HealthResponse, JinaHealth, QdrantHealth, DependenciesHealth
from services.embedding import embedding_service
from services.qdrant import qdrant_service
import asyncio

router = APIRouter()

@router.get("/", response_model=HealthResponse)
async def get_health():
    """
    Detailed health check endpoint assessing Jina AI latency and Qdrant segment health.
    """
    jina_result, qdrant_result = await asyncio.gather(
        embedding_service.check_health(),
        qdrant_service.check_health()
    )

    system_status = "healthy"
    if jina_result.get("status") != "healthy" or qdrant_result.get("status") not in ("green", "ok"):
        system_status = "degraded"

    return HealthResponse(
        system=system_status,
        dependencies=DependenciesHealth(
            jina_ai=JinaHealth(
                status=jina_result.get("status", "unknown"),
                latency_ms=jina_result.get("latency_ms", 0.0)
            ),
            qdrant=QdrantHealth(
                status=qdrant_result.get("status", "unknown"),
                optimizer_status=qdrant_result.get("optimizer_status", "unknown"),
                segments_count=qdrant_result.get("segments_count", 0)
            )
        )
    )
