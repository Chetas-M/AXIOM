import subprocess
import httpx
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.alerts import alert_failure

load_dotenv()

CHECKS = []

def check(name):
    def decorator(fn):
        CHECKS.append((name, fn))
        return fn
    return decorator

@check("axiom-postgres (Docker)")
def check_postgres():
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", "axiom-postgres"],
        capture_output=True, text=True
    )
    if result.stdout.strip() != "true":
        raise RuntimeError("Container not running")

@check("axiom-qdrant (HTTP - Node Alpha)")
def check_qdrant():
    qdrant_url = os.environ.get("QDRANT_HEALTH_URL", "http://node-alpha:6333/")
    r = httpx.get(qdrant_url, timeout=5)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")

@check("axiom-api (FastAPI)")
def check_api():
    api_url = os.environ.get("API_HEALTH_URL", "http://localhost:8000/health")
    r = httpx.get(api_url, timeout=5)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")

@check("axiom-scheduler (systemd)")
def check_scheduler():
    result = subprocess.run(
        ["systemctl", "is-active", "axiom-scheduler"],
        capture_output=True, text=True
    )
    if result.stdout.strip() != "active":
        raise RuntimeError("Scheduler not active")

if __name__ == "__main__":
    failed = []
    for name, fn in CHECKS:
        try:
            fn()
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            failed.append(f"{name}: {e}")

    if failed:
        alert_failure("watchdog", "\n".join(failed))
        sys.exit(1)
    else:
        print("All checks passed.")
