import os
import sys
import httpx
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "node-beta"))
from utils.alerts import alert

load_dotenv()
logger = logging.getLogger(__name__)

# DB setup
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

POSTGRES_DSN = os.environ.get("POSTGRES_DSN", "postgresql://user:pass@localhost:5432/axiom")
engine = create_engine(POSTGRES_DSN)
SessionLocal = sessionmaker(bind=engine)

def check_postgres() -> tuple[bool, str]:
    try:
        session = SessionLocal()
        session.execute(text("SELECT 1"))
        # Check migrations state (alembic_version table should have at least 1 row)
        res = session.execute(text("SELECT version_num FROM alembic_version")).fetchone()
        if not res:
            return False, "Postgres is up, but Alembic migrations table is empty"
        session.close()
        return True, "OK"
    except Exception as e:
        return False, str(e)

def check_redis() -> tuple[bool, str]:
    import redis
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    try:
        r = redis.from_url(redis_url, socket_connect_timeout=2)
        r.ping()
        return True, "OK"
    except Exception as e:
        return False, str(e)

def check_beta_api() -> tuple[bool, str]:
    api_url = os.environ.get("API_HEALTH_URL", "http://localhost:8000/health")
    try:
        r = httpx.get(api_url, timeout=3)
        if r.status_code == 200:
            return True, "OK"
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)

def check_scraper_activity() -> tuple[bool, str]:
    from storage.models import NewsArticle
    try:
        session = SessionLocal()
        latest = session.query(NewsArticle).order_by(NewsArticle.created_at.desc()).first()
        session.close()
        if not latest:
            return False, "No articles found in DB"
        
        # Freshness threshold: 24 hours
        time_since = (datetime.now() - latest.created_at).total_seconds()
        if time_since > 86400: # 24h
            return False, f"Stalled. Last article {time_since/3600:.1f}h ago"
        return True, "OK"
    except Exception as e:
        return False, str(e)

def check_alpha_reachable() -> bool:
    # Just check if we can hit Celery flower, or check redis ping (if celery uses same redis)
    # We will assume Alpha is online if Ollama or worker is pingable
    ollama_url = os.environ.get("OLLAMA_URL", "http://node-alpha:11434")
    try:
        httpx.get(ollama_url, timeout=2)
        return True
    except:
        return False

def check_celery_worker() -> tuple[bool, str]:
    import redis
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    try:
        r = redis.from_url(redis_url, socket_connect_timeout=2)
        # The worker emits heartbeats, but we can do a broker ping or inspect worker list
        # For simplicity, if we can inspect celery state... wait, celery needs an app
        from celery import Celery
        app = Celery("axiom", broker=redis_url)
        i = app.control.inspect(timeout=1)
        stats = i.stats()
        if stats and len(stats) > 0:
            return True, "OK"
        return False, "No active Celery workers reported via inspect"
    except Exception as e:
        return False, str(e)

def check_ollama() -> tuple[bool, str]:
    ollama_url = os.environ.get("OLLAMA_URL", "http://node-alpha:11434")
    try:
        r = httpx.get(ollama_url, timeout=3)
        if r.status_code == 200:
            return True, "OK"
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)

def main():
    failed_critical = []
    failed_high = []
    failed_info = []

    # CRITICAL: Postgres, Redis, Beta API
    db_ok, db_msg = check_postgres()
    if not db_ok: failed_critical.append(f"Postgres down: {db_msg}")
    
    redis_ok, redis_msg = check_redis()
    if not redis_ok: failed_critical.append(f"Redis down: {redis_msg}")
    
    api_ok, api_msg = check_beta_api()
    if not api_ok: failed_critical.append(f"Beta API down: {api_msg}")

    # HIGH: scraper stalled
    scrape_ok, scrape_msg = check_scraper_activity()
    if not scrape_ok: failed_high.append(f"Scraper stalled: {scrape_msg}")

    # Alpha conditional
    if check_alpha_reachable():
        cw_ok, cw_msg = check_celery_worker()
        if not cw_ok: failed_high.append(f"Worker stalled/down: {cw_msg}")
        
        ol_ok, ol_msg = check_ollama()
        if not ol_ok: failed_high.append(f"Ollama down: {ol_msg}")
    else:
        # If alpha is unreachable but expected, maybe it's high or info? 
        # The task condition says: "Only if Alpha reachable: Celery worker heartbeat..."
        # implying Alpha is not always on. Thus, no alert if Alpha is down.
        pass

    if failed_critical:
        alert("CRITICAL", "Watchdog Matrix", "\n".join(failed_critical))
        print("CRITICAL:", failed_critical)
        
    if failed_high:
        alert("HIGH", "Watchdog Matrix", "\n".join(failed_high))
        print("HIGH:", failed_high)
        
    if failed_info:
        alert("INFO", "Watchdog Matrix", "\n".join(failed_info))
        print("INFO:", failed_info)

if __name__ == '__main__':
    main()
