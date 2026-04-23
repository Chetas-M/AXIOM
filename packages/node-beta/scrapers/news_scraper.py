import logging
import hashlib
import feedparser
from datetime import datetime, timezone
from base import get_conn

log = logging.getLogger("news_scraper")

GLOBAL_FEEDS = [
    "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
    "https://www.moneycontrol.com/rss/business.xml",
    "https://www.moneycontrol.com/rss/marketreports.xml",
]

def content_hash(title: str, url: str) -> str:
    return hashlib.sha256(f"{title}{url}".encode()).hexdigest()

def parse_published(entry) -> int:
    try:
        t = entry.get("published_parsed") or entry.get("updated_parsed")
        if t:
            return int(datetime(*t[:6], tzinfo=timezone.utc).timestamp())
    except Exception:
        pass
    return int(datetime.now(timezone.utc).timestamp())

def scrape_feed(feed_url: str) -> list[dict]:
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries:
        articles.append({
            "headline":   entry.get("title", "")[:500],
            "url":        entry.get("link", "")[:1000],
            "source":     feed.feed.get("title", feed_url)[:200],
            "published_at": parse_published(entry),
            "body_snippet": entry.get("summary", "")[:2000],
            "content_hash": content_hash(
                entry.get("title", ""),
                entry.get("link", "")
            ),
        })
    return articles

def upsert_articles(conn, articles: list[dict]):
    sql = """
        INSERT INTO news_articles
            (headline, url, source, published_at, body_snippet, content_hash)
        VALUES
            (%(headline)s, %(url)s, %(source)s, %(published_at)s, %(body_snippet)s, %(content_hash)s)
        ON CONFLICT (content_hash) DO NOTHING;
    """
    inserted = 0
    with conn.cursor() as cur:
        for a in articles:
            cur.execute(sql, a)
            inserted += cur.rowcount
    log.info(f"Inserted {inserted}/{len(articles)} new articles")

def run():
    log.info("News scraper started")
    all_articles = []
    for feed_url in GLOBAL_FEEDS:
        try:
            arts = scrape_feed(feed_url)
            log.info(f"Feed {feed_url}: {len(arts)} entries")
            all_articles.extend(arts)
        except Exception as e:
            log.error(f"Feed failed {feed_url}: {e}")

    with get_conn() as conn:
        upsert_articles(conn, all_articles)
    log.info("News scraper done")

if __name__ == "__main__":
    run()
