from fastapi import APIRouter
import requests
import time
from qdrant_client.http.models import Filter, FieldCondition, MatchAny, Range
from storage.qdrant_client import get_qdrant_client
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG"])

def get_context_for_ticker(ticker: str, top_k: int = 5, max_age_hours: int = 48) -> list[dict]:
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
async def rag_query(ticker: str, top_k: int = 5, max_age_hours: int = 48):
    # Wrap synchronous function in an async endpoint natively
    payloads = get_context_for_ticker(ticker, top_k, max_age_hours)
    return payloads
