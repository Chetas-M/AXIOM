from fastapi import APIRouter, Depends, HTTPException, Path, Query
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.exc import SQLAlchemyError
from api.database import get_db
from storage.models import NewsArticle
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG"])

@router.get("/{ticker}")
async def rag_query(
    ticker: str = Path(..., min_length=1, max_length=20, pattern=r"^[A-Za-z0-9&._-]+$"),
    top_k: int = Query(5, ge=1, le=50),
    max_age_hours: int = Query(48, ge=1, le=336),
    db: AsyncSession = Depends(get_db),
):
    cutoff_timestamp = int(time.time()) - (max_age_hours * 3600)
    ticker = ticker.upper()
    
    stmt = (
        select(NewsArticle)
        .where(
            or_(NewsArticle.ticker == ticker, NewsArticle.ticker == "GENERAL", NewsArticle.ticker.is_(None)),
            NewsArticle.published_at >= cutoff_timestamp
        )
        .order_by(NewsArticle.published_at.desc())
        .limit(top_k)
    )
    
    try:
        result = await db.execute(stmt)
    except SQLAlchemyError:
        logger.exception("Postgres RAG search failed for %s", ticker)
        raise HTTPException(status_code=503, detail="RAG backend unavailable")

    articles = result.scalars().all()
    return [
        {
            "id": a.id,
            "ticker": a.ticker,
            "headline": a.headline,
            "body_snippet": a.body_snippet,
            "source": a.source,
            "url": a.url,
            "published_at": a.published_at,
        }
        for a in articles
    ]
