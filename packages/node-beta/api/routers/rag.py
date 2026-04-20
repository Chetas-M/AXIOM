from fastapi import APIRouter, Depends
import requests
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from qdrant_client.http.models import Filter, FieldCondition, MatchAny, Range
from storage.qdrant_client import get_qdrant_client
from api.database import get_db
from storage.models import NewsArticle
import logging
import sys
import os

# Add shared to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from axiom_shared.config import VECTOR_BACKEND

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG"])

async def get_context_for_ticker_pgvector(ticker: str, db: AsyncSession, top_k: int = 5, max_age_hours: int = 48) -> list[dict]:
    query_str = f"{ticker} NSE stock news earnings"
    
    # 1. Embed query
    try:
        resp = requests.post(
            "http://node-alpha:11434/api/embeddings", 
            json={"model": "nomic-embed-text", "prompt": query_str},
            timeout=10
        )
        if not resp.ok:
            logger.warning(f"Ollama embedding failed for query: {query_str}")
            return []
        vec = resp.json().get("embedding")
        if not vec:
            return []
    except Exception as e:
        logger.warning(f"Failed to connect to Ollama for embedding: {e}")
        return []

    # 2. Search PGVector
    cutoff_timestamp = int(time.time()) - (max_age_hours * 3600)
    
    # Use pgvector cosine distance `<=>` operator (or `<->` for L2, but we configured cosine index with vector_cosine_ops)
    stmt = (
        select(NewsArticle)
        .where(
            NewsArticle.embedding.is_not(None),
            or_(NewsArticle.ticker == ticker, NewsArticle.ticker == "GENERAL", NewsArticle.ticker.is_(None)),
            NewsArticle.published_at >= cutoff_timestamp
        )
        .order_by(NewsArticle.embedding.cosine_distance(vec))
        .limit(top_k)
    )
    
    try:
        result = await db.execute(stmt)
        articles = result.scalars().all()
        
        # 3. Format as payload
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
        logger.error(f"PGVector search failed for {ticker}: {e}")
        return []

def get_context_for_ticker_qdrant(ticker: str, top_k: int = 5, max_age_hours: int = 48) -> list[dict]:
    client = get_qdrant_client()
    query_str = f"{ticker} NSE stock news earnings"
    
    # 1. Embed query
    try:
        resp = requests.post(
            "http://node-alpha:11434/api/embeddings", 
            json={"model": "nomic-embed-text", "prompt": query_str},
            timeout=10
        )
        if not resp.ok:
            logger.warning(f"Ollama embedding failed for query: {query_str}")
            return []
        vec = resp.json().get("embedding")
        if not vec:
            return []
    except Exception as e:
        logger.warning(f"Failed to connect to Ollama for embedding: {e}")
        return []

    # 2. Build filter
    cutoff_timestamp = int(time.time()) - (max_age_hours * 3600)
    
    query_filter = Filter(
        must=[
            FieldCondition(
                key="ticker",
                match=MatchAny(any=[ticker, "GENERAL"])
            ),
            FieldCondition(
                key="published_at",
                range=Range(gte=cutoff_timestamp)
            )
        ]
    )

    # 3. Search Qdrant
    try:
        search_result = client.search(
            collection_name="news_docs",
            query_vector=vec,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True
        )
        
        # return sorted by score desc (Qdrant handles this natively)
        payloads = [hit.payload for hit in search_result if hit.payload]
        return payloads
    except Exception as e:
        logger.error(f"Qdrant search failed for {ticker}: {e}")
        return []


@router.get("/{ticker}")
async def rag_query(ticker: str, top_k: int = 5, max_age_hours: int = 48, db: AsyncSession = Depends(get_db)):
    if VECTOR_BACKEND == "pgvector":
        payloads = await get_context_for_ticker_pgvector(ticker, db, top_k, max_age_hours)
    else:
        # Wrap synchronous Qdrant fallback 
        payloads = get_context_for_ticker_qdrant(ticker, top_k, max_age_hours)
    return payloads
