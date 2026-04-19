import requests
import logging
import os
from llm.prompts import MORNING_BRIEF_PROMPT
from rag.rag_enrichment import build_context_block
from llm.loader import get_llm_client  # Assuming exist or mockup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_signals():
    # Mocking existing signal fetch per task description
    return {
        "RELIANCE": {"signal": "LONG", "confidence": 0.82},
        "INFY": {"signal": "SHORT", "confidence": 0.70}
    }

def format_signals(signals_dict):
    lines = []
    for t, s in signals_dict.items():
        lines.append(f"{t}: {s['signal']} (conf: {s['confidence']*100:.1f}%)")
    return "\n".join(lines)

def send_telegram(text: str):
    logger.info("Sending to telegram: \n%s", text)

def run_morning_brief():
    logger.info("Fetching signals...")
    signals = fetch_signals()
    tickers = list(signals.keys())
    
    logger.info("Building context block for tickers: %s", tickers)
    try:
        context_block = build_context_block(tickers)
    except Exception as e:
        logger.warning(f"RAG failed, falling back to signals only: {e}")
        context_block = "No recent news found — signal is quantitative only."

    signals_block = format_signals(signals)
    prompt = MORNING_BRIEF_PROMPT.format(
        signals_block=signals_block,
        context_block=context_block
    )

    logger.info("Calling Qwen with enriched prompt...")
    # Mocking Qwen call per existing flow implied
    try:
        # Assuming local Ollama call to Qwen or similar
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen", "prompt": prompt, "stream": False},
            timeout=30
        )
        if resp.ok:
            narration = resp.json().get("response", "Could not generate brief.")
        else:
            narration = "LLM Generation failed."
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        narration = "LLM unavailable."

    send_telegram(narration)

if __name__ == "__main__":
    run_morning_brief()