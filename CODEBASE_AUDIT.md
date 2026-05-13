# AXIOM Codebase Audit

Date: 2026-05-13

## Executive Summary

AXIOM has a sensible three-node shape, but it is not production-ready yet. The largest risks are a committed Telegram credential, unauthenticated internal APIs exposed by systemd on `0.0.0.0`, mock inference paths that can create operational trading records, brittle migrations/schema drift, and tests that mix live integration calls with unit tests.

This review focused on source under `packages/`, `infra/`, `tests/`, and top-level docs/scripts. Generated deployment copies under `build/` were treated as derived artifacts.

## Critical

### C1. Telegram Bot Token Is Present In A Shell Script

- Location: `update-gamma.sh:2`
- Evidence: the script writes a concrete `TELEGRAM_BOT_TOKEN` value into `/etc/systemd/system/axiom-gamma-bot.service`.
- Impact: anyone with repository access can control or abuse that bot until the token is revoked. If the repo was ever pushed, assume the token is compromised.
- Fix: revoke/rotate the Telegram token immediately, delete `update-gamma.sh` or replace it with an environment-file based workflow, and purge the token from git history if it was committed or shared.

### C2. Internal Financial APIs Have No Authentication Or Authorization Boundary

- Locations: `packages/node-beta/api/main.py:48`, `packages/node-beta/api/routers/ohlcv.py:10`, `packages/node-beta/api/routers/news.py:9`, `packages/node-beta/api/routers/signals.py:9`, `packages/node-beta/api/routers/rag.py:12`
- Evidence: all routers are included without `Depends()`/`Security()` dependencies, and the routes expose market data, signals, and RAG content directly.
- Impact: if the service is reachable outside a trusted private network, any caller can enumerate signals/news/context. This is especially risky because the service unit binds Uvicorn to all interfaces.
- Fix: add a shared FastAPI auth dependency for non-health routes, attach it at router inclusion time, and document which endpoints are intentionally public.

## High

### H1. Uvicorn Binds To All Interfaces While Docs Are Enabled

- Locations: `infra/systemd/axiom-beta-api.service:11`, `packages/node-beta/api/main.py:16`, `packages/node-beta/api/main.py:20`
- Evidence: systemd starts `uvicorn api.main:app --host 0.0.0.0 --port 8000`, and FastAPI docs/redoc remain enabled.
- Impact: an internal API can become discoverable on the network, with `/docs` advertising schemas and endpoints.
- Fix: bind to localhost behind a controlled reverse proxy, add `TrustedHostMiddleware`, and disable or protect `/docs`, `/redoc`, and `/openapi.json` outside development.

### H2. Mock Inference Can Produce Tradeable Operational Data

- Locations: `packages/node-alpha/api/main.py:26`, `packages/node-alpha/api/main.py:28`, `packages/node-alpha/worker/tasks.py:103`, `packages/node-alpha/worker/tasks.py:113`
- Evidence: `/infer` uses random model scores, and the Celery worker uses fixed dummy predictions before writing `Signal` rows.
- Impact: paper trading and downstream summaries can act on synthetic confidence values as if they came from the actual model ensemble.
- Fix: gate mock inference behind an explicit development flag, mark mock signals as non-tradeable, and fail closed in production until real model runners are wired.

### H3. Duplicate Signal Writes Can Fail Entire Inference Runs

- Locations: `packages/node-alpha/worker/tasks.py:113`, `packages/node-alpha/worker/tasks.py:135`, `packages/node-beta/storage/models.py:89`
- Evidence: `Signal` has a unique constraint on `(ticker, date, signal_type)`, but `infer_signals()` blindly `session.add()`s a new row for each ticker/run.
- Impact: rerunning an intraday task for the same ticker/date/type raises an integrity error, rolls back every signal in the batch, and may leave `SignalRun` stale.
- Fix: upsert by `(ticker, date, signal_type)` or update the existing row in the same transaction before committing.

### H4. Alembic Phase 3 Migration Can Break On Existing Data

- Location: `packages/node-beta/storage/migrations/versions/828ca2876536_phase3_schema.py:24`
- Evidence: the migration adds non-null `title` and `content_hash` columns to `news_articles` without defaults or a backfill before dropping `headline`.
- Impact: upgrading a database with existing news rows can fail, blocking deployments and leaving schema drift.
- Fix: add nullable columns first, backfill from existing fields, create hashes, then enforce `nullable=False` and constraints.

## Medium

### M1. RAG Endpoint Swallows Database Errors And Returns Empty Success

- Location: `packages/node-beta/api/routers/rag.py:44`
- Evidence: all exceptions are caught, logged, and converted to `[]`.
- Impact: upstream brief generation cannot distinguish “no relevant news” from database/query failure, so outages become silent degraded output.
- Fix: catch expected database exceptions narrowly and return a 503/500 for backend failures.

### M2. Query Parameters Are Under-Constrained

- Locations: `packages/node-beta/api/routers/rag.py:13`, `packages/node-beta/api/routers/news.py:13`, `packages/node-beta/api/routers/ohlcv.py:15`
- Evidence: `top_k` and `max_age_hours` have no bounds; several `limit` fields only set max values and no lower bound.
- Impact: callers can request negative/huge windows or odd limits, causing unnecessary database work or confusing output.
- Fix: use `Query(..., ge=1, le=...)` and ticker regex/length validation.

### M3. Dependencies Are Mostly Unpinned

- Locations: `packages/node-alpha/requirements.txt:1`, `packages/node-beta/requirements.txt:1`, `packages/node-gamma/requirements.txt:1`
- Evidence: most dependencies are floating; only a few FastAPI/Uvicorn/SQLAlchemy entries in beta are pinned.
- Impact: installs are non-reproducible and can pull breaking or vulnerable dependency versions unexpectedly.
- Fix: use constraints/lock files per node, pin security-sensitive packages, and add a dependency audit step to CI.

### M4. Production Service Units Lack Hardening

- Locations: `infra/systemd/axiom-beta-api.service:5`, `infra/systemd/axiom-beta-scheduler.service:5`, `infra/systemd/axiom-gamma-bot.service:5`
- Evidence: units run without sandboxing options such as `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem`, `ReadWritePaths`, or restart-rate controls.
- Impact: a compromised process gets broader filesystem/process access than necessary.
- Fix: add service hardening appropriate to each node and restrict writable paths to logs/state only.

## Bugs And Reliability

### B1. Pytest Collection Includes A Live Integration Script

- Location: `packages/node-alpha/test_phase8.py:9`
- Evidence: `test_rag_endpoint()` calls `http://node-beta:8000/rag/RELIANCE` directly, while `test_full_prompt(context_block)` and `test_llm_inference(prompt)` expect missing fixtures.
- Impact: `python -m pytest -q` currently fails with `1 failed, 2 errors`.
- Fix: move this file under an integration test folder with skips/env guards, or convert it to real pytest fixtures/mocks.

### B2. Scheduler Job IDs Are Missing For Several Cron Jobs

- Locations: `packages/node-beta/scheduler/main.py:106`, `packages/node-beta/scheduler/main.py:109`, `packages/node-beta/scheduler/main.py:114`
- Evidence: three jobs are added without stable `id`/`replace_existing`.
- Impact: scheduler restarts or future persistent job stores can create duplicate scheduled jobs.
- Fix: assign stable IDs and `replace_existing=True` consistently.

### B3. Watchdog Freshness Check Mixes Naive And Aware Datetimes

- Location: `packages/node-gamma/bot/watchdog.py:68`
- Evidence: `datetime.now()` is naive, while `latest.created_at` may be timezone-aware depending on DB/driver.
- Impact: the freshness check can raise and report scraper failure even when data is fresh.
- Fix: use `datetime.now(timezone.utc)` and normalize database timestamps.

### B4. Local Build Artifacts And Virtualenv Are Present In The Repo Workspace

- Locations: `build/`, `venv/`
- Evidence: generated deployment copies and a virtualenv are present, and `rg --files` shows duplicated source under `build/`.
- Impact: reviews and searches are noisy, and stale generated copies can be mistaken for source of truth.
- Fix: expand `.gitignore`, keep generated archives outside source review paths, and avoid committing environment output.

## Verification

- Ran `python -m pytest -q`.
- Result: `6 passed, 1 failed, 2 errors, 1 warning`.
- Main failing area: `packages/node-alpha/test_phase8.py` live integration/scratch tests.

