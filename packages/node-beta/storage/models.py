from sqlalchemy import Column, String, Date, DateTime, Float, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import declarative_base

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
    created_at  = Column(DateTime, server_default=func.now())
    __table_args__ = (UniqueConstraint("ticker", "date", "signal_type", name="uq_signal_ticker_date_type"),)

class NewsArticle(Base):
    __tablename__ = "news_articles"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    ticker          = Column(String(20), nullable=True) # Allowed NULL for global news
    title           = Column(Text, nullable=False)      # Renamed for script sync
    summary         = Column(Text)                      # Added for script sync
    source          = Column(String(100))
    url             = Column(Text)
    published_at    = Column(DateTime)
    content_hash    = Column(String(64), unique=True, nullable=False) # Added for script sync
    embedding_id    = Column(String(100))
    created_at      = Column(DateTime, server_default=func.now())
