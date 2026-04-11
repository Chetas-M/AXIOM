from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from api.database import get_db

router = APIRouter(prefix="/news", tags=["News"])

@router.get("/")
async def get_news(
    ticker: Optional[str] = Query(None, description="Filter by ticker (optional)"),
    source: Optional[str] = Query(None),
    limit: int = Query(20, le=200),
    db: AsyncSession = Depends(get_db),
):
    filters = "WHERE 1=1"
    params = {}

    if ticker:
        filters += " AND ticker = :ticker"
        params["ticker"] = ticker.upper()
    if source:
        filters += " AND source ILIKE :source"
        params["source"] = f"%{source}%"

    sql = text(f"""
        SELECT id, title, url, source, ticker, published_at, summary
        FROM news_articles
        {filters}
        ORDER BY published_at DESC
        LIMIT :limit
    """)
    params["limit"] = limit

    result = await db.execute(sql, params)
    rows = result.mappings().all()
    return {"count": len(rows), "data": [dict(r) for r in rows]}
