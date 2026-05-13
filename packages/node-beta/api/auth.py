"""
Shared authentication dependency for AXIOM internal API routes.

How it works
------------
* Every non-health route requires a valid API key passed via the
  ``X-API-Key`` header (or the ``api_key`` query param as fallback).
* The expected key is loaded from the ``AXIOM_API_KEY`` env-var at
  startup.  If the env-var is missing the application will **refuse to
  start**, preventing accidental unauthenticated deployments.

Intentionally public routes (``/health``, ``/``) are excluded from this
dependency by attaching it only at router-inclusion time in ``main.py``.
"""

import os
import secrets
import logging
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load the expected API key from the environment
# ---------------------------------------------------------------------------

_API_KEY: Optional[str] = os.getenv("AXIOM_API_KEY")

if not _API_KEY:
    logger.critical(
        "AXIOM_API_KEY is not set.  Refusing to start with unauthenticated "
        "financial data endpoints.  Set the env-var and restart."
    )
    raise SystemExit(
        "FATAL: AXIOM_API_KEY environment variable is required but not set."
    )

# ---------------------------------------------------------------------------
# FastAPI security schemes
# ---------------------------------------------------------------------------

_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)
_query_scheme = APIKeyQuery(name="api_key", auto_error=False)


async def require_api_key(
    header_key: Optional[str] = Security(_header_scheme),
    query_key: Optional[str] = Security(_query_scheme),
) -> str:
    """Dependency that enforces a valid API key on every protected route.

    Accepts the key from:
      1. ``X-API-Key`` request header  (preferred)
      2. ``?api_key=`` query parameter (convenience / dev tooling)

    Returns the validated key so downstream handlers can log caller
    identity if needed.
    """
    provided = header_key or query_key

    if not provided:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key – supply via X-API-Key header or api_key query param.",
        )

    # Constant-time comparison to prevent timing side-channels
    if not secrets.compare_digest(provided, _API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return provided
