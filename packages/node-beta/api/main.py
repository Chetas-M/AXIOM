import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import ohlcv, news, signals, rag

app = FastAPI(
    title="AXIOM Internal API",
    description="Financial intelligence data layer for node-beta",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

allowed_origins = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost,http://127.0.0.1").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(ohlcv.router)
app.include_router(news.router)
app.include_router(signals.router)
app.include_router(rag.router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "axiom-api"}

@app.get("/")
async def root():
    return {"message": "AXIOM API - see /docs for endpoints"}
