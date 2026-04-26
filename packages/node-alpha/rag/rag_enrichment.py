from datetime import datetime

import requests
from axiom_shared.config import BETA_API_URL


def _get_beta_api_base_url() -> str:
    return BETA_API_URL.rstrip("/")


def build_context_block(tickers: list[str]) -> str:
    """
    For each ticker in the watchlist, call node-beta RAG endpoint,
    format results into the context_block string.
    """
    lines = []
    base_url = _get_beta_api_base_url()
    for ticker in tickers:
        try:
            resp = requests.get(
                f"{base_url}/rag/{ticker}",
                params={"top_k": 5},
                timeout=10,
            )
            docs = resp.json() if resp.ok else []
            for doc in docs:
                ts = datetime.fromtimestamp(doc["published_at"]).strftime("%Y-%m-%d %H:%M")
                lines.append(f"[{ticker}] ({ts}) {doc['source']} - {doc['headline']}")
        except requests.RequestException:
            # Fall back gracefully per instruction
            continue

    return "\n".join(lines) if lines else "No news context retrieved."
