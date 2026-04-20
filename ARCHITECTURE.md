# AXIOM Architecture & Boundaries (v2.1)

## Node Responsibilities
- **Node Alpha (`packages/node-alpha`)**: Compute & ML. 
  - Runs ML runners (LSTM, Prophet, XGBoost) and RAG generation.
  - Manages LLM connections (Ollama).
  - Handles Celery workers for heavy tasks.

- **Node Beta (`packages/node-beta`)**: Data Ingestion & API.
  - Scrapes data (NSE, News, RSS).
  - Manages Storage (PostgreSQL, Qdrant).
  - Serves FastAPI (News, OHLCV, RAG, Signals).
  - Scheduler enqueues jobs to Redis.

- **Node Gamma (`packages/node-gamma`)**: Interfaces & Monitors.
  - Runs the bot/watchdog.
  - Serves the Dashboard.
  - Triggers lightweight, non-critical actions.

## Allowed Dependencies (Code Review Rules)
- **Node Alpha**:
  - *Allowed*: Read/write to PostgreSQL directly. Read jobs from Redis.
  - *Forbidden*: Must **not** require Beta API synchronously (prevent tight coupling).
- **Node Beta**:
  - *Allowed*: Enqueue jobs to Redis. Serve APIs to consumers.
  - *Forbidden*: Must **not** depend on Alpha's immediate availability (must degrade gracefully if Alpha is down/busy).
- **Node Gamma**:
  - *Constraint*: Must not be on the critical path. Acts only as a monitor/trigger layer.
