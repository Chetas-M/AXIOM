# Setup and Operations

## Supported Operating Model

The codebase is organized around three separately deployed Python applications. The intended setup is:

- Linux host with GPU or strong local compute for Node Alpha
- Linux server for Node Beta with Postgres access and always-on scheduler runtime
- low-power Linux host or small box for Node Gamma

Development can still be done on one machine if you replace internal hostnames such as `node-alpha` and `node-beta` with reachable local addresses.

## Shared Prerequisites

- Python 3.11+ recommended
- `pip`
- network reachability between nodes
- Postgres for Beta
- Qdrant for vector search
- optional Ollama or equivalent local model runtime for Alpha embedding and narration flows

## Repository Bootstrap

From the repo root:

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -e .\packages\shared
```

Each node has its own dependency set, so install them separately when working on that node:

```powershell
pip install -r .\packages\node-alpha\requirements.txt
pip install -r .\packages\node-beta\requirements.txt
pip install -r .\packages\node-gamma\requirements.txt
```

## Environment Variables

### Node Beta

Used directly in [packages/node-beta/api/database.py](D:\New folder\AXIOM\packages\node-beta\api\database.py):

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `DATABASE_URL`

Used elsewhere in Beta or related health checks:

- `QDRANT_HOST`
- `QDRANT_PORT`
- `QDRANT_HEALTH_URL`
- `API_HEALTH_URL`

The code attempts to load Beta config from `~/axiom/.env`, and the systemd units also reference `/home/chetas/axiom/.env`.

### Node Gamma

Used directly in [packages/node-gamma/bot/main.py](D:\New folder\AXIOM\packages\node-gamma\bot\main.py):

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### Node Alpha

Node Alpha currently relies more on fixed hostnames than env configuration. If you operationalize Alpha further, externalize at least:

- model endpoint URL
- Qdrant host and port
- Node Beta base URL

## Starting Services Manually

### Node Alpha

```powershell
cd "D:\New folder\AXIOM\packages\node-alpha"
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001
```

Optional script:

```powershell
python morning_brief.py
```

### Node Beta API

```powershell
cd "D:\New folder\AXIOM\packages\node-beta"
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Node Beta Scheduler

```powershell
cd "D:\New folder\AXIOM\packages\node-beta"
python scheduler/main.py
```

### Node Gamma

```powershell
cd "D:\New folder\AXIOM\packages\node-gamma"
python bot/main.py
```

## Database And Vector Store

### Postgres

Beta expects Postgres for `ohlcv`, `signals`, `news_articles`, and related operational tables.

Migration assets live in [packages/node-beta/storage/migrations](D:\New folder\AXIOM\packages\node-beta\storage\migrations). Typical usage:

```powershell
cd "D:\New folder\AXIOM\packages\node-beta"
alembic upgrade head
```

### Qdrant

Initialize vector storage with:

```powershell
cd "D:\New folder\AXIOM\packages\node-beta"
python storage/qdrant_client.py
```

This prepares the `news_docs` collection and payload indexes if they do not already exist.

## Production Service Files

Available systemd assets:

- [infra/systemd/axiom-beta-api.service](D:\New folder\AXIOM\infra\systemd\axiom-beta-api.service)
- [infra/systemd/axiom-beta-scheduler.service](D:\New folder\AXIOM\infra\systemd\axiom-beta-scheduler.service)
- [infra/systemd/axiom-gamma-bot.service](D:\New folder\AXIOM\infra\systemd\axiom-gamma-bot.service)

Beta units are the closest to production-ready. Gamma's unit should be corrected before use because its `Environment=` lines are malformed.

## Deployment Scripts

Existing scripts:

- [infra/scripts/deploy-alpha.sh](D:\New folder\AXIOM\infra\scripts\deploy-alpha.sh)
- [infra/scripts/deploy-beta.sh](D:\New folder\AXIOM\infra\scripts\deploy-beta.sh)
- [infra/scripts/deploy-gamma.sh](D:\New folder\AXIOM\infra\scripts\deploy-gamma.sh)
- [infra/scripts/deploy-gamma.ps1](D:\New folder\AXIOM\infra\scripts\deploy-gamma.ps1)

Current state:

- Gamma deploy helpers are functional SCP-based copy scripts.
- Alpha and Beta deploy scripts are placeholders and need implementation before they can be used as an official runbook.

## Operational Checks

Useful health endpoints:

- Beta: `http://<host>:8000/health`
- Alpha: `http://<host>:8001/health`

Gamma and Beta both contain watchdog logic:

- [packages/node-gamma/bot/main.py](D:\New folder\AXIOM\packages\node-gamma\bot\main.py)
- [packages/node-gamma/bot/watchdog.py](D:\New folder\AXIOM\packages\node-gamma\bot\watchdog.py)

## Known Setup Hazards

- Internal service URLs are hard-coded in several modules, so local development may require hostfile entries or source edits.
- The repo root includes `venv/` and generated build output, which should not be mistaken for the active application source.
- Some Beta modules depend on `storage.db.get_conn`, but that file is still marked TODO.
- The codebase mixes sync and async database access patterns; keep that in mind while debugging connection issues.
