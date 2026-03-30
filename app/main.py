import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.sync import router as sync_router
from api.search import router as search_router
from api.recommend import router as recommend_router
from services.qdrant import qdrant_service
from core.config import settings

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
    logger.info("SYSTEM STARTUP: Validating Qdrant Connection...")
    try:
        await qdrant_service.ensure_collection(settings.COLLECTION_NAME)
        logger.info(f"SYSTEM READY: Shared collection '{settings.COLLECTION_NAME}' is active and optimized.")
    except Exception as e:
        logger.error(f"SYSTEM CRITICAL: Failed to initialize Qdrant at startup: {str(e)}")

    yield

    logger.info("SYSTEM SHUTDOWN: Closing connections...")
    await qdrant_service.client.close()

app = FastAPI(
    title="Unified Shopify Recommendation Engine",
    lifespan=lifespan
)

# Register Routers
app.include_router(sync_router, prefix="/sync", tags=["Sync"])
app.include_router(search_router, prefix="/search", tags=["Search"])
app.include_router(recommend_router, prefix="/recommend", tags=["Recommend"])

@app.get("/")
async def root():
    logger.info("Root endpoint accessed.")
    return {"message": "Unified Shopify Recommendation Engine API is running - Standardized Multi-tenant Core Active"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
