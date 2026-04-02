import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.sync import router as sync_router
from api.search import router as search_router
from api.recommend import router as recommend_router
from api.admin import router as admin_router
from api.health import router as health_router
from services.qdrant import qdrant_service
from core.config import settings
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from utils.limiter import limiter
from fastapi.responses import PlainTextResponse

# Configure Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Pre-initialize Qdrant Collection and Indexes
    logger.info("SYSTEM STARTUP: Validating Qdrant Connection...")
    try:
        await qdrant_service.ensure_collection(settings.COLLECTION_NAME)
        logger.info(f"SYSTEM READY: Shared collection '{settings.COLLECTION_NAME}' is active and optimized.")
    except Exception as e:
        logger.error(f"SYSTEM CRITICAL: Failed to initialize Qdrant at startup: {str(e)}")
    
    yield
    
    # SHUTDOWN: Clean up resources if needed
    logger.info("SYSTEM SHUTDOWN: Closing connections...")
    await qdrant_service.client.close()

app = FastAPI(
    title="Unified Shopify Recommendation Engine",
    lifespan=lifespan
)

# Initialize Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Register Routers
app.include_router(sync_router, prefix="/sync", tags=["Sync"])
app.include_router(search_router, prefix="/search", tags=["Search"])
app.include_router(recommend_router, prefix="/recommend", tags=["Recommend"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(health_router, prefix="/health", tags=["Health"])

@app.get("/")
async def root():
    logger.info("Root endpoint accessed.")
    return {"message": "Unified Shopify Recommendation Engine API is running - Standardized Multi-tenant Core Active"}

@app.get("/ping",response_class=PlainTextResponse)
async def ping():
    return "Server is alive."

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
