import os
import httpx
import logging
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("axiom.alerts")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message: str):
    if not BOT_TOKEN or not CHAT_ID or BOT_TOKEN == "your_token_here":
        log.warning("Telegram credentials not set - alert suppressed")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = httpx.post(url, json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
        }, timeout=10)
        log.debug(f"Telegram response status: {r.status_code}")
    except Exception as e:
        log.error(f"Telegram alert failed: {e}")

def alert_success(job: str, detail: str = ""):
    send_telegram(f"✅ *AXIOM* `{job}` completed\n{detail}")

def alert_failure(job: str, error: str):
    send_telegram(f"🚨 *AXIOM FAILURE* `{job}`\n```{error}```")
