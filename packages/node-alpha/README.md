# Node Alpha

## Purpose

Node Alpha is the compute-oriented service in AXIOM. It owns:

- inference serving
- LLM narration
- embedding-backed RAG assistance

## Code Map

- [api/main.py](D:\New folder\AXIOM\packages\node-alpha\api\main.py): FastAPI inference API
- [morning_brief.py](D:\New folder\AXIOM\packages\node-alpha\morning_brief.py): morning brief orchestration
- [llm/loader.py](D:\New folder\AXIOM\packages\node-alpha\llm\loader.py): model loader stub
- [rag/rag_enrichment.py](D:\New folder\AXIOM\packages\node-alpha\rag\rag_enrichment.py): pulls RAG context from Beta

## Dependencies

Declared in [requirements.txt](D:\New folder\AXIOM\packages\node-alpha\requirements.txt):

- `torch`
- `xgboost`
- `prophet`
- `qdrant-client`
- `fastapi`
- `uvicorn`
- `llama-cpp-python`
- editable install of `../shared`

## Run

```powershell
cd "D:\New folder\AXIOM\packages\node-alpha"
pip install -r requirements.txt
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001
```

Optional narrative flow:

```powershell
python morning_brief.py
```

## Endpoints

- `GET /health`
- `POST /infer`

## Current State

- The API works, but inference is mocked with random score generation.
- The LLM loader is still a TODO.
- This package is structurally important, but not yet production-complete.
