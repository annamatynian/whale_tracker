"""Accumulation Metrics Pydantic Schemas"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List


class AccumulationMetricCreate(BaseModel):
    """Schema for creating accumulation metric."""
    token_symbol: str
    whale_count: int
    total_balance_current_wei: str
    total_balance_historical_wei: str
    total_balance_change_wei: str
    total_balance_current_eth: Decimal
    total_balance_historical_eth: Decimal
    total_balance_change_eth: Decimal
    accumulation_score: Decimal
    accumulators_count: int
    distributors_count: int
    neutral_count: int
    current_block_number: int
    historical_block_number: int
    lookback_hours: int
    
    # ============================================
    # LST CORRECTION FIELDS (Phase 2)
    # ============================================
    
    # LST Balance Tracking
    total_weth_balance_eth: Optional[Decimal] = Field(
        default=None,
        description="Total WETH holdings across all whales (in ETH units)"
    )
    
    total_steth_balance_eth: Optional[Decimal] = Field(
        default=None,
        description="Total stETH holdings converted to ETH equivalent (using current rate)"
    )
    
    lst_adjusted_score: Optional[Decimal] = Field(
        default=None,
        description="Accumulation score with ETH+WETH+stETH aggregation (absolute balance change in ETH)"
    )
    
    lst_migration_count: int = Field(
        default=0,
        description="Number of whales with detected LST migration (ETH→stETH within 1h)"
    )
    
    steth_eth_rate: Optional[Decimal] = Field(
        default=None,
        ge=0.90, le=1.10,  # FIXED: Wider range for crisis scenarios (was 0.95-1.05)
        description="stETH/ETH rate (typically 0.998-1.002, crisis: 0.92-0.95)"
    )
    
    # Smart Tags System
    tags: List[str] = Field(
        default_factory=list,
        description="Diagnostic tags: [Organic Accumulation], [Bullish Divergence], [LST Migration], etc."
    )
    
    # Statistical Quality Metrics
    concentration_gini: Optional[Decimal] = Field(
        default=None,
        ge=0.0, le=1.0,
        description="Gini coefficient of balance distribution (0=perfectly equal, 1=one whale has all)"
    )
    
    num_signals_used: int = Field(
        default=0,
        description="Number of valid whale addresses used in Gini calculation (excludes RPC errors)"
    )
    
    num_signals_excluded: int = Field(
        default=0,
        description="Number of addresses excluded from Gini due to RPC errors (VULNERABILITY FIX #4)"
    )
    
    is_anomaly: bool = Field(
        default=False,
        description="True if score driven by statistical outlier (detected via MAD > 3σ threshold)"
    )
    
    mad_threshold: Optional[Decimal] = Field(
        default=None,
        description="Median Absolute Deviation threshold (in ETH balance units, not %)"
    )
    
    top_anomaly_driver: Optional[str] = Field(
        default=None,
        max_length=42,
        description="Address of whale causing anomaly (if is_anomaly=True)"
    )
    
    # Price Context (for Bullish Divergence detection)
    price_change_48h_pct: Optional[Decimal] = Field(
        default=None,
        description="ETH price change over 48h (%) - for Bullish Divergence tag"
    )


class AccumulationMetric(AccumulationMetricCreate):
    """Schema for accumulation metric with database fields."""
    id: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = ConfigDict(from_attributes=True)
