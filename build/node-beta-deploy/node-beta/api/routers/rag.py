from fastapi import APIRouter, Depends
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from api.database import get_db
from storage.models import NewsArticle
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG"])

@router.get("/{ticker}")
async def rag_query(ticker: str, top_k: int = 5, max_age_hours: int = 48, db: AsyncSession = Depends(get_db)):
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
        articles = result.scalars().all()
        
        payloads = [
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
        return payloads
    except Exception as e:
        logger.error(f"Postgres search failed for {ticker}: {e}")
        return []
