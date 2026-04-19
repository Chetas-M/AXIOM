import requests
from datetime import datetime

def build_context_block(tickers: list[str]) -> str:
    """
    For each ticker in the watchlist, call node-beta RAG endpoint,
    format results into the context_block string.
    """
    lines = []
    for ticker in tickers:
        try:
            resp = requests.get(
                f"http://node-beta:8000/rag/{ticker}",  # Assumes node-beta is running on 8000
                params={"top_k": 5},
                timeout=10
            )
            docs = resp.json() if resp.ok else []
            for doc in docs:
                ts = datetime.fromtimestamp(doc["published_at"]).strftime("%Y-%m-%d %H:%M")
                lines.append(f"[{ticker}] ({ts}) {doc['source']} — {doc['headline']}")
        except requests.RequestException:
            # Fall back gracefully per instruction
            continue
            
    return "\n".join(lines) if lines else "No news context retrieved."
