"""phase12 regime

Revision ID: phase12_regime
Revises: phase11_celery_models
Create Date: 2026-04-20 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'phase12_regime'
down_revision = 'phase11_celery_models'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('market_regime',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('vix', sa.Float(), nullable=False),
        sa.Column('regime', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date')
    )
    op.create_table('signal_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date')
    )
    op.add_column('signals', sa.Column('is_tradeable', sa.Integer(), nullable=True, server_default='1'))

def downgrade() -> None:
    op.drop_column('signals', 'is_tradeable')
    op.drop_table('signal_runs')
    op.drop_table('market_regime')
