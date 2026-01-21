"""Recreate accumulation_metrics table with LST correction fields

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-01-19 21:00:00.000000

WHY: Complete schema redesign to support LST correction (WETH + stETH aggregation)
PHASE 2: Adds MAD anomaly detection, Gini index, smart tags, and LST migration tracking
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    DROP old accumulation_metrics table and CREATE new with LST fields.
    
    NEW SCHEMA:
    - Native ETH metrics (backward compatible)
    - LST aggregation (WETH + stETH)
    - MAD anomaly detection
    - Gini coefficient
    - Smart tags system
    - Price context for Bullish Divergence
    """
    
    # DROP old table
    op.drop_index('idx_accumulation_network_time', table_name='accumulation_metrics')
    op.drop_table('accumulation_metrics')
    
    # CREATE new table with complete schema
    op.create_table(
        'accumulation_metrics',
        
        # Primary key
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Basic metadata
        sa.Column('token_symbol', sa.String(length=10), nullable=False),
        sa.Column('whale_count', sa.Integer(), nullable=False),
        
        # Native ETH balance metrics (backward compatibility)
        sa.Column('total_balance_current_wei', sa.String(length=78), nullable=False),  # String for precision
        sa.Column('total_balance_historical_wei', sa.String(length=78), nullable=False),
        sa.Column('total_balance_change_wei', sa.String(length=78), nullable=False),
        sa.Column('total_balance_current_eth', sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column('total_balance_historical_eth', sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column('total_balance_change_eth', sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column('accumulation_score', sa.Numeric(precision=10, scale=4), nullable=False),
        
        # ============================================
        # LST CORRECTION FIELDS (Phase 2)
        # ============================================
        
        # LST Balance Tracking
        sa.Column('total_weth_balance_eth', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('total_steth_balance_eth', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('lst_adjusted_score', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('lst_migration_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('steth_eth_rate', sa.Numeric(precision=10, scale=6), nullable=True),
        
        # Smart Tags System
        sa.Column('tags', postgresql.ARRAY(sa.String(length=50)), nullable=False, server_default='{}'),
        
        # Statistical Quality Metrics
        sa.Column('concentration_gini', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('is_anomaly', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('mad_threshold', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('top_anomaly_driver', sa.String(length=42), nullable=True),
        
        # Price Context (for Bullish Divergence)
        sa.Column('price_change_48h_pct', sa.Numeric(precision=10, scale=4), nullable=True),
        
        # ============================================
        # WHALE DISTRIBUTION
        # ============================================
        sa.Column('accumulators_count', sa.Integer(), nullable=False),
        sa.Column('distributors_count', sa.Integer(), nullable=False),
        sa.Column('neutral_count', sa.Integer(), nullable=False),
        
        # ============================================
        # METADATA
        # ============================================
        sa.Column('current_block_number', sa.BigInteger(), nullable=False),
        sa.Column('historical_block_number', sa.BigInteger(), nullable=False),
        sa.Column('lookback_hours', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('whale_count >= 0', name='valid_whale_count'),
        sa.CheckConstraint('accumulators_count >= 0', name='valid_accumulators'),
        sa.CheckConstraint('distributors_count >= 0', name='valid_distributors'),
        sa.CheckConstraint('neutral_count >= 0', name='valid_neutral'),
        sa.CheckConstraint('lookback_hours > 0', name='valid_lookback'),
        sa.CheckConstraint('steth_eth_rate IS NULL OR (steth_eth_rate >= 0.90 AND steth_eth_rate <= 1.10)', name='valid_steth_rate'),
        sa.CheckConstraint('concentration_gini IS NULL OR (concentration_gini >= 0.0 AND concentration_gini <= 1.0)', name='valid_gini')
    )
    
    # Indexes for efficient queries
    op.create_index('idx_accumulation_token_time', 'accumulation_metrics', ['token_symbol', 'created_at'], postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_accumulation_created_at', 'accumulation_metrics', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_accumulation_anomaly', 'accumulation_metrics', ['is_anomaly', 'created_at'], postgresql_where=sa.text('is_anomaly = true'))
    
    # GIN index for tags array (fast CONTAINS queries)
    op.create_index('idx_accumulation_tags', 'accumulation_metrics', ['tags'], postgresql_using='gin')


def downgrade() -> None:
    """
    Restore old accumulation_metrics table structure.
    
    WARNING: This will lose LST correction data!
    """
    # DROP new table
    op.drop_index('idx_accumulation_tags', table_name='accumulation_metrics')
    op.drop_index('idx_accumulation_anomaly', table_name='accumulation_metrics')
    op.drop_index('idx_accumulation_created_at', table_name='accumulation_metrics')
    op.drop_index('idx_accumulation_token_time', table_name='accumulation_metrics')
    op.drop_table('accumulation_metrics')
    
    # Recreate old table (from revision 66a854bd3a29)
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
