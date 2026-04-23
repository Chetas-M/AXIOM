import requests
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def scrape_nse_announcements() -> list[dict]:
    """Scrapes NSE announcements using a cookies session."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    })
    
    # 1. Hit main page to get cookies
    try:
        session.get("https://www.nseindia.com", timeout=15)
        time.sleep(1)
    except Exception as e:
        logger.error(f"Failed to fetch cookies from NSE: {e}")
        return []

    # 2. Fetch corporate announcements API
    announcements = []
    try:
        url = "https://www.nseindia.com/api/corporate-announcements?index=equities"
        response = session.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"Failed to get NSE API: {e}")
        return []

    cutoff_time = datetime.now() - timedelta(hours=48)
    cutoff_ts = int(cutoff_time.timestamp())

    for item in data:
        symbol = item.get("symbol")
        desc = item.get("desc")
        url_attachment = item.get("attchmntFile")
        exchdisstime = item.get("exchdisstime")
        
        if not symbol or not desc or not exchdisstime:
            continue
            
        try:
            dt = datetime.strptime(exchdisstime, "%d-%b-%Y %H:%M:%S")
            published_at = int(dt.timestamp())
        except ValueError:
            continue
            
        if published_at < cutoff_ts:
            continue
            
        announcements.append({
            "ticker": symbol.strip().upper(),
            "published_at": published_at,
            "source": "nse",
            "headline": desc.strip(),
            "body_snippet": desc.strip()[:400],
            "url": f"https://www.nseindia.com{url_attachment}" if url_attachment else "https://www.nseindia.com"
        })

    logger.info(f"Scraped {len(announcements)} valid NSE announcements.")
    return announcements
