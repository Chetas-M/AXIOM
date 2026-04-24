# AXIOM Architecture

## Purpose

AXIOM is designed as a distributed market-intelligence stack for Indian equities with three operational concerns split across separate machines:

- compute-heavy inference on Node Alpha
- always-on ingestion and persistence on Node Beta
- low-resource alerting and operator interaction on Node Gamma

This separation keeps model workloads isolated from scraping and bot reliability concerns.

## High-Level Topology

```text
                   +--------------------------------------+
                   | Node Alpha                           |
                   | Ports: 8001, 11434, 6333            |
                   | Roles: infer, embed, narrate, RAG   |
                   +-----------------+--------------------+
                                     ^
                                     |
                                     |
+---------------------+              |              +------------------------+
| Node Gamma          |              |              | Node Beta              |
| Role: watchdog      |              |              | Ports: 8000            |
| Telegram alerts     | ------------ | ------------ | API + scheduler        |
| Dashboard stub      | health/API   | infer/embed  | Postgres + ingestion   |
+---------------------+                             +------------------------+
```

## Node Responsibilities

### Node Alpha

Primary responsibility:

- produce inference responses for requested tickers
- host or proxy local LLM and embedding workloads
- support RAG enrichment used by narrations and Beta search

Implemented components:

- [packages/node-alpha/api/main.py](D:\New folder\AXIOM\packages\node-alpha\api\main.py): FastAPI service exposing `/infer` and `/health`
- [packages/node-alpha/morning_brief.py](D:\New folder\AXIOM\packages\node-alpha\morning_brief.py): orchestration script for signal narration with RAG context
- [packages/node-alpha/rag/rag_enrichment.py](D:\New folder\AXIOM\packages\node-alpha\rag\rag_enrichment.py): fetches Beta RAG context per ticker

Current limitations:

- inference output is mocked with random ensemble values
- the LLM loader is still a stub
- there is no documented service definition in `infra/systemd/` for Alpha yet

### Node Beta

Primary responsibility:

- scrape market and news data
- persist structured records in Postgres
- serve internal APIs
- run the recurring scheduling layer
- mirror embedded content into Qdrant

Implemented components:

- [packages/node-beta/api/main.py](D:\New folder\AXIOM\packages\node-beta\api\main.py): internal FastAPI service
- [packages/node-beta/api/routers](D:\New folder\AXIOM\packages\node-beta\api\routers): OHLCV, news, signals, and RAG endpoints
- [packages/node-beta/scheduler/main.py](D:\New folder\AXIOM\packages\node-beta\scheduler\main.py): APScheduler-based recurring jobs
- [packages/node-beta/scrapers](D:\New folder\AXIOM\packages\node-beta\scrapers): OHLCV, RSS, NSE, and embedding pipelines
- [packages/node-beta/storage/models.py](D:\New folder\AXIOM\packages\node-beta\storage\models.py): SQLAlchemy schema definitions
- [packages/node-beta/storage/migrations](D:\New folder\AXIOM\packages\node-beta\storage\migrations): Alembic migration history

Node Beta is the operational center of the system as currently implemented.

### Node Gamma

Primary responsibility:

- notify operators when system health degrades
- eventually expose bot commands and a light dashboard

Implemented components:

- [packages/node-gamma/bot/main.py](D:\New folder\AXIOM\packages\node-gamma\bot\main.py): Telegram notifier with a five-minute watchdog job
- [packages/node-gamma/bot/watchdog.py](D:\New folder\AXIOM\packages\node-gamma\bot\watchdog.py): alternate watchdog script with Docker, systemd, and HTTP checks

Current limitations:

- bot commands are not implemented
- dashboard is a stub
- the packaged systemd service file currently has malformed environment lines and should be treated as draft configuration

## Shared Package

[packages/shared](D:\New folder\AXIOM\packages\shared) contains the editable package `axiom-shared`, intended to host common constants, types, and utilities across all nodes.

Current reality:

- package scaffolding exists
- constants and types remain mostly placeholders

The shared package is still important architecturally because every node already depends on it through editable installs.

## Data Flow

### OHLCV Pipeline

1. Beta scheduler triggers NSE scraping jobs.
2. [packages/node-beta/scrapers/nse_scraper.py](D:\New folder\AXIOM\packages\node-beta\scrapers\nse_scraper.py) pulls recent OHLCV via `yfinance`.
3. Data is upserted into Postgres `ohlcv`.
4. Beta API exposes `/ohlcv` and `/ohlcv/latest` for consumers.

### News and RAG Pipeline

1. Beta scheduler triggers RSS and NSE announcement ingestion jobs.
2. Scrapers normalize article payloads.
3. [packages/node-beta/scrapers/rag_pipeline.py](D:\New folder\AXIOM\packages\node-beta\scrapers\rag_pipeline.py) deduplicates documents against Qdrant.
4. Embeddings are generated and stored in Qdrant `news_docs`.
5. Documents are mirrored into Postgres `news_articles`.
6. Beta `/rag/{ticker}` retrieves recent relevant context for Node Alpha and other consumers.

### Signal and Narration Flow

1. Beta scheduler calls Alpha `/infer` for configured tickers.
2. Alpha returns mocked ensemble values and derived directional labels.
3. Alpha `morning_brief.py` can combine signal data with Beta RAG context.
4. Gamma is positioned to relay health or narrative output to Telegram, though that full workflow is not yet wired end-to-end.

## Runtime Interfaces

### HTTP Endpoints

Node Alpha:

- `GET /health`
- `POST /infer`

Node Beta:

- `GET /`
- `GET /health`
- `GET /ohlcv`
- `GET /ohlcv/latest`
- `GET /news`
- `GET /signals`
- `GET /rag/{ticker}`

Node Gamma:

- no stable HTTP interface yet

### Storage Systems

Postgres tables defined in code:

- `stocks`
- `ohlcv`
- `signals`
- `news_articles`
- `paper_positions`
- `portfolio_snapshots`

Vector storage:

- Qdrant collection `news_docs` with cosine distance and payload indexes on `ticker`, `published_at`, `source`, and `url`

## Scheduling Model

Beta schedules multiple jobs in `Asia/Kolkata`:

- market close scrape at `15:35`, weekdays
- RAG NSE ingestion every 30 minutes from `08:00` to `16:30`, weekdays
- RAG RSS ingestion every 30 minutes offset by 15 minutes from `07:15` to `16:45`, weekdays
- premarket pipeline at `08:45`
- intraday signal checks every 15 minutes across market hours
- postmarket summary at `15:45`

Gamma schedules:

- watchdog health check every 5 minutes

## Deployment Model

The repo assumes separate hosts with shared code synchronized manually:

- Gamma deploy scripts copy `packages/shared` and `packages/node-gamma` to `192.168.1.50`
- Beta has systemd units for API and scheduler
- Nginx and Alpha deployment remain only lightly documented at this stage

## Risks And Architectural Gaps

- Node Alpha inference is mocked, so the system is not yet a true model-serving platform.
- News schema usage is inconsistent: some code uses `title` and `summary`, while SQLAlchemy models define `headline` and `body_snippet`.
- `packages/node-beta/storage/db.py` is still a TODO even though RAG mirroring imports `get_conn` from it.
- Node Gamma service configuration is incomplete and currently unsafe to rely on as-is.
- The repository contains generated build output and virtual environment artifacts, which can confuse source-of-truth discovery if not filtered out during ops work.
