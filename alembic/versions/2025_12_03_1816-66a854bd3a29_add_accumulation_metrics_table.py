"""Add accumulation_metrics table

Revision ID: 66a854bd3a29
Revises: 
Create Date: 2025-12-03 18:16:59.346817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66a854bd3a29'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'accumulation_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('network', sa.String(length=20), nullable=False),
        sa.Column('score', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('addresses_analyzed', sa.Integer(), nullable=False),
        sa.Column('total_balance_change', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('measurement_period_days', sa.Integer(), nullable=True),
        sa.Column('top_accumulators', sa.JSON(), nullable=True),
        sa.Column('top_distributors', sa.JSON(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=False),
        sa.Column('calculation_duration_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('score >= 0 AND score <= 1', name='valid_score'),
        sa.CheckConstraint("network IN ('bitcoin', 'ethereum', 'usdt')", name='valid_network')
    )
    op.create_index('idx_accumulation_network_time', 'accumulation_metrics', ['network', 'calculated_at'])


def downgrade() -> None:
    op.drop_index('idx_accumulation_network_time', table_name='accumulation_metrics')
    op.drop_table('accumulation_metrics')
