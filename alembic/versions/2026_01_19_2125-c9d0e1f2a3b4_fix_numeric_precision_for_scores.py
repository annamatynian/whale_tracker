"""Fix numeric precision for LST scores and MAD threshold

Revision ID: c9d0e1f2a3b4
Revises: b7c8d9e0f1a2
Create Date: 2026-01-19 21:25:00.000000

WHY: lst_adjusted_score and mad_threshold overflow NUMERIC(10,4)
FIX: Change to NUMERIC(36,18) to support large absolute values (balances in ETH units)

ISSUE: Current precision (10,4) = max ±999,999.9999
ACTUAL: Values like 776,397.558 ETH (balance, not %) and 82 trillion (MAD in %)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Increase precision for fields that store absolute balances (not percentages).
    
    BEFORE: NUMERIC(10, 4) - max ±999,999.9999
    AFTER: NUMERIC(36, 18) - same as balance fields
    """
    
    # lst_adjusted_score: Stores aggregated ETH balance (ETH + WETH + stETH)
    op.alter_column(
        'accumulation_metrics',
        'lst_adjusted_score',
        type_=sa.Numeric(precision=36, scale=18),
        existing_type=sa.Numeric(precision=10, scale=4),
        existing_nullable=True
    )
    
    # mad_threshold: MAD calculated on balance changes (in ETH units)
    op.alter_column(
        'accumulation_metrics',
        'mad_threshold',
        type_=sa.Numeric(precision=36, scale=18),
        existing_type=sa.Numeric(precision=10, scale=4),
        existing_nullable=True
    )


def downgrade() -> None:
    """
    Restore original precision (WARNING: May cause overflow on existing data!).
    """
    
    op.alter_column(
        'accumulation_metrics',
        'lst_adjusted_score',
        type_=sa.Numeric(precision=10, scale=4),
        existing_type=sa.Numeric(precision=36, scale=18),
        existing_nullable=True
    )
    
    op.alter_column(
        'accumulation_metrics',
        'mad_threshold',
        type_=sa.Numeric(precision=10, scale=4),
        existing_type=sa.Numeric(precision=36, scale=18),
        existing_nullable=True
    )
