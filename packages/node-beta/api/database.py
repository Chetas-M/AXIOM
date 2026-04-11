import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import urllib.parse

load_dotenv(os.path.expanduser("~/axiom/.env"))

pw = urllib.parse.quote_plus(os.environ.get("POSTGRES_PASSWORD", ""))
user = os.environ.get("POSTGRES_USER", "axiom")
db = os.environ.get("POSTGRES_DB", "axiom")
host = os.environ.get("POSTGRES_HOST", "localhost")
port = os.environ.get("POSTGRES_PORT", "5432")
base_url = os.environ.get("DATABASE_URL", f"postgresql://{user}:{pw}@{host}:{port}/{db}")

_url = base_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(_url, pool_size=5, max_overflow=10, echo=False)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
