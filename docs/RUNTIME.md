# API and Runtime Flows

## Node Alpha API

File: [packages/node-alpha/api/main.py](D:\New folder\AXIOM\packages\node-alpha\api\main.py)

### `POST /infer`

Request body:

```json
{
  "tickers": ["RELIANCE", "TCS"],
  "timeframe": "15m",
  "models": ["xgboost", "lstm", "prophet"]
}
```

Response shape:

```json
{
  "RELIANCE": {
    "signal": "LONG",
    "confidence": 0.78,
    "xgb": 0.82,
    "lstm": 0.74,
    "prophet": 0.77
  }
}
```

Behavior:

- returns one signal per requested ticker
- calculates the final signal from the average of mocked model scores
- is currently suitable for integration testing, not production-grade inference

### `GET /health`

Returns a basic service heartbeat.

## Node Beta API

File: [packages/node-beta/api/main.py](D:\New folder\AXIOM\packages\node-beta\api\main.py)

### `GET /`

Returns a simple welcome payload pointing operators to `/docs`.

### `GET /health`

Returns a service heartbeat.

### `GET /ohlcv`

Query parameters:

- `ticker`
- `from_date`
- `to_date`
- `limit`

Backed by raw SQL against Postgres `ohlcv`.

### `GET /ohlcv/latest`

Returns latest close and volume per ticker using `DISTINCT ON`.

### `GET /news`

Query parameters:

- `ticker`
- `source`
- `limit`

Important note:

- the SQL query selects `title` and `summary`, but the SQLAlchemy model currently defines `headline` and `body_snippet`; this should be resolved before relying on the endpoint contract.

### `GET /signals`

Query parameters:

- `ticker`
- `signal_type`
- `limit`

Returns recent signal rows from Postgres.

### `GET /rag/{ticker}`

Query parameters:

- `top_k`
- `max_age_hours`

Behavior:

- requests an embedding from Alpha's local model endpoint on port `11434`
- searches Qdrant `news_docs`
- filters by ticker and recency
- returns payloads only

## Scheduled Jobs

File: [packages/node-beta/scheduler/main.py](D:\New folder\AXIOM\packages\node-beta\scheduler\main.py)

### Jobs Defined

- `market_close_scrape`
- `rag_nse`
- `rag_rss`
- premarket pipeline
- intraday signal check
- postmarket summary

### Cross-Node Calls

The scheduler currently reaches:

- `http://node-alpha:8001/infer`
- `run_nse_scrape_and_embed()`
- `run_rss_scrape_and_embed()`

## Telegram Watchdog

File: [packages/node-gamma/bot/main.py](D:\New folder\AXIOM\packages\node-gamma\bot\main.py)

Behavior:

- checks Beta `http://node-beta:8000/health`
- checks Alpha `http://node-alpha:8001/health`
- sends Telegram alerts if either call fails
- otherwise logs success locally

## Storage Model Summary

File: [packages/node-beta/storage/models.py](D:\New folder\AXIOM\packages\node-beta\storage\models.py)

Core tables:

- `stocks`
- `ohlcv`
- `signals`
- `news_articles`
- `paper_positions`
- `portfolio_snapshots`

Important note:

- the file appears to contain mixed encoding or copied text near the bottom; keep that in mind if migrations or imports behave strangely on some environments.
