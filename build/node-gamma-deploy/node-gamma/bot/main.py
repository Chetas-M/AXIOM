
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import os
import requests
from datetime import datetime

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("axiom.bot")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(msg: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning(f"MOCK TELEGRAM ALERT (No token/chat_id set): {msg}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        log.info("Telegram alert sent successfully.")
    except Exception as e:
        log.error(f"Failed to send Telegram alert: {e}")

def watchdog():
    failed_checks = []
    
    try:
        res_beta = requests.get("http://node-beta:8000/health", timeout=5)
        if res_beta.status_code != 200: failed_checks.append("node-beta:8000 FastAPI")
    except Exception:
        failed_checks.append("node-beta:8000 unreachable")
        
    try:
        res_alpha = requests.get("http://node-alpha:8001/health", timeout=5)
        if res_alpha.status_code != 200: failed_checks.append("node-alpha:8001 inference")
    except Exception:
        failed_checks.append("node-alpha:8001 unreachable")
        
    # TODO: Check scraper freshness (e.g. hitting an endpoint on beta)
    
    if failed_checks:
        send_telegram_alert(f"?? AXIOM health check failed: {failed_checks}")
    else:
        log.info("Watchdog: all systems go")

def main():
    scheduler = BackgroundScheduler()
    # Every 5 mins
    scheduler.add_job(watchdog, "interval", minutes=5)
    scheduler.start()
    
    log.info("Gateway to TG bot running. Watchdog scheduled.")
    try:
        # keep alive
        while True:
            pass
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()

