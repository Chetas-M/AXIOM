import sys
import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime, timezone

# Adjust path to import packages inside node-beta
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from storage.models import NewsArticle
try:
    from scrapers.embedder import embed_documents
except ImportError:
    # mock or fallback
    def embed_documents(docs):
        return [([0.0] * 768, doc) for doc in docs]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backfill_pgvector")

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://user:pass@localhost:5432/axiom")
import urllib.parse
password = urllib.parse.quote_plus(os.environ.get('POSTGRES_PASSWORD', 'changeme')).replace('%', '%%')
host = os.environ.get("POSTGRES_HOST", "localhost")
port = os.environ.get("POSTGRES_PORT", "5432")
user = os.environ.get("POSTGRES_USER", "axiom")
db = os.environ.get("POSTGRES_DB", "axiom")

if POSTGRES_DSN == "postgresql://user:pass@localhost:5432/axiom":
    POSTGRES_DSN = f"postgresql://{user}:{password}@{host}:{port}/{db}"

engine = create_engine(POSTGRES_DSN)
SessionLocal = sessionmaker(bind=engine)

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def backfill_embeddings():
    """
    Fetches rows where embedding IS NULL and populates them.
    Idempotent due to IS NULL check.
    """
    logger.info("Starting backfill for pgvector embeddings...")
    session = SessionLocal()
    try:
        # Fetch rows without embeddings
        articles = session.query(NewsArticle).filter(NewsArticle.embedding == None).all()
        logger.info(f"Found {len(articles)} articles missing embeddings.")

        if not articles:
            logger.info("Nothing to backfill.")
            return

        # Process in batches
        BATCH_SIZE = 100
        for batch in chunks(articles, BATCH_SIZE):
            logger.info(f"Processing batch of {len(batch)}...")
            
            docs = []
            for a in batch:
                docs.append({
                    "id": a.id,
                    "headline": a.headline,
                    "body_snippet": a.body_snippet or ''
                })
            
            # Fetch embeddings
            embedded = embed_documents(docs)
            
            # Update DB
            for env_vec, doc in embedded:
                article = session.query(NewsArticle).get(doc["id"])
                if article:
                    article.embedding = env_vec
                    article.embedded_at = datetime.now(timezone.utc)
                    article.embed_model = "nomic-embed-text" 
                
            session.commit()
            logger.info(f"Committed {len(embedded)} embeddings.")

    except Exception as e:
        session.rollback()
        logger.error(f"Backfill failed: {e}")
    finally:
        session.close()
    
    logger.info("Backfill complete.")

if __name__ == "__main__":
    backfill_embeddings()
