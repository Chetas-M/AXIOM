"""phase10_pgvector

Revision ID: phase10_pgvector
Revises: phase8_news_articles
Create Date: 2026-04-20 10:00:00.000000

"""
import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'phase10_pgvector'
down_revision: Union[str, Sequence[str], None] = 'phase8_news_articles'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2. Add new columns to news_articles
    op.add_column('news_articles', sa.Column('embedding', Vector(768), nullable=True))
    op.add_column('news_articles', sa.Column('embedded_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('news_articles', sa.Column('embed_model', sa.Text(), nullable=True))

    # 3. Create indexes
    op.create_index('ix_news_articles_ticker', 'news_articles', ['ticker'])
    op.create_index('ix_news_articles_published_at', 'news_articles', ['published_at'])
    try:
        lists = int(os.getenv("PGVECTOR_IVFFLAT_LISTS", "100"))
    except ValueError:
        lists = 100
    lists = max(1, min(lists, 10000))
    with op.get_context().autocommit_block():
        op.execute(
            "CREATE INDEX CONCURRENTLY ix_news_articles_embedding "
            "ON news_articles USING ivfflat (embedding vector_cosine_ops) "
            f"WITH (lists = {lists});"
        )


def downgrade() -> None:
    # 1. Drop indexes
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_news_articles_embedding;")
    op.drop_index('ix_news_articles_published_at', table_name='news_articles')
    op.drop_index('ix_news_articles_ticker', table_name='news_articles')

    # 2. Drop columns
    op.drop_column('news_articles', 'embed_model')
    op.drop_column('news_articles', 'embedded_at')
    op.drop_column('news_articles', 'embedding')

    # 3. Leave the extension (it might be used by other apps/future)
    # op.execute("DROP EXTENSION IF EXISTS vector")
