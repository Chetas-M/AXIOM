import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from axiom_shared.config import REDIS_URL

from celery import Celery

celery_app = Celery("axiom", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.update(
    task_routes={
        "worker.embed_backlog": {"queue": "embed_backlog"},
        "worker.infer_signals": {"queue": "infer_signals"},
        "worker.morning_brief": {"queue": "morning_brief"},
    },
    task_time_limit=3600,
)
