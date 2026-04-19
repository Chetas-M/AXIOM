import feedparser
import re
import logging
from datetime import datetime, timedelta
from storage.db import get_conn

logger = logging.getLogger(__name__)

# MoneyControl: https://www.moneycontrol.com/rss/marketsnews.xml
# Economic Times Markets: https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms

RSS_FEEDS = {
    "moneycontrol": "https://www.moneycontrol.com/rss/marketsnews.xml",
    "et": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
}

def load_tickers_from_db():
    tickers = set()
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT ticker FROM stocks")
                rows = cur.fetchall()
                for row in rows:
                    tickers.add(row[0].upper())
    except Exception as e:
        logger.error(f"Failed to load tickers from db: {e}")
    return tickers

def extract_ticker(text, known_tickers):
    words = re.findall(r'\b[A-Z0-9]{3,15}\b', text.upper())
    for word in words:
        if word in known_tickers:
            return word
    return "GENERAL"

def scrape_rss_feeds() -> list[dict]:
    known_tickers = load_tickers_from_db()

    cutoff_time = datetime.now() - timedelta(hours=48)
    cutoff_ts = int(cutoff_time.timestamp())

    articles = []

    for source_name, feed_url in RSS_FEEDS.items():
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.get('title', '')
            link = entry.get('link', '')
            summary = entry.get('summary', '')
            published = entry.get('published_parsed')
            
            if not published:
                continue
            
            # Format time
            try:
                published_ts = int(time.mktime(published))
            except Exception:
                continue

            if published_ts < cutoff_ts:
                continue

            ticker = extract_ticker(title + " " + summary, known_tickers)

            articles.append({
                "ticker": ticker,
                "published_at": published_ts,
                "source": source_name,
                "headline": title.strip(),
                "body_snippet": summary.strip()[:400],
                "url": link.strip()
            })

    logger.info(f"Scraped {len(articles)} RSS articles.")
    return articles
