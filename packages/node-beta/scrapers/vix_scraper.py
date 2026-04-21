import yfinance as yf
from datetime import datetime
import logging
from sqlalchemy.orm import sessionmaker
from storage.db import engine
from storage.models import MarketRegime

logger = logging.getLogger(__name__)

SessionLocal = sessionmaker(bind=engine)

def fetch_and_store_vix():
    logger.info("Fetching India VIX from yfinance...")
    try:
        ticker = yf.Ticker("^INDIAVIX")
        hist = ticker.history(period="1d")
        if hist.empty:
            logger.error("No VIX data returned")
            return
            
        latest = hist.iloc[-1]
        vix_close = float(latest['Close'])
        # Determine regime
        if vix_close > 25.0:
            regime = "CHAOTIC"
        elif vix_close > 18.0:
            regime = "HIGH_VOLATILITY"
        else:
            regime = "NORMAL"
            
        today = datetime.now().date()
        
        session = SessionLocal()
        try:
            # Upsert
            existing = session.query(MarketRegime).filter(MarketRegime.date == today).first()
            if existing:
                existing.vix = vix_close
                existing.regime = regime
            else:
                new_regime = MarketRegime(date=today, vix=vix_close, regime=regime)
                session.add(new_regime)
            session.commit()
            logger.info(f"Stored VIX {vix_close} (Regime: {regime}) for {today}")
        except Exception as e:
            session.rollback()
            logger.error(f"DB Error while storing VIX: {e}")
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error fetching VIX: {e}")

if __name__ == '__main__':
    fetch_and_store_vix()
