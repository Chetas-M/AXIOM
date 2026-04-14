from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional
import random

app = FastAPI(title="AXIOM Node Alpha API")

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

@app.post("/infer", response_model=Dict[str, TickerSignal])
def run_inference(req: InferenceRequest):
    """
    Runs the ensemble and returns the predicted signals.
    """
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
            prophet=prophet_val
        )
    return response

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "node-alpha"}

