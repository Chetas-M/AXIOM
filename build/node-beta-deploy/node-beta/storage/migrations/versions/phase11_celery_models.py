"""phase11_celery_models

Revision ID: phase11_celery_models
Revises: phase10_pgvector
Create Date: 2026-04-20 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'phase11_celery_models'
down_revision: Union[str, Sequence[str], None] = 'phase10_pgvector'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Update signals table
    op.add_column('signals', sa.Column('model_votes', postgresql.JSONB(), nullable=True))
    op.add_column('signals', sa.Column('features_version', sa.String(length=50), nullable=True))
    op.add_column('signals', sa.Column('model_version', sa.String(length=50), nullable=True))

    # 2. Create morning_briefs table
    op.create_table(
        'morning_briefs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('ticker_scope', sa.String(length=20), nullable=True),
        sa.Column('narrative', sa.Text(), nullable=False),
        sa.Column('citations', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'ticker_scope', name='uq_morning_brief_date_scope')
    )

def downgrade() -> None:
    op.drop_table('morning_briefs')
    op.drop_column('signals', 'model_version')
    op.drop_column('signals', 'features_version')
    op.drop_column('signals', 'model_votes')