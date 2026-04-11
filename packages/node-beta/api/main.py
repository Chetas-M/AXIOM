from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import ohlcv, news, signals

app = FastAPI(
    title="AXIOM Internal API",
    description="Financial intelligence data layer for node-alpha",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(ohlcv.router)
app.include_router(news.router)
app.include_router(signals.router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "axiom-api"}

@app.get("/")
async def root():
    return {"message": "AXIOM API - see /docs for endpoints"}
