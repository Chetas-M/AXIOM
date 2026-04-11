from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from api.database import get_db

router = APIRouter(prefix="/signals", tags=["Signals"])

@router.get("/")
async def get_signals(
    ticker: Optional[str] = Query(None),
    signal_type: Optional[str] = Query(None, description="e.g. BUY, SELL, HOLD"),
    limit: int = Query(20, le=200),
    db: AsyncSession = Depends(get_db),
):
    filters = "WHERE 1=1"
    params = {}

    if ticker:
        filters += " AND ticker = :ticker"
        params["ticker"] = ticker.upper()
    if signal_type:
        filters += " AND signal_type = :signal_type"
        params["signal_type"] = signal_type.upper()

    sql = text(f"""
        SELECT ticker, signal_type, created_at as generated_at, confidence, narration as notes
        FROM signals
        {filters}
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    params["limit"] = limit

    result = await db.execute(sql, params)
    rows = result.mappings().all()
    return {"count": len(rows), "data": [dict(r) for r in rows]}
