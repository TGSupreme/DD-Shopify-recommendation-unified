from fastapi import FastAPI
from api.sync import router as sync_router
from api.search import router as search_router
from api.recommend import router as recommend_router

app = FastAPI(title="Unified Shopify Recommendation Engine")

# Register Routers
app.include_router(sync_router, prefix="/sync", tags=["Sync"])
app.include_router(search_router, prefix="/search", tags=["Search"])
app.include_router(recommend_router, prefix="/recommend", tags=["Recommend"])

@app.get("/")
async def root():
    return {"message": "Unified Shopify Recommendation Engine API is running"}

if __name__ == "__main__":
    import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

