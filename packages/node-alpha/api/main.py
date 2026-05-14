import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import random

app = FastAPI(title="AXIOM Node Alpha API")

is_development = os.getenv("AXIOM_ENV", "development").lower() == "development"

class InferenceRequest(BaseModel):
    tickers: List[str]
    timeframe: str
    models: List[str]

class TickerSignal(BaseModel):
    signal: str
    confidence: float
    xgb: float
    lstm: float
    prophet: float
    is_mock: bool = False

@app.post("/infer", response_model=Dict[str, TickerSignal])
def run_inference(req: InferenceRequest):
    """
    Runs the ensemble and returns the predicted signals.
    """
    if not is_development:
        # Fail closed in production until real model runners are wired
        raise HTTPException(status_code=501, detail="Real model runners are not yet linked to /infer.")

    response = {}
    for ticker in req.tickers:
        # Mocking the ML pipeline returns for paper trading validation
        xgb_val = random.uniform(0.5, 0.95)
        lstm_val = random.uniform(0.4, 0.9)
        prophet_val = random.uniform(0.3, 0.8)
        
        avg_conf = (xgb_val + lstm_val + prophet_val) / 3.0
        
        response[ticker] = TickerSignal(
            signal="LONG" if avg_conf > 0.65 else "SHORT",
            confidence=avg_conf,
            xgb=xgb_val,
            lstm=lstm_val,
            prophet=prophet_val,
            is_mock=True
        )
    return response

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "node-alpha"}

