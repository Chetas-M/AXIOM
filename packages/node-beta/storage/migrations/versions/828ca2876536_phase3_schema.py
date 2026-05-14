"""phase3_schema

Revision ID: 828ca2876536
Revises: 8f43abbc39a8
Create Date: 2026-04-09 17:53:10.664687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '828ca2876536'
down_revision: Union[str, Sequence[str], None] = '8f43abbc39a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add columns as nullable first
    op.add_column('news_articles', sa.Column('title', sa.Text(), nullable=True))
    op.add_column('news_articles', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('news_articles', sa.Column('content_hash', sa.String(length=64), nullable=True))
    
    # 2. Backfill data
    op.execute(
        """
        UPDATE news_articles
        SET title = headline,
            content_hash = md5(url || headline)
        """
    )

    # 3. Enforce not-null
    op.alter_column('news_articles', 'title', nullable=False)
    op.alter_column('news_articles', 'content_hash', nullable=False)

    op.alter_column('news_articles', 'ticker',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
    op.drop_constraint('uq_news_url', 'news_articles', type_='unique')
    op.create_unique_constraint('uq_news_content_hash', 'news_articles', ['content_hash'])
    op.drop_column('news_articles', 'headline')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('news_articles', sa.Column('headline', sa.TEXT(), autoincrement=False, nullable=True))
    op.execute(
        """
        UPDATE news_articles
        SET headline = title
        """
    )
    op.alter_column('news_articles', 'headline', nullable=False)
    
    op.drop_constraint('uq_news_content_hash', 'news_articles', type_='unique')
    op.create_unique_constraint('uq_news_url', 'news_articles', ['url'])
    op.alter_column('news_articles', 'ticker',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
    op.drop_column('news_articles', 'content_hash')
    op.drop_column('news_articles', 'summary')
    op.drop_column('news_articles', 'title')
