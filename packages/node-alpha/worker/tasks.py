import os
import sys
import logging
from datetime import datetime, timezone
import requests
import time

from .celery_app import celery_app

# Add beta path to get DB models and shared tasks
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'node-beta'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from axiom_shared.tasks import EmbedTask, InferTask, BriefTask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.models import Signal, MorningBrief, MarketRegime, SignalRun, NewsArticle
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
        dt = datetime.fromisoformat(str(enqueued_at).replace("Z", "+00:00"))
        if (datetime.now(timezone.utc) - dt).total_seconds() > expiry_seconds:
            return True
    except Exception:
        pass
    return False

@celery_app.task(name="worker.embed_backlog")
def embed_backlog(payload: dict):
    task = EmbedTask(**payload)
    logger.info(f"Running Embed Backlog {task.run_id} for {len(task.article_ids)} articles.")
    
    session = SessionLocal()
    try:
        # Fetch articles
        articles = session.query(NewsArticle).filter(NewsArticle.id.in_(task.article_ids), NewsArticle.embedding.is_(None)).all()
        logger.info(f"Found {len(articles)} unembedded articles.")
        
        for article in articles:
            prompt = f"{article.headline} {article.body_snippet}"
            try:
                # Use localhost because we are inside Node-Alpha where Ollama is hosted
                resp = requests.post(
                    "http://localhost:11434/api/embeddings", 
                    json={"model": "nomic-embed-text", "prompt": prompt},
                    timeout=10
                )
                if resp.ok:
                    vector = resp.json().get("embedding")
                    if vector:
                        article.embedding = vector
                        article.embed_model = "nomic-embed-text"
                        article.embedded_at = datetime.now()
                else:
                    logger.warning(f"Ollama returned {resp.status_code} for {article.url}")
            except Exception as e:
                logger.warning(f"Ollama error on embedding: {e}")
            time.sleep(0.1) # Brief pause to not hammer Ollama
            
        session.commit()
        logger.info("Completed embedding backlog chunk.")
    except Exception as e:
        session.rollback()
        logger.error(f"Embed backlog failed: {e}")
    finally:
        session.close()

@celery_app.task(name="worker.infer_signals")
def infer_signals(payload: dict):
    task = InferTask(**payload)
    if is_expired(str(task.enqueued_at), 86400):
        logger.warning(f"Task {task.run_id} expired. Dropping.")
        return
    
    logger.info(f"Inferring signals for {task.tickers} on {task.date}")
    
    is_development = os.getenv("AXIOM_ENV", "development").lower() == "development"
    if not is_development:
        logger.error("Real model runners are not yet linked. Failing closed in production.")
        return
    
    session = SessionLocal()
    try:
        run_date = datetime.strptime(task.date, "%Y-%m-%d").date()
        regime_entry = session.query(MarketRegime).order_by(MarketRegime.date.desc()).first()
        VIX_THRESHOLD = 25.0
        if regime_entry and regime_entry.vix > VIX_THRESHOLD:
            logger.warning(f"VIX is {regime_entry.vix}. Skipping inference.")
            existing_sr = session.query(SignalRun).filter(SignalRun.date == run_date).first()
            if existing_sr:
                existing_sr.status = "SKIPPED_REGIME"
                existing_sr.reason = f"VIX > {VIX_THRESHOLD}"
            else:
                session.add(SignalRun(date=run_date, status="SKIPPED_REGIME", reason=f"VIX > {VIX_THRESHOLD}"))
            session.commit()
            return

        for ticker in task.tickers:
            LSTM_pred = 0.6
            XGB_pred = 0.7
            PROPHET_pred = 0.65
            
            ensemble_val = (LSTM_pred + XGB_pred + PROPHET_pred) / 3.0
            confidence = ensemble_val
            direction = "LONG" if ensemble_val > 0.5 else "SHORT"
            # Mock signals are forced non-tradeable
            is_tradeable = 0
            
            existing_sig = session.query(Signal).filter_by(
                ticker=ticker,
                date=run_date,
                signal_type="ensemble"
            ).first()
            if existing_sig:
                existing_sig.value = ensemble_val
                existing_sig.direction = direction
                existing_sig.confidence = confidence
                existing_sig.is_tradeable = is_tradeable
                existing_sig.narration = "Ensemble predicts upwards"
                existing_sig.model_votes = {"lstm": LSTM_pred, "xgb": XGB_pred, "prophet": PROPHET_pred}
                existing_sig.features_version = "v2.1"
                existing_sig.model_version = "v2.1"
            else:
                sig = Signal(
                    ticker=ticker,
                    date=run_date,
                    signal_type="ensemble",
                    value=ensemble_val,
                    direction=direction,
                    confidence=confidence,
                    is_tradeable=is_tradeable,
                    narration="Ensemble predicts upwards",
                    model_votes={"lstm": LSTM_pred, "xgb": XGB_pred, "prophet": PROPHET_pred},
                    features_version="v2.1",
                    model_version="v2.1"
                )
                session.add(sig)
            
        existing_sr = session.query(SignalRun).filter(SignalRun.date == run_date).first()
        if existing_sr:
            existing_sr.status = "COMPLETED"
            existing_sr.reason = "Generated signals"
        else:
            session.add(SignalRun(date=run_date, status="COMPLETED", reason="Generated signals"))
            
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Inference failed: {e}")
    finally:
        session.close()

@celery_app.task(name="worker.morning_brief")
def morning_brief(payload: dict):
    task = BriefTask(**payload)
    if is_expired(str(task.enqueued_at), 21600):
        logger.warning(f"Task {task.run_id} expired. Dropping.")
        return
        
    logger.info(f"Generating morning brief for {task.tickers} on {task.date}")
    brief = generate_brief(task.tickers)
    
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
