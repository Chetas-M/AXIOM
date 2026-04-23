
from sqlalchemy import func
from sqlalchemy.orm import Session
from storage.db import SessionLocal
from storage.models import PaperPosition, PortfolioSnapshot
from datetime import date
from statistics import mean

def compute_daily_metrics(target_date: date):
    "Computes daily paper trade metrics and stores snapshot"
    db: Session = SessionLocal()
    
    try:
        # fetch closed trades for today
        closed_trades = db.query(PaperPosition).filter(
            PaperPosition.status == "CLOSED",
            func.date(PaperPosition.exit_time) == target_date
        ).all()
        
        wins, losses = 0, 0
        pnl_array = []
        for t in closed_trades:
            if t.pnl > 0: wins += 1
            else: losses += 1
            pnl_array.append(t.pnl)
            
        total = wins + losses
        win_rate = (wins / total) if total > 0 else 0
        avg_pnl = mean(pnl_array) if pnl_array else 0
        
        # calculate total equity, realize pnl
        total_pnl = sum(pnl_array)
        
        open_trades_count = db.query(PaperPosition).filter(PaperPosition.status == "OPEN").count()
        
        snap = PortfolioSnapshot(
            snapshot_date=target_date,
            total_capital=100000 + total_pnl, # dummy base
            deployed_capital=open_trades_count * 10000,
            unrealized_pnl=0,
            realized_pnl=total_pnl,
            open_positions=open_trades_count,
            daily_sharpe=0.0 # dummy
        )
        db.add(snap)
        db.commit()
        return {
            "win_rate": win_rate,
            "avg_pnl_per_trade": avg_pnl,
            "total_pnl": total_pnl,
            "open_positions": open_trades_count
        }
    finally:
        db.close()

