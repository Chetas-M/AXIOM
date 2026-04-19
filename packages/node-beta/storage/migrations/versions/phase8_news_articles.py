"""phase8_schema

Revision ID: phase8_news_articles
Revises: 828ca2876536
Create Date: 2026-04-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'phase8_news_articles'
down_revision: Union[str, Sequence[str], None] = '828ca2876536'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop columns from Phase 3 schema that are obsolete
    op.drop_column('news_articles', 'title')
    op.drop_column('news_articles', 'summary')
    op.drop_column('news_articles', 'embedding_id')
    op.drop_column('news_articles', 'published_at')
    
    # Re-add as per Phase 8 definition
    op.add_column('news_articles', sa.Column('headline', sa.Text(), nullable=False, server_default=''))
    op.add_column('news_articles', sa.Column('body_snippet', sa.Text(), nullable=True))
    op.add_column('news_articles', sa.Column('published_at', sa.Integer(), nullable=True))
    op.alter_column('news_articles', 'url', existing_type=sa.Text(), nullable=False)
    # content_hash was already unique in Phase 3, so we keep it.


def downgrade() -> None:
    op.drop_column('news_articles', 'published_at')
    op.drop_column('news_articles', 'headline')
    op.drop_column('news_articles', 'body_snippet')
    
    op.add_column('news_articles', sa.Column('title', sa.Text(), nullable=False, server_default=''))
    op.add_column('news_articles', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('news_articles', sa.Column('embedding_id', sa.String(length=100), nullable=True))
    op.add_column('news_articles', sa.Column('published_at', sa.DateTime(), nullable=True))
    op.alter_column('news_articles', 'url', existing_type=sa.Text(), nullable=True)
