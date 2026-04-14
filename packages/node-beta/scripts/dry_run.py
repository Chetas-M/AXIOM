import sys
import os

# Add parent path so we can import scheduler
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scheduler.main import run_premarket_pipeline, run_intraday_signal_check, run_postmarket_summary
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("dry_run")

def dry_run():
    log.info("=== STARTING DRY RUN ===")
    
    log.info("1. Running pre-market pipeline...")
    run_premarket_pipeline()
    
    log.info("2. Running intraday signal check...")
    run_intraday_signal_check()
    
    log.info("3. Running post-market summary...")
    run_postmarket_summary()
    
    log.info("=== DRY RUN COMPLETE ===")

if __name__ == "__main__":
    dry_run()

