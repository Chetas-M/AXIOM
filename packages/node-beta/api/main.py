import os
import logging
from urllib.parse import urlparse
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import ohlcv, news, signals, rag
from api.auth import require_api_key

logger = logging.getLogger(__name__)
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app = FastAPI(
    title="AXIOM Internal API",
    description="Financial intelligence data layer for node-beta",
    version="0.1.0",
    docs_url="/docs" if os.getenv("AXIOM_ENABLE_DOCS", "").lower() in {"1", "true", "yes"} else None,
    redoc_url="/redoc" if os.getenv("AXIOM_ENABLE_DOCS", "").lower() in {"1", "true", "yes"} else None,
    openapi_url="/openapi.json" if os.getenv("AXIOM_ENABLE_DOCS", "").lower() in {"1", "true", "yes"} else None,
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
    return origins or DEFAULT_CORS_ORIGINS

allowed_origins = _load_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---- Protected routers (require AXIOM_API_KEY) ----
_auth = [Depends(require_api_key)]

app.include_router(ohlcv.router,   dependencies=_auth)
app.include_router(news.router,    dependencies=_auth)
app.include_router(signals.router, dependencies=_auth)
app.include_router(rag.router,     dependencies=_auth)

# ---- Intentionally public endpoints ----

@app.get("/health")
async def health():
    return {"status": "ok", "service": "axiom-api"}

@app.get("/")
async def root():
    if app.docs_url:
        return {"message": "AXIOM API - see /docs for endpoints"}
    return {"message": "AXIOM API"}
