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
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    with op.batch_alter_table('news_articles') as batch_op:
        batch_op.alter_column(
            'title',
            existing_type=sa.Text(),
            existing_nullable=False,
            existing_server_default=sa.text("''"),
            new_column_name='headline',
            server_default='',
        )
        batch_op.alter_column(
            'summary',
            existing_type=sa.Text(),
            existing_nullable=True,
            new_column_name='body_snippet',
        )
        batch_op.add_column(sa.Column('published_at_new', sa.Integer(), nullable=True))

    if dialect_name == 'postgresql':
        op.execute(
            """
            UPDATE news_articles
            SET published_at_new = CAST(EXTRACT(EPOCH FROM published_at) AS INTEGER)
            WHERE published_at IS NOT NULL
            """
        )
    elif dialect_name == 'sqlite':
        op.execute(
            """
            UPDATE news_articles
            SET published_at_new = CAST(strftime('%s', published_at) AS INTEGER)
            WHERE published_at IS NOT NULL
            """
        )
    else:
        op.execute(
            """
            UPDATE news_articles
            SET published_at_new = UNIX_TIMESTAMP(published_at)
            WHERE published_at IS NOT NULL
            """
        )

    with op.batch_alter_table('news_articles') as batch_op:
        batch_op.drop_column('published_at')
        batch_op.drop_column('embedding_id')
        batch_op.alter_column(
            'published_at_new',
            existing_type=sa.Integer(),
            existing_nullable=True,
            new_column_name='published_at',
        )
        batch_op.alter_column('url', existing_type=sa.Text(), nullable=False)
    # content_hash was already unique in Phase 3, so we keep it.


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    with op.batch_alter_table('news_articles') as batch_op:
        batch_op.add_column(sa.Column('published_at_old', sa.DateTime(), nullable=True))

    if dialect_name == 'postgresql':
        op.execute(
            """
            UPDATE news_articles
            SET published_at_old = to_timestamp(published_at)
            WHERE published_at IS NOT NULL
            """
        )
    elif dialect_name == 'sqlite':
        op.execute(
            """
            UPDATE news_articles
            SET published_at_old = datetime(published_at, 'unixepoch')
            WHERE published_at IS NOT NULL
            """
        )
    else:
        op.execute(
            """
            UPDATE news_articles
            SET published_at_old = FROM_UNIXTIME(published_at)
            WHERE published_at IS NOT NULL
            """
        )

    with op.batch_alter_table('news_articles') as batch_op:
        batch_op.drop_column('published_at')
        batch_op.alter_column(
            'headline',
            existing_type=sa.Text(),
            existing_nullable=False,
            existing_server_default=sa.text("''"),
            new_column_name='title',
            server_default='',
        )
        batch_op.alter_column(
            'body_snippet',
            existing_type=sa.Text(),
            existing_nullable=True,
            new_column_name='summary',
        )
        batch_op.add_column(sa.Column('embedding_id', sa.String(length=100), nullable=True))
        batch_op.alter_column(
            'published_at_old',
            existing_type=sa.DateTime(),
            existing_nullable=True,
            new_column_name='published_at',
        )
        batch_op.alter_column('url', existing_type=sa.Text(), nullable=True)
