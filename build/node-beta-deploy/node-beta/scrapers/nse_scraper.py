import logging
import time
import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from base import get_conn

log = logging.getLogger("nse_scraper")

WATCHLIST = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "SBIN", "WIPRO", "LT", "AXISBANK", "BAJFINANCE",
    "MARUTI", "TITAN", "NESTLEIND", "ASIANPAINT", "ULTRACEMCO",
    "HINDUNILVR", "SUNPHARMA", "DRREDDY", "ONGC", "POWERGRID"
]

def fetch_ohlcv(ticker: str, days_back: int = 5):
    symbol = f"{ticker}.NS"
    end = date.today()
    start = end - timedelta(days=days_back)
    df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    df.reset_index(inplace=True)
    df.dropna(subset=["Close"], inplace=True)
    return df

def upsert_ohlcv(conn, ticker: str, df):
    sql = """
        INSERT INTO ohlcv (ticker, date, open, high, low, close, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ticker, date) DO UPDATE SET
            open   = EXCLUDED.open,
            high   = EXCLUDED.high,
            low    = EXCLUDED.low,
            close  = EXCLUDED.close,
            volume = EXCLUDED.volume;
    """
    with conn.cursor() as cur:
        for _, row in df.iterrows():
            cur.execute(sql, (
                ticker,
                row["Date"].to_pydatetime().date(),
                float(row["Open"]),
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
                float(row["Volume"]),
            ))
    log.info(f"{ticker}: {len(df)} rows upserted into ohlcv")

def run():
    log.info("NSE scraper started")
    with get_conn() as conn:
        for ticker in WATCHLIST:
            try:
                df = fetch_ohlcv(ticker)
                if df.empty:
                    log.warning(f"{ticker}: empty dataframe, skipping")
                    continue
                upsert_ohlcv(conn, ticker, df)
                time.sleep(0.5)
            except Exception as e:
                log.error(f"{ticker}: failed - {e}")
    log.info("NSE scraper done")

if __name__ == "__main__":
    run()
