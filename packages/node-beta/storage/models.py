from sqlalchemy import Column, String, Date, DateTime, Float, Integer, Text, UniqueConstraint, func

from sqlalchemy.orm import declarative_base

from sqlalchemy.dialects.postgresql import JSONB

from pgvector.sqlalchemy import Vector



Base = declarative_base()



class Stock(Base):

    __tablename__ = "stocks"

    ticker      = Column(String(20), primary_key=True)

    name        = Column(String(255), nullable=False)

    exchange    = Column(String(10), nullable=False)

    sector      = Column(String(100))

    is_active   = Column(Integer, default=1)

    created_at  = Column(DateTime, server_default=func.now())



class OHLCV(Base):

    __tablename__ = "ohlcv"

    id          = Column(Integer, primary_key=True, autoincrement=True)

    ticker      = Column(String(20), nullable=False)

    date        = Column(Date, nullable=False)

    open        = Column(Float)

    high        = Column(Float)

    low         = Column(Float)

    close       = Column(Float)

    volume      = Column(Float)

    created_at  = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("ticker", "date", name="uq_ohlcv_ticker_date"),)



class Signal(Base):

    __tablename__ = "signals"

    id          = Column(Integer, primary_key=True, autoincrement=True)

    ticker      = Column(String(20), nullable=False)

    date        = Column(Date, nullable=False)

    signal_type = Column(String(50), nullable=False)

    value       = Column(Float)

    direction   = Column(String(10))

    confidence  = Column(Float)

    narration   = Column(Text)

    model_votes = Column(JSONB)

    features_version = Column(String(50))

    model_version = Column(String(50))

    is_tradeable= Column(Integer, default=1)

    created_at  = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("ticker", "date", "signal_type", name="uq_signal_ticker_date_type"),)



class MorningBrief(Base):

    __tablename__ = "morning_briefs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    date = Column(Date, nullable=False)

    ticker_scope = Column(String(20)) # "GENERAL" or ticker

    narrative = Column(Text, nullable=False)

    citations = Column(JSONB) # array of news ids

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("date", "ticker_scope", name="uq_morning_brief_date_scope"),)



class NewsArticle(Base):

    __tablename__ = "news_articles"

    id              = Column(Integer, primary_key=True, autoincrement=True)

    ticker          = Column(String(20), nullable=True, index=True) # Allowed NULL for global news

    headline        = Column(Text, nullable=False)

    body_snippet    = Column(Text)

    source          = Column(String(100))

    url             = Column(Text, nullable=False)

    content_hash    = Column(String(64), unique=True, nullable=False)

    published_at    = Column(Integer, index=True)

    created_at      = Column(DateTime, server_default=func.now())

    

    # pgvector columns

    embedding       = Column(Vector(768))

    embedded_at     = Column(DateTime(timezone=True))

    embed_model     = Column(Text)





class PaperPosition(Base):

    __tablename__ = 'paper_positions'

    id = Column(Integer, primary_key=True)

    ticker = Column(String(20), nullable=False)

    direction = Column(String(10), nullable=False)  # LONG / SHORT

    entry_price = Column(Float)

    entry_time = Column(DateTime(timezone=True))

    quantity = Column(Integer)

    status = Column(String(10), default='OPEN')    # OPEN / CLOSED

    exit_price = Column(Float)

    exit_time = Column(DateTime(timezone=True))

    pnl = Column(Float)

    signal_confidence = Column(Float)

    model_votes = Column(JSONB)                    # {xgb: 0.81, lstm: 0.69, prophet: 0.72}



class PortfolioSnapshot(Base):

    __tablename__ = 'portfolio_snapshots'

    id = Column(Integer, primary_key=True)

    snapshot_date = Column(Date, nullable=False)

    total_capital = Column(Float)

    deployed_capital = Column(Float)

    unrealized_pnl = Column(Float)

    realized_pnl = Column(Float)

    open_positions = Column(Integer)

    daily_sharpe = Column(Float)







class MarketRegime(Base):

    __tablename__ = 'market_regime'

    id = Column(Integer, primary_key=True, autoincrement=True)

    date = Column(Date, nullable=False, unique=True)

    vix = Column(Float, nullable=False)

    regime = Column(String(50)) # NORMAL, HIGH_VOLATILITY, CHAOTIC

    created_at = Column(DateTime, server_default=func.now())



class SignalRun(Base):

    __tablename__ = 'signal_runs'

    id = Column(Integer, primary_key=True, autoincrement=True)

    date = Column(Date, nullable=False, unique=True)

    status = Column(String(50), nullable=False) # e.g. COMPLETED, SKIPPED_REGIME

    reason = Column(String(255))

    created_at = Column(DateTime, server_default=func.now())

