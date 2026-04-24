# Node Beta

## Purpose

Node Beta is the data plane for AXIOM. It is responsible for:

- scraping market and news data
- persisting operational data in Postgres
- serving internal APIs
- running scheduled ingestion and orchestration jobs
- mirroring vector-searchable content into Qdrant

## Code Map

- [api/main.py](D:\New folder\AXIOM\packages\node-beta\api\main.py): FastAPI entrypoint
- [api/routers](D:\New folder\AXIOM\packages\node-beta\api\routers): OHLCV, news, signals, and RAG routes
- [scheduler/main.py](D:\New folder\AXIOM\packages\node-beta\scheduler\main.py): APScheduler orchestration
- [scrapers](D:\New folder\AXIOM\packages\node-beta\scrapers): OHLCV, RSS, NSE, and embedding pipelines
- [storage/models.py](D:\New folder\AXIOM\packages\node-beta\storage\models.py): ORM definitions
- [storage/migrations](D:\New folder\AXIOM\packages\node-beta\storage\migrations): Alembic migration history

## Dependencies

Declared in [requirements.txt](D:\New folder\AXIOM\packages\node-beta\requirements.txt):

- ingestion and scraping: `requests`, `beautifulsoup4`, `feedparser`, `yfinance`, `pandas`
- API and database: `fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `psycopg2-binary`, `alembic`
- scheduling and runtime: `apscheduler`, `python-dotenv`, `httpx`
- vectors: `qdrant-client`
- editable install of `../shared`

## Run

Install dependencies:

```powershell
cd "D:\New folder\AXIOM\packages\node-beta"
pip install -r requirements.txt
```

Apply migrations:

```powershell
alembic upgrade head
```

Start API:

```powershell
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Start scheduler:

```powershell
python scheduler/main.py
```

Initialize Qdrant collection if needed:

```powershell
python storage/qdrant_client.py
```

## Environment

Expected variables:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `DATABASE_URL`
- `QDRANT_HOST`
- `QDRANT_PORT`

## API Surface

- `GET /`
- `GET /health`
- `GET /ohlcv`
- `GET /ohlcv/latest`
- `GET /news`
- `GET /signals`
- `GET /rag/{ticker}`

## Current State

- This is the most complete node in the repo.
- Some storage modules are still unfinished, especially `storage/db.py`.
- There is field-name drift in news-related code paths that should be cleaned up before relying on them as a stable contract.
