import logging
from datetime import datetime, timezone

import yfinance as yf
from sqlalchemy.orm import sessionmaker

from storage.db import engine
from storage.models import Signal, PaperPosition, PortfolioSnapshot, SignalRun


logger = logging.getLogger(__name__)
SessionLocal = sessionmaker(bind=engine)


def execute_daily_paper_trades_and_snapshot():
    session = SessionLocal()
    today = datetime.now(timezone.utc).date()

    try:
        # 1. Check if signals ran or skipped
        run_status = session.query(SignalRun).filter(SignalRun.date == today).first()
        if run_status and run_status.status == "SKIPPED_REGIME":
            logger.info(f"Signals skipped today due to regime: {run_status.reason}")
            # Report to bot (simulation)
            return

        # 2. Enter new positions from today's signals (if any)
        # We only enter if not skipped regime, but wait, if it was skipped, there are no tradeable signals.
        signals = session.query(Signal).filter(Signal.date == today, Signal.is_tradeable == 1).all()

        for sig in signals:
            # check if an open position for this ticker exists
            existing = session.query(PaperPosition).filter(
                PaperPosition.ticker == sig.ticker,
                PaperPosition.status == "OPEN",
            ).first()

            if not existing:
                # Mock entry price using yfinance
                try:
                    symbol = sig.ticker + ".NS" if not sig.ticker.startswith("^") else sig.ticker
                    hist = yf.Ticker(symbol).history(period="1d")
                    entry_price = float(hist.iloc[-1]["Close"]) if not hist.empty else 100.0
                except Exception:
                    entry_price = 100.0  # fallback

                pos = PaperPosition(
                    ticker=sig.ticker,
                    direction=sig.direction,
                    entry_price=entry_price,
                    entry_time=datetime.now(timezone.utc),
                    quantity=10,  # static quantity for paper trading
                    status="OPEN",
                    signal_confidence=sig.confidence,
                    model_votes=sig.model_votes,
                )
                session.add(pos)
                logger.info(f"Opened {sig.direction} paper position on {sig.ticker} at {entry_price}")

        # 3. Update Snapshot and Unrealized PNL
        open_positions = session.query(PaperPosition).filter(PaperPosition.status == "OPEN").all()

        unrealized_pnl = 0.0
        total_deployed = 0.0

        for pos in open_positions:
            try:
                symbol = pos.ticker + ".NS" if not pos.ticker.startswith("^") else pos.ticker
                hist = yf.Ticker(symbol).history(period="1d")
                current_price = float(hist.iloc[-1]["Close"]) if not hist.empty else pos.entry_price
            except Exception:
                current_price = pos.entry_price

            if pos.direction == "LONG":
                pnl = (current_price - pos.entry_price) * pos.quantity
            else:
                pnl = (pos.entry_price - current_price) * pos.quantity
            pos.pnl = pnl
            unrealized_pnl += pnl
            total_deployed += pos.entry_price * pos.quantity

        total_capital = 100000.0 + unrealized_pnl  # Assuming base 100k

        snapshot = PortfolioSnapshot(
            snapshot_date=today,
            total_capital=total_capital,
            deployed_capital=total_deployed,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=0.0,
            open_positions=len(open_positions),
            daily_sharpe=0.0,  # Mocked
        )
        session.add(snapshot)
        session.commit()
        logger.info(
            f"Recorded End-of-Day Portfolio Snapshot: {total_capital} capital, {unrealized_pnl} uPNL"
        )

    except Exception as e:
        session.rollback()
        logger.error(f"Paper ledger update failed: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    execute_daily_paper_trades_and_snapshot()
