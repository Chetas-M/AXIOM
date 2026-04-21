"""phase12 regime

Revision ID: phase12_regime
Revises: phase11_celery_models
Create Date: 2026-04-20 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

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
    op.create_table('paper_positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(length=20), nullable=False),
        sa.Column('direction', sa.String(length=10), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=True),
        sa.Column('entry_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=10), nullable=True),
        sa.Column('exit_price', sa.Float(), nullable=True),
        sa.Column('exit_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pnl', sa.Float(), nullable=True),
        sa.Column('signal_confidence', sa.Float(), nullable=True),
        sa.Column('model_votes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('portfolio_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('total_capital', sa.Float(), nullable=True),
        sa.Column('deployed_capital', sa.Float(), nullable=True),
        sa.Column('unrealized_pnl', sa.Float(), nullable=True),
        sa.Column('realized_pnl', sa.Float(), nullable=True),
        sa.Column('open_positions', sa.Integer(), nullable=True),
        sa.Column('daily_sharpe', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.add_column('signals', sa.Column('is_tradeable', sa.Integer(), nullable=False, server_default=sa.text('1')))

def downgrade() -> None:
    op.drop_column('signals', 'is_tradeable')
    op.drop_table('portfolio_snapshots')
    op.drop_table('paper_positions')
    op.drop_table('signal_runs')
    op.drop_table('market_regime')
