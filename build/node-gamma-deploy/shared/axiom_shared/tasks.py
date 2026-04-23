from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone

class BaseTask(BaseModel):
    enqueued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    run_id: str

class EmbedTask(BaseTask):
    article_ids: Optional[List[int]] = None
    since_ts: Optional[int] = None

class InferTask(BaseTask):
    date: str # YYYY-MM-DD
    tickers: List[str]

class BriefTask(BaseTask):
    date: str # YYYY-MM-DD
    tickers: List[str]