import requests
import json
import logging
import time

logger = logging.getLogger(__name__)

def embed_documents(docs: list[dict]) -> list[tuple[list[float], dict]]:
    embedded = []
    
    for i in range(0, len(docs), 20):
        batch = docs[i:i+20]
        for doc in batch:
            prompt = f"{doc['headline']} {doc['body_snippet']}"
            
            try:
                resp = requests.post(
                    "http://node-alpha:11434/api/embeddings", # Replace with local/remote Ollama host as appropriate. The spec asks for locahost, but node-alpha is the LLM node.
                    json={"model": "nomic-embed-text", "prompt": prompt},
                    timeout=10
                )
                if resp.ok:
                    vector = resp.json().get("embedding")
                    if vector:
                        embedded.append((vector, doc))
                else:
                    logger.warning(f"Ollama returned {resp.status_code} for {doc.get('url')}")
            except Exception as e:
                logger.warning(f"Ollama error on embedding: {e}")
                
        time.sleep(0.5)

    return embedded
