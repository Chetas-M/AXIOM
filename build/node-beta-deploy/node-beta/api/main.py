import os
import logging
from urllib.parse import urlparse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import ohlcv, news, signals, rag

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AXIOM Internal API",
    description="Financial intelligence data layer for node-beta",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

def _load_allowed_origins() -> list[str]:
    configured = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost,http://127.0.0.1")
    origins: list[str] = []
    for origin in (o.strip() for o in configured.split(",")):
        if not origin or origin == "*":
            if origin == "*":
                logger.warning("Ignoring wildcard origin '*' in CORS_ALLOW_ORIGINS")
            continue
        parsed = urlparse(origin)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            origins.append(origin)
        else:
            logger.warning("Ignoring invalid CORS origin '%s'", origin)
    return origins or ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]

allowed_origins = _load_allowed_origins()

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
