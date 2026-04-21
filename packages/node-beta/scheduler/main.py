
import logging
import sys
import os
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scrapers"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))

from utils.alerts import alert_success, alert_failure
import nse_scraper
import news_scraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s - %(message)s",
)
log = logging.getLogger("axiom.scheduler")

def run_premarket_pipeline():
    log.info("Running premarket pipeline (Enqueuing Morning Brief)")
    try:
        from axiom_shared.tasks import BriefTask
        from celery import Celery
        from axiom_shared.config import REDIS_URL
        celery_app = Celery("axiom", broker=REDIS_URL, backend=REDIS_URL)

        task = BriefTask(date=datetime.now().strftime("%Y-%m-%d"), tickers=["RELIANCE", "TCS", "INFY"], run_id=f"brief_{datetime.now().timestamp()}")
        celery_app.send_task("worker.morning_brief", kwargs={"payload": task.model_dump()})
        log.info(f"Enqueued brief task {task.run_id}")
    except Exception as e:
        log.error(f"Failed to enqueue brief task: {e}")

def run_intraday_signal_check():
    log.info("Enqueuing intraday signal check...")
    try:
        from axiom_shared.tasks import InferTask
        from celery import Celery
        from axiom_shared.config import REDIS_URL
        celery_app = Celery("axiom", broker=REDIS_URL, backend=REDIS_URL)

        task = InferTask(date=datetime.now().strftime("%Y-%m-%d"), tickers=["RELIANCE", "TCS"], run_id=f"infer_{datetime.now().timestamp()}")
        celery_app.send_task("worker.infer_signals", kwargs={"payload": task.model_dump()})
        log.info(f"Enqueued signal task {task.run_id}")
    except Exception as e:
        log.error(f"Failed to enqueue infer task: {e}")

import paper_ledger

def run_postmarket_summary():
    log.info("Running post-market summary and metrics update")
    # compute daily metrics -> notify bot
    paper_ledger.execute_daily_paper_trades_and_snapshot()
    
def run_all_scrapers():
    log.info("=== Scheduled scrape job started ===")
    try:
        nse_scraper.run()
        news_scraper.run()
    except Exception as e:
        log.error(f"Scraper failed: {e}")

from scrapers.rag_pipeline import run_nse_scrape_and_embed, run_rss_scrape_and_embed
import vix_scraper

def main():
    scheduler = BlockingScheduler(timezone="Asia/Kolkata")
    
    # Existing job
    scheduler.add_job(
        run_all_scrapers,
        trigger=CronTrigger(day_of_week="mon-fri", hour=15, minute=35),
        id="market_close_scrape",
        max_instances=1
    )
    
    # Job 1 — NSE announcements
    scheduler.add_job(
        run_nse_scrape_and_embed,
        CronTrigger(hour="8-16", minute="0,30", day_of_week="mon-fri"),
        id="rag_nse",
        replace_existing=True
    )
    
    # Job 2 — RSS feeds
    scheduler.add_job(
        run_rss_scrape_and_embed,
        CronTrigger(hour="7-16", minute="15,45", day_of_week="mon-fri"),
        id="rag_rss",
        replace_existing=True
    )
    
    # Job 3 — VIX Scraper before market opens
    scheduler.add_job(
        vix_scraper.fetch_and_store_vix,
        CronTrigger(hour=8, minute=30, day_of_week="mon-fri"),
        id="vix_scraper",
        replace_existing=True
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

