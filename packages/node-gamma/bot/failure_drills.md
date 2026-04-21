# AXIOM Failure Drills Runbook

## 1. Matrix Watchdog Alerting
Test that the watchdog script successfully outputs the correct alert levels.
\\\ash
python packages/node-gamma/bot/watchdog.py
\\\

## 2. Redis Failure (CRITICAL)
- **Action**: Stop Redis service (docker stop axiom-redis or systemctl stop redis-server).
- **Expected Outcome**: 
  - Watchdog script raises a **CRITICAL: Redis down** alert.
  - Celery attempts to reconnect and logs errors. Queueing operations immediately fail safely (no silent drops).

## 3. Ollama Failure (HIGH)
- **Action**: Stop the ollama service on 
ode-alpha.
- **Expected Outcome**:
  - Watchdog script raises a **HIGH: Ollama down** alert (assuming node-alpha itself is reachable).
  - Any inflight text generation tasks fail, logging retries and backoffs.

## 4. Node Alpha Outage (Node Down Mid-Run)
- **Action**: Power off or completely disconnect 
ode-alpha midway through daily inference.
- **Expected Outcome**:
  - Watchdog avoids spamming HIGH Celery/Ollama alerts, as ping timeouts silently suppress child alerts.
  - 
ode-beta enqueuing tasks will pile up in the Redis broker.
  - Upon 
ode-alpha recovery, tasks resume draining from Redis broker where they left off.

## 5. Regime Gate (INFO)
- **Action**: Override VIX via manual SQL: UPDATE market_regime SET vix = 26 WHERE date = CURRENT_DATE;
- **Expected Outcome**:
  - The inference task receives the regime trigger, emits **INFO: Regime gate triggered**.
  - SignalRuns table registers SKIPPED_REGIME.
