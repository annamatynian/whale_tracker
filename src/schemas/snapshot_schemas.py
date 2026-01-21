"""
Whale Balance Snapshot Pydantic Schemas

For hourly balance snapshots to avoid archive node dependency.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator, field_serializer
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List


class WhaleBalanceSnapshotCreate(BaseModel):
    """Schema for creating whale balance snapshot."""
    
    address: str = Field(..., min_length=42, max_length=42)
    balance_wei: str = Field(..., description="Balance in Wei (as string for precision)")
    balance_eth: Decimal = Field(..., ge=0, description="Balance in ETH")
    block_number: int = Field(..., gt=0)
    snapshot_timestamp: datetime
    network: str = Field(default="ethereum")
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, v: str) -> str:
        """Validate Ethereum address format."""
        if not v.startswith('0x'):
            raise ValueError("Address must start with '0x'")
        if len(v) != 42:
            raise ValueError("Address must be 42 characters (0x + 40 hex)")
        return v.lower()
    
    @field_validator('network')
    @classmethod
    def validate_network(cls, v: str) -> str:
        """Validate network name."""
        allowed = {'ethereum', 'bitcoin', 'usdt', 'solana'}
        if v not in allowed:
            raise ValueError(f"Network must be one of {allowed}")
        return v
    
    @field_serializer('snapshot_timestamp')
    def serialize_timestamp(self, v: datetime) -> str:
        """Serialize datetime to ISO format."""
        return v.isoformat() if v else None
    
    @field_serializer('balance_eth')
    def serialize_decimal(self, v: Decimal) -> str:
        """Serialize Decimal to string."""
        return str(v) if v else None
    
    model_config = ConfigDict(from_attributes=True)


class WhaleBalanceSnapshot(WhaleBalanceSnapshotCreate):
    """Schema for whale balance snapshot with database fields."""
    
    id: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = ConfigDict(from_attributes=True)


class SnapshotQuery(BaseModel):
    """Schema for querying historical snapshots."""
    
    addresses: Optional[List[str]] = None
    timestamp: datetime
    tolerance_hours: int = Field(default=1, ge=0, le=24)
    network: str = Field(default="ethereum")
    
    @field_validator('addresses')
    @classmethod
    def validate_addresses(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate address list."""
        if v is None:
            return None
        return [addr.lower() for addr in v]


class SnapshotSummary(BaseModel):
    """Summary statistics for a snapshot batch."""
    
    total_snapshots: int
    total_addresses: int
    total_balance_eth: Decimal
    avg_balance_eth: Decimal
    min_balance_eth: Decimal
    max_balance_eth: Decimal
    snapshot_timestamp: datetime
    network: str
