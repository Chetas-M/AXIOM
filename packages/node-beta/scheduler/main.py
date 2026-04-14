
import logging
import sys
import os
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scrapers"))

from utils.alerts import alert_success, alert_failure
import nse_scraper
import news_scraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s - %(message)s",
)
log = logging.getLogger("axiom.scheduler")

def run_premarket_pipeline():
    log.info("Running premarket pipeline (T-1 signals, etc.)")

def run_intraday_signal_check():
    log.info("Running intraday signal check...")
    # call node-alpha/infer
    try:
        req = {
            "tickers": ["RELIANCE", "TCS"],
            "timeframe": "15m",
            "models": ["xgboost", "lstm", "prophet"]
        }
        res = requests.post("http://node-alpha:8001/infer", json=req)
        # TODO: Execute paper trading logic
        log.info(res.json())
    except Exception as e:
        log.error(f"Failed to call alpha: {e}")

def run_postmarket_summary():
    log.info("Running post-market summary and metrics update")
    # compute daily metrics -> notify bot
    
def run_all_scrapers():
    log.info("=== Scheduled scrape job started ===")
    try:
        nse_scraper.run()
        news_scraper.run()
    except Exception as e:
        log.error(f"Scraper failed: {e}")

def main():
    scheduler = BlockingScheduler(timezone="Asia/Kolkata")
    
    # Existing job
    scheduler.add_job(
        run_all_scrapers,
        trigger=CronTrigger(day_of_week="mon-fri", hour=15, minute=35),
        id="market_close_scrape",
        max_instances=1
    )
    
    # pre-market: 08:45 IST
    scheduler.add_job(run_premarket_pipeline, CronTrigger(hour=8, minute=45))

    # intraday tick: 09:15 - 15:30
    scheduler.add_job(run_intraday_signal_check, CronTrigger(
        hour="9-15", minute="15,30,45,0", day_of_week="mon-fri"
    ))

    # post-market close: 15:45 IST
    scheduler.add_job(run_postmarket_summary, CronTrigger(hour=15, minute=45))

    log.info("Running start up.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    main()

