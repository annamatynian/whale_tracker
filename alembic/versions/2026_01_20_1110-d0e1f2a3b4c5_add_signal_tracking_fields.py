"""Add num_signals_used and num_signals_excluded fields

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-01-20 11:10:00.000000

WHY: Professional report formatter requires these fields for data quality transparency
GEMINI FIX #4: Track valid vs excluded signals (RPC errors, None values)

FIELDS:
- num_signals_used: Count of valid whale addresses in Gini/score calculation
- num_signals_excluded: Count of addresses excluded due to RPC errors
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0e1f2a3b4c5'
down_revision: Union[str, None] = 'c9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add data quality tracking fields for professional reports.
    
    WHY: Transparent reporting of RPC error impact on signal quality
    """
    
    # num_signals_used: Count of valid signals in calculation
    op.add_column(
        'accumulation_metrics',
        sa.Column(
            'num_signals_used',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Number of valid whale addresses used in Gini calculation (excludes RPC errors)'
        )
    )
    
    # num_signals_excluded: Count of excluded signals
    op.add_column(
        'accumulation_metrics',
        sa.Column(
            'num_signals_excluded',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Number of addresses excluded from Gini due to RPC errors (VULNERABILITY FIX #4)'
        )
    )
    
    # Add check constraints
    op.create_check_constraint(
        'valid_signals_used',
        'accumulation_metrics',
        'num_signals_used >= 0'
    )
    
    op.create_check_constraint(
        'valid_signals_excluded',
        'accumulation_metrics',
        'num_signals_excluded >= 0'
    )


def downgrade() -> None:
    """
    Remove data quality tracking fields.
    """
    
    # Drop constraints first
    op.drop_constraint('valid_signals_excluded', 'accumulation_metrics', type_='check')
    op.drop_constraint('valid_signals_used', 'accumulation_metrics', type_='check')
    
    # Drop columns
    op.drop_column('accumulation_metrics', 'num_signals_excluded')
    op.drop_column('accumulation_metrics', 'num_signals_used')
