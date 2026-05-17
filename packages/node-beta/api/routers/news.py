from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from api.database import get_db
from api.routers._params import OptionalTickerQueryParam

router = APIRouter(prefix="/news", tags=["News"])

@router.get("/")
async def get_news(
    ticker: OptionalTickerQueryParam,
    source: str | None = Query(None),
    limit: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    filters = "WHERE 1=1"
    params = {}

    ticker = ticker.upper() if ticker else None
    if ticker:
        filters += " AND ticker = :ticker"
        params["ticker"] = ticker
    if source:
        filters += " AND source ILIKE :source"
        params["source"] = f"%{source}%"

    sql = text(f"""
        SELECT id, headline, url, source, ticker, published_at, body_snippet
        FROM news_articles
        {filters}
        ORDER BY published_at DESC
        LIMIT :limit
    """)
    params["limit"] = limit

    result = await db.execute(sql, params)
    rows = result.mappings().all()
    return {"count": len(rows), "data": [dict(r) for r in rows]}
