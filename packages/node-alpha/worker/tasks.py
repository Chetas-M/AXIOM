import os
import sys
import logging
from datetime import datetime, timezone

from .celery_app import celery_app

# Add beta path to get DB models and shared tasks
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'node-beta'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from axiom_shared.tasks import EmbedTask, InferTask, BriefTask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.models import Signal, MorningBrief
from ml.lstm_runner import run_lstm
from ml.xgboost_runner import run_xgboost
from ml.prophet_runner import run_prophet
from morning_brief import generate_brief

logger = logging.getLogger(__name__)

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://user:pass@localhost:5432/axiom")
engine = create_engine(POSTGRES_DSN)
SessionLocal = sessionmaker(bind=engine)

def is_expired(enqueued_at: str, expiry_seconds: int) -> bool:
    try:
        dt = datetime.fromisoformat(enqueued_at.replace("Z", "+00:00"))
        if (datetime.now(timezone.utc) - dt).total_seconds() > expiry_seconds:
            return True
    except Exception:
        pass
    return False

@celery_app.task(name="worker.embed_backlog")
def embed_backlog(payload: dict):
    task = EmbedTask(**payload)
    # no expiry
    logger.info(f"Running Embed Backlog {task.run_id}")
    # Would call embedding routine here

@celery_app.task(name="worker.infer_signals")
def infer_signals(payload: dict):
    task = InferTask(**payload)
    if is_expired(str(task.enqueued_at), 86400): # 24h
        logger.warning(f"Task {task.run_id} expired. Dropping.")
        return
    
    logger.info(f"Inferring signals for {task.tickers} on {task.date}")
    
    session = SessionLocal()
    try:
        for ticker in task.tickers:
            # Here we'd call ML models. Simulating.
            LSTM_pred = 0.6 # run_lstm(ticker, task.date)
            XGB_pred = 0.7  # run_xgboost(ticker, task.date)
            PROPHET_pred = 0.65 # run_prophet(ticker, task.date)
            
            sig = Signal(
                ticker=ticker,
                date=datetime.strptime(task.date, "%Y-%m-%d").date(),
                signal_type="ensemble",
                value=0.65,
                direction="LONG",
                confidence=0.65,
                narration="Ensemble models predict upwards movement",
                model_votes={"lstm": LSTM_pred, "xgb": XGB_pred, "prophet": PROPHET_pred},
                features_version="v2.1",
                model_version="v2.1"
            )
            session.add(sig)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Inference failed: {e}")
    finally:
        session.close()

@celery_app.task(name="worker.morning_brief")
def morning_brief(payload: dict):
    task = BriefTask(**payload)
    if is_expired(str(task.enqueued_at), 21600): # 6h
        logger.warning(f"Task {task.run_id} expired. Dropping.")
        return
        
    logger.info(f"Generating morning brief for {task.tickers} on {task.date}")
    
    brief = generate_brief(task.tickers) # LLM writes the brief
    
    session = SessionLocal()
    try:
        mb = MorningBrief(
            date=datetime.strptime(task.date, "%Y-%m-%d").date(),
            ticker_scope="GENERAL",
            narrative=brief,
            citations=[]
        )
        session.add(mb)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Brief generation failed: {e}")
    finally:
        session.close()
