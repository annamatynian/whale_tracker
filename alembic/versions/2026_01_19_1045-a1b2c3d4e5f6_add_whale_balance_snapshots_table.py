"""Add whale_balance_snapshots table for historical balance tracking

Revision ID: a1b2c3d4e5f6
Revises: 66a854bd3a29
Create Date: 2026-01-19 10:45:00.000000

WHY: Avoid expensive archive node queries by storing hourly snapshots
GEMINI RECOMMENDATION: "Snapshot system is industry standard for avoiding archive nodes"
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '66a854bd3a29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create whale_balance_snapshots table.
    
    Stores hourly snapshots of whale balances to enable historical comparisons
    without requiring archive node access.
    """
    op.create_table(
        'whale_balance_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('address', sa.String(length=42), nullable=False),
        sa.Column('balance_wei', sa.String(length=78), nullable=False),  # String for precision
        sa.Column('balance_eth', sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column('block_number', sa.BigInteger(), nullable=False),
        sa.Column('snapshot_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('network', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("network IN ('bitcoin', 'ethereum', 'usdt', 'solana')", name='valid_network_snapshot')
    )
    
    # Indexes for efficient queries
    op.create_index('idx_snapshot_address_time', 'whale_balance_snapshots', ['address', 'snapshot_timestamp'], postgresql_ops={'snapshot_timestamp': 'DESC'})
    op.create_index('idx_snapshot_time', 'whale_balance_snapshots', ['snapshot_timestamp'], postgresql_ops={'snapshot_timestamp': 'DESC'})
    op.create_index('idx_snapshot_network_time', 'whale_balance_snapshots', ['network', 'snapshot_timestamp'], postgresql_ops={'snapshot_timestamp': 'DESC'})
    
    # Unique constraint to prevent duplicate snapshots
    op.create_index('idx_snapshot_unique', 'whale_balance_snapshots', ['address', 'snapshot_timestamp', 'network'], unique=True)


def downgrade() -> None:
    """Remove whale_balance_snapshots table."""
    op.drop_index('idx_snapshot_unique', table_name='whale_balance_snapshots')
    op.drop_index('idx_snapshot_network_time', table_name='whale_balance_snapshots')
    op.drop_index('idx_snapshot_time', table_name='whale_balance_snapshots')
    op.drop_index('idx_snapshot_address_time', table_name='whale_balance_snapshots')
    op.drop_table('whale_balance_snapshots')
