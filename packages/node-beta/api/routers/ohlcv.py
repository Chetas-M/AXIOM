from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import date
from typing import Optional
from api.database import get_db

router = APIRouter(prefix="/ohlcv", tags=["OHLCV"])

@router.get("/")
async def get_ohlcv(
    ticker: str = Query(..., description="NSE ticker e.g. RELIANCE"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    limit: int = Query(30, le=500),
    db: AsyncSession = Depends(get_db),
):
    filters = "WHERE ticker = :ticker"
    params = {"ticker": ticker.upper()}

    if from_date:
        filters += " AND date >= :from_date"
        params["from_date"] = from_date
    if to_date:
        filters += " AND date <= :to_date"
        params["to_date"] = to_date

    sql = text(f"""
        SELECT ticker, date, open, high, low, close, volume
        FROM ohlcv
        {filters}
        ORDER BY date DESC
        LIMIT :limit
    """)
    params["limit"] = limit

    result = await db.execute(sql, params)
    rows = result.mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No OHLCV data for {ticker}")

    return {"ticker": ticker.upper(), "count": len(rows), "data": [dict(r) for r in rows]}

@router.get("/latest")
async def get_latest_prices(db: AsyncSession = Depends(get_db)):
    sql = text("""
        SELECT DISTINCT ON (ticker) ticker, date, close, volume
        FROM ohlcv
        ORDER BY ticker, date DESC
    """)
    result = await db.execute(sql)
    rows = result.mappings().all()
    return {"count": len(rows), "data": [dict(r) for r in rows]}
