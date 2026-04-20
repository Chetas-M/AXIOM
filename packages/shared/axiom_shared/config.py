import os

# Config Contract (Environment Variables)
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://user:pass@localhost:5432/axiom")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Thresholds
AXIOM_CONFIDENCE_THRESHOLD = float(os.getenv("AXIOM_CONFIDENCE_THRESHOLD", "0.65"))
VIX_THRESHOLD = float(os.getenv("VIX_THRESHOLD", "25.0"))

# Time settings
TIMEZONE = os.getenv("TIMEZONE", "Asia/Calcutta")

# Application boundaries
ALPHA_WORKER_QUEUES = ["alpha-ml", "alpha-embeddings"]
BETA_API_URL = os.getenv("BETA_API_URL", "http://localhost:8000")

# Vector DB Backend toggle
VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "qdrant")
