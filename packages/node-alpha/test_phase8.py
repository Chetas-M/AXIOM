import requests
import logging
from rag.rag_enrichment import build_context_block
from llm.prompts import MORNING_BRIEF_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rag_endpoint():
    logger.info("Testing /rag/RELIANCE endpoint on node-beta...")
    resp = requests.get("http://node-beta:8000/rag/RELIANCE", params={"top_k": 5}, timeout=10)
    assert resp.ok, "RAG endpoint failed"
    data = resp.json()
    assert isinstance(data, list), "Response is not a list"
    if data:
        logger.info("RAG endpoint returned elements.")
    else:
        logger.warning("RAG endpoint returned an empty list (no docs).")

def test_context_block():
    logger.info("Testing build_context_block()...")
    ctx = build_context_block(["RELIANCE", "INFY"])
    assert isinstance(ctx, str) and len(ctx) > 0, "Context block empty or invalid"
    logger.info("Context block:\n%s", ctx)
    return ctx

def test_full_prompt(context_block):
    logger.info("Testing full MORNING_BRIEF prompt construction...")
    dummy_signals = "RELIANCE: LONG (conf: 80.5%)\nINFY: SHORT (conf: 65.0%)"
    
    prompt = MORNING_BRIEF_PROMPT.format(
        signals_block=dummy_signals,
        context_block=context_block
    )
    logger.info("--- CONSTRUCTED PROMPT ---")
    print(prompt)
    logger.info("--------------------------")
    return prompt

def test_llm_inference(prompt):
    logger.info("Sending prompt to local Qwen for narration...")
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen2.5:latest", "prompt": prompt, "stream": False}, # Example model name
            timeout=30
        )
        if resp.ok:
            narration = resp.json().get("response")
            logger.info("--- LLM FINAL OUTPUT ---")
            print(narration)
            logger.info("------------------------")
        else:
            logger.error(f"LLM returned status code {resp.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to LLM: {e}")

if __name__ == "__main__":
    try:
        test_rag_endpoint()
        ctx = test_context_block()
        prompt = test_full_prompt(ctx)
        test_llm_inference(prompt)
        logger.info("Phase 8 testing complete.")
    except AssertionError as e:
        logger.error(f"Test failed: {e}")
    except Exception as e:
        logger.error(f"Tests failed due to unexpected error: {e}")
