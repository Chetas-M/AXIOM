import logging
import sys
import os
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

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

def run_all_scrapers():
    log.info("=== Scheduled scrape job started ===")
    errors = []
    
    try:
        nse_scraper.run()
    except Exception as e:
        log.error(f"NSE scraper failed: {e}", exc_info=True)
        errors.append(f"nse_scraper: {e}")

    try:
        news_scraper.run()
    except Exception as e:
        log.error(f"News scraper failed: {e}", exc_info=True)
        errors.append(f"news_scraper: {e}")

    if errors:
        alert_failure("market_close_scrape", "\n".join(errors))
    else:
        alert_success("market_close_scrape", "OHLCV + news ingested successfully.")
        
    log.info("=== Scheduled scrape job finished ===")

def main():
    scheduler = BlockingScheduler(timezone="Asia/Kolkata")
    
    scheduler.add_job(
        run_all_scrapers,
        trigger=CronTrigger(day_of_week="mon-fri", hour=15, minute=35, timezone="Asia/Kolkata"),
        id="market_close_scrape",
        name="NSE + News scrape at market close",
        max_instances=1,
        misfire_grace_time=300,
    )

    log.info("Scheduler initialized. Jobs scheduled:")
    for job in scheduler.get_jobs():
        log.info(f"  [{job.id}] registered successfully")

    log.info("Running startup scrape to catch up on any missed data...")
    run_all_scrapers()

    log.info("Entering scheduler loop - waiting for triggers...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped.")

if __name__ == "__main__":
    main()
