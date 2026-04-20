import logging
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from storage.qdrant_client import get_qdrant_client, init_qdrant
from scrapers.scraper_nse import scrape_nse_announcements
from scrapers.scraper_rss import scrape_rss_feeds
from scrapers.embedder import embed_documents
from storage.db import get_conn
import uuid
import sys
import os
import hashlib

# Add shared to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from axiom_shared.config import VECTOR_BACKEND

logger = logging.getLogger(__name__)

def deduplicate_against_qdrant(client, docs: list[dict], collection_name="news_docs") -> list[dict]:
    new_docs = []
    for doc in docs:
        url = doc["url"]
        scroll_result, _ = client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="url",
                        match=MatchValue(value=url)
                    )
                ]
            ),
            limit=1,
            with_payload=False,
            with_vectors=False,
        )
        if not scroll_result:
            new_docs.append(doc)
    return new_docs

def upsert_to_qdrant(client, vectors_and_docs: list[tuple[list[float], dict]], collection_name="news_docs"):
    from qdrant_client.http.models import PointStruct
    points = []
    for vec, payload in vectors_and_docs:
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload=payload
        ))
    if points:
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        logger.info(f"Upserted {len(points)} docs into Qdrant '{collection_name}'.")

def get_content_hash(doc: dict) -> str:
    raw = f"{doc.get('url', '')}{doc.get('headline', '')}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def mirror_to_postgres(docs: list[dict], vectors_and_docs: list[tuple[list[float], dict]] = None):
    url_to_vec = {}
    if vectors_and_docs:
        for vec, md in vectors_and_docs:
            url_to_vec[md.get("url")] = vec

    sql = """
        INSERT INTO news_articles (ticker, headline, body_snippet, url, source, published_at, content_hash, embedding, embedded_at, embed_model)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        ON CONFLICT (content_hash) DO NOTHING;
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                for doc in docs:
                    vec = url_to_vec.get(doc.get("url"))
                    model = "nomic-embed-text" if vec else None
                    cur.execute(sql, (
                        doc.get("ticker"),
                        doc.get("headline"),
                        doc.get("body_snippet"),
                        doc.get("url"),
                        doc.get("source"),
                        doc.get("published_at"),
                        get_content_hash(doc),
                        vec,
                        model
                    ))
            conn.commit()
            logger.info(f"Mirrored {len(docs)} documents to Postgres.")
    except Exception as e:
        logger.error(f"Error mirroring to Postgres: {e}")

def run_nse_scrape_and_embed():
    logger.info("Running NSE RAG pipeline...")
    docs = scrape_nse_announcements()
    if not docs:
        return
    
    if VECTOR_BACKEND == "pgvector":
        vectors_and_docs = embed_documents(docs)
        if vectors_and_docs:
             mirror_to_postgres(docs, vectors_and_docs)
        else:
             mirror_to_postgres(docs)
    else:
        init_qdrant()
        client = get_qdrant_client()
        new_docs = deduplicate_against_qdrant(client, docs)
        if not new_docs:
            return
        vectors_and_docs = embed_documents(new_docs)
        if vectors_and_docs:
            upsert_to_qdrant(client, vectors_and_docs)
            mirror_to_postgres(new_docs)

def run_rss_scrape_and_embed():
    logger.info("Running RSS RAG pipeline...")
    docs = scrape_rss_feeds()
    if not docs:
        return
    
    if VECTOR_BACKEND == "pgvector":
        vectors_and_docs = embed_documents(docs)
        if vectors_and_docs:
             mirror_to_postgres(docs, vectors_and_docs)
        else:
             mirror_to_postgres(docs)
    else:
        init_qdrant()
        client = get_qdrant_client()
        new_docs = deduplicate_against_qdrant(client, docs)
        if not new_docs:
            return
        vectors_and_docs = embed_documents(new_docs)
        if vectors_and_docs:
            upsert_to_qdrant(client, vectors_and_docs)
            mirror_to_postgres(new_docs)
import logging
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from storage.qdrant_client import get_qdrant_client, init_qdrant
from scrapers.scraper_nse import scrape_nse_announcements
from scrapers.scraper_rss import scrape_rss_feeds
from scrapers.embedder import embed_documents
from storage.db import get_conn
import uuid
import sys
import os

# Add shared to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from axiom_shared.config import VECTOR_BACKEND

logger = logging.getLogger(__name__)

def deduplicate_against_qdrant(client, docs: list[dict], collection_name="news_docs") -> list[dict]:
    new_docs = []
    for doc in docs:
        url = doc["url"]
        scroll_result, _ = client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="url",
                        match=MatchValue(value=url)
                    )
                ]
            ),
            limit=1,
            with_payload=False,
            with_vectors=False,
        )
        if not scroll_result:
            new_docs.append(doc)
    return new_docs

def upsert_to_qdrant(client, vectors_and_docs: list[tuple[list[float], dict]], collection_name="news_docs"):
    from qdrant_client.http.models import PointStruct
    points = []
    for vec, payload in vectors_and_docs:
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload=payload
        ))
    if points:
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        logger.info(f"Upserted {len(points)} docs into Qdrant '{collection_name}'.")

import hashlib

def get_content_hash(doc: dict) -> str:
    raw = f"{doc.get('url', '')}{doc.get('headline', '')}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def mirror_to_postgres(docs: list[dict]):
    sql = """
        INSERT INTO news_articles (ticker, headline, body_snippet, url, source, published_at, content_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (content_hash) DO NOTHING;
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                for doc in docs:
                    cur.execute(sql, (
                        doc.get("ticker"),
                        doc.get("headline"),
                        doc.get("body_snippet"),
                        doc.get("url"),
                        doc.get("source"),
                        doc.get("published_at"),
                        get_content_hash(doc)
                    ))
            logger.info(f"Mirrored {len(docs)} documents to Postgres.")
    except Exception as e:
        logger.error(f"Error mirroring to Postgres: {e}")

def run_nse_scrape_and_embed():
    logger.info("Running NSE RAG pipeline...")
    init_qdrant()
    client = get_qdrant_client()
    docs = scrape_nse_announcements()
    if not docs:
        return
    logger.info(f"NSE Scraped {len(docs)} docs, deduplicating...")
    new_docs = deduplicate_against_qdrant(client, docs)
    if not new_docs:
        logger.info("No new NSE docs to process.")
        return
    vectors_and_docs = embed_documents(new_docs)
    if vectors_and_docs:
        upsert_to_qdrant(client, vectors_and_docs)
        mirror_to_postgres(new_docs)

def run_rss_scrape_and_embed():
    logger.info("Running RSS RAG pipeline...")
    init_qdrant()
    client = get_qdrant_client()
    docs = scrape_rss_feeds()
    if not docs:
        return
    logger.info(f"RSS Scraped {len(docs)} docs, deduplicating...")
    new_docs = deduplicate_against_qdrant(client, docs)
    if not new_docs:
        logger.info("No new RSS docs to process.")
        return
    vectors_and_docs = embed_documents(new_docs)
    if vectors_and_docs:
        upsert_to_qdrant(client, vectors_and_docs)
        mirror_to_postgres(new_docs)
