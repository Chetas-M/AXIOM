import logging
import sys
import os
import hashlib
from datetime import datetime

from scrapers.scraper_nse import scrape_nse_announcements
from scrapers.scraper_rss import scrape_rss_feeds
from storage.db import get_conn

# Add shared to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from axiom_shared.config import REDIS_URL
from axiom_shared.tasks import EmbedTask
from celery import Celery

logger = logging.getLogger(__name__)
celery_app = Celery("axiom", broker=REDIS_URL, backend=REDIS_URL)

def get_content_hash(doc: dict) -> str:
    raw = f"{doc.get('url', '')}{doc.get('headline', '')}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def save_to_postgres(docs: list[dict]) -> list[int]:
    inserted_ids = []
    sql = """
        INSERT INTO news_articles (ticker, headline, body_snippet, url, source, published_at, content_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (content_hash) DO NOTHING
        RETURNING id;
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
                    res = cur.fetchone()
                    if res:
                        inserted_ids.append(res[0])
            conn.commit()
            logger.info(f"Saved {len(inserted_ids)} new documents to Postgres out of {len(docs)} scraped.")
    except Exception as e:
        logger.error(f"Error saving to Postgres: {e}")
    return inserted_ids

def trigger_embedding(article_ids: list[int]):
    if not article_ids:
        return
    logger.info(f"Enqueuing embedding task for {len(article_ids)} new articles.")
    task = EmbedTask(article_ids=article_ids, run_id=f"embed_{datetime.now().timestamp()}")
    celery_app.send_task("worker.embed_backlog", kwargs={"payload": task.model_dump()})

def run_nse_scrape_and_embed():
    logger.info("Running NSE RAG pipeline...")
    docs = scrape_nse_announcements()
    if not docs:
        return
    inserted_ids = save_to_postgres(docs)
    trigger_embedding(inserted_ids)

def run_rss_scrape_and_embed():
    logger.info("Running RSS RAG pipeline...")
    docs = scrape_rss_feeds()
    if not docs:
        return
    inserted_ids = save_to_postgres(docs)
    trigger_embedding(inserted_ids)
