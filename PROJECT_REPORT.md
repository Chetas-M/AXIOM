# AXIOM: Project Status and Architecture Report

## 1. Executive Summary

AXIOM is a distributed financial intelligence system focused on Indian-market data ingestion, internal analytics APIs, machine-learning-assisted signal generation, and operator-facing alerting. The repository is organized as a three-node Python monorepo:

- Node Alpha for inference, narration, and RAG-adjacent compute
- Node Beta for ingestion, storage, APIs, and scheduling
- Node Gamma for Telegram-based monitoring and future interaction surfaces

The system already has a solid structural foundation, but it is still in an implementation phase rather than a finished production state. Some parts are operational, while other parts remain stubs or placeholders.

## 2. Three-Node Architecture

### 2.1 Node Alpha: Compute and Inference

- Hardware target: high-performance machine such as a Ryzen 7 plus GPU
- Main responsibilities:
- serve inference responses through a FastAPI API
- host local model-serving dependencies for narration and embeddings
- consume contextual data from Node Beta's RAG endpoint

Current implementation status:

- `packages/node-alpha/api/main.py` exposes `/infer` and `/health`
- `packages/node-alpha/morning_brief.py` orchestrates a morning narrative flow
- the LLM loader remains a stub
- inference output is currently mocked rather than backed by a real ensemble runtime

### 2.2 Node Beta: Data Plane and Orchestration

- Hardware target: always-on server such as an i5-class machine
- Main responsibilities:
- scrape OHLCV and news data
- store operational records in PostgreSQL
- expose the internal FastAPI surface
- run recurring APScheduler jobs
- maintain vector-searchable context in Qdrant

Current implementation status:

- `packages/node-beta/api/` contains the core internal API
- `packages/node-beta/scheduler/main.py` runs timed ingestion and orchestration jobs
- `packages/node-beta/scrapers/` contains NSE, RSS, and news ingestion paths
- Alembic migrations and SQLAlchemy models are present
- Node Beta is the most complete and operationally central node in the codebase

### 2.3 Node Gamma: Monitoring and Interaction

- Hardware target: low-power always-on machine
- Main responsibilities:
- run watchdog health checks
- send Telegram alerts
- eventually host bot commands and dashboard functionality

Current implementation status:

- `packages/node-gamma/bot/main.py` runs a watchdog loop with Telegram integration
- command handling remains a placeholder
- the dashboard app is still a stub

### 2.4 Shared and Infrastructure

- `packages/shared/` contains the editable `axiom-shared` package for common types and constants
- `infra/` contains deployment scripts, Nginx notes, and systemd unit files

Current implementation status:

- shared packaging is present, but many shared constants and types are still placeholders
- Beta systemd assets are close to usable
- Gamma systemd configuration still needs cleanup before production use
- Alpha and Beta deploy scripts are still placeholders

## 3. How the System Works

### 3.1 Ingestion Phase

Node Beta periodically runs scheduled jobs that pull:

- OHLCV data through `yfinance`
- RSS and market-news feeds
- NSE announcement data for RAG-style enrichment flows

Structured data is written into PostgreSQL tables such as `ohlcv`, `signals`, and `news_articles`.

### 3.2 Context and Search Phase

Node Beta's RAG pipeline:

- embeds documents
- stores vectors in Qdrant collection `news_docs`
- mirrors relevant metadata back into PostgreSQL

This enables ticker-scoped contextual retrieval through the `/rag/{ticker}` endpoint.

### 3.3 Inference and Narrative Phase

Node Beta can call Node Alpha's `/infer` endpoint during scheduled jobs. Node Alpha can also build morning-brief context by querying Beta's RAG endpoint.

Current reality:

- cross-node HTTP calls exist
- inference is mocked
- narrative generation is partially scaffolded around a local model endpoint, but not yet a fully validated production workflow

### 3.4 Monitoring Phase

Node Gamma checks Alpha and Beta health endpoints and sends Telegram alerts when services are unavailable. This provides lightweight operator visibility without making Gamma a critical dependency for core ingestion or storage.

## 4. Work Completed To Date

The repository already includes meaningful implementation progress:

- monorepo structure established for Alpha, Beta, Gamma, and shared code
- Node Beta FastAPI service, routers, scheduler, scrapers, migrations, and ORM models
- Node Alpha API scaffolding, morning-brief flow, and RAG integration hooks
- Node Gamma watchdog process and Telegram alerting path
- deploy and service scaffolding under `infra/`
- documentation set covering architecture, setup, runtime flows, and package-level responsibilities

## 5. Important Gaps and Risks

The main gaps visible in the current repository are:

- Node Alpha inference is still mocked
- Node Alpha model loader is not implemented
- Node Gamma commands and dashboard are not implemented
- some storage and integration code on Beta is incomplete, especially `storage/db.py`
- there is schema drift between some news-related SQL queries and ORM field names
- some infra artifacts are present as placeholders rather than fully operational deployment assets

## 6. Recommended Next Steps

1. Replace mocked Alpha inference with a real model-serving path.
2. Align Beta database schema usage so SQL queries and ORM models use the same field names.
3. Finish Node Beta connection utilities and validate end-to-end ingestion plus RAG mirroring.
4. Complete Node Gamma command handling and decide whether the dashboard belongs in this node or elsewhere.
5. Harden production deployment assets, especially Alpha/Beta deploy scripts and Gamma systemd configuration.
