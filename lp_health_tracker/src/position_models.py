"""
Position Data Models - Pydantic Models for LP Positions
======================================================

This module contains Pydantic models for:
- LP Position configuration and validation
- Token information
- Historical data entries
- Network configuration

Author: Generated for DeFi-RAG Project
"""

import re
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class SupportedNetwork(str, Enum):
    """Supported blockchain networks."""
    ETHEREUM_MAINNET = "ethereum_mainnet"
    ETHEREUM_SEPOLIA = "ethereum_sepolia"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"


class SupportedProtocol(str, Enum):
    """Supported DeFi protocols."""
    UNISWAP_V2 = "uniswap_v2"
    UNISWAP_V3 = "uniswap_v3"
    SUSHISWAP = "sushiswap"
    CURVE = "curve"


class TokenInfo(BaseModel):
    """Model for token information."""
    symbol: str = Field(..., min_length=1, max_length=20, description="Token symbol")
    address: str = Field(..., description="Token contract address")
    decimals: Optional[int] = Field(default=18, ge=0, le=30, description="Token decimals")
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate token symbol format."""
        v = v.upper().strip()
        if not re.match(r'^[A-Z0-9]{1,20}$', v):
            raise ValueError('Token symbol must contain only uppercase letters and numbers')
        return v
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, v: str) -> str:
        """Validate Ethereum address format."""
        if not isinstance(v, str):
            raise ValueError('Address must be a string')
        
        v = v.strip()
        
        if not v.startswith('0x'):
            raise ValueError('Address must start with 0x')
        
        if len(v) != 42:
            raise ValueError('Address must be 42 characters long')
        
        # Check if it contains only hex characters
        if not re.match(r'^0x[a-fA-F0-9]{40}$', v):
            raise ValueError('Address must contain only hex characters')
        
        # Return checksummed address (simple version)
        return v.lower()


class LPPosition(BaseModel):
    """Model for LP position configuration."""
    
    # Basic identification
    name: str = Field(..., min_length=1, max_length=100, description="Position name")
    pair_address: str = Field(..., description="LP pair contract address")
    
    # Token information
    token_a: TokenInfo = Field(..., description="First token in the pair")
    token_b: TokenInfo = Field(..., description="Second token in the pair")
    
    # Initial position data
    initial_liquidity_a: Decimal = Field(..., gt=0, description="Initial amount of token A")
    initial_liquidity_b: Decimal = Field(..., gt=0, description="Initial amount of token B")
    initial_price_a_usd: Decimal = Field(..., gt=0, description="Initial price of token A in USD")
    initial_price_b_usd: Decimal = Field(..., gt=0, description="Initial price of token B in USD")
    
    # Configuration
    wallet_address: str = Field(..., description="Wallet address holding the position")
    network: SupportedNetwork = Field(..., description="Blockchain network")
    protocol: SupportedProtocol = Field(..., description="DeFi protocol")
    pool_fee: Decimal = Field(default=Decimal('0.003'), ge=0, le=1, description="Pool fee percentage")
    
    # Alert settings
    il_alert_threshold: Decimal = Field(
        default=Decimal('0.05'), 
        gt=0, 
        le=1, 
        description="IL alert threshold (0.05 = 5%)"
    )
    
    # Status and metadata
    active: bool = Field(default=True, description="Whether position is actively monitored")
    added_at: datetime = Field(default_factory=datetime.now, description="When position was added")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    notes: Optional[str] = Field(default="", max_length=500, description="Additional notes")
    
    @field_validator('pair_address', 'wallet_address')
    @classmethod
    def validate_ethereum_addresses(cls, v: str) -> str:
        """Validate Ethereum addresses."""
        if not isinstance(v, str):
            raise ValueError('Address must be a string')
        
        v = v.strip()
        
        if not v.startswith('0x'):
            raise ValueError('Address must start with 0x')
        
        if len(v) != 42:
            raise ValueError('Address must be 42 characters long')
        
        if not re.match(r'^0x[a-fA-F0-9]{40}$', v):
            raise ValueError('Address must contain only hex characters')
        
        return v.lower()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate position name."""
        v = v.strip()
        if not v:
            raise ValueError('Position name cannot be empty')
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9\s\-_\.\/]+$', v):
            raise ValueError('Position name contains invalid characters')
        
        return v
    
    @model_validator(mode='after')
    def validate_token_pair(self) -> 'LPPosition':
        """Validate token pair configuration."""
        # Tokens should be different
        if self.token_a.address.lower() == self.token_b.address.lower():
            raise ValueError('Token A and Token B must be different')
        
        # Symbol should be different
        if self.token_a.symbol == self.token_b.symbol:
            raise ValueError('Token A and Token B symbols must be different')
        
        return self
    
    def calculate_initial_value_usd(self) -> Decimal:
        """Calculate initial total value in USD."""
        value_a = self.initial_liquidity_a * self.initial_price_a_usd
        value_b = self.initial_liquidity_b * self.initial_price_b_usd
        return value_a + value_b
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = self.model_dump()
        
        # Convert Decimal to float for JSON compatibility
        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = float(value)
        
        # Handle nested TokenInfo
        if 'token_a' in data and isinstance(data['token_a'], dict):
            for k, v in data['token_a'].items():
                if isinstance(v, Decimal):
                    data['token_a'][k] = float(v)
        
        if 'token_b' in data and isinstance(data['token_b'], dict):
            for k, v in data['token_b'].items():
                if isinstance(v, Decimal):
                    data['token_b'][k] = float(v)
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LPPosition':
        """Create LPPosition from dictionary."""
        # Handle legacy format where tokens are separate fields
        if 'token_a' not in data and 'token_a_symbol' in data:
            data = cls._convert_legacy_format(data)
        
        return cls(**data)
    
    @staticmethod
    def _convert_legacy_format(data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy position format to new format."""
        converted = data.copy()
        
        # Convert token data
        if 'token_a_symbol' in data:
            converted['token_a'] = {
                'symbol': data.pop('token_a_symbol'),
                'address': data.pop('token_a_address', ''),
                'decimals': 18
            }
        
        if 'token_b_symbol' in data:
            converted['token_b'] = {
                'symbol': data.pop('token_b_symbol'),
                'address': data.pop('token_b_address', ''),
                'decimals': 18
            }
        
        # Remove old fields that might conflict
        old_fields = ['token_a_address', 'token_b_address']
        for field in old_fields:
            converted.pop(field, None)
        
        return converted


class HistoricalDataEntry(BaseModel):
    """Model for historical analysis data."""
    timestamp: datetime = Field(default_factory=datetime.now, description="Data timestamp")
    position_name: str = Field(..., description="Position name")
    
    # Analysis results
    current_il_percentage: Optional[Decimal] = Field(None, description="Current IL percentage")
    current_value_usd: Optional[Decimal] = Field(None, description="Current position value in USD")
    hold_value_usd: Optional[Decimal] = Field(None, description="Hold strategy value in USD")
    fees_earned_usd: Optional[Decimal] = Field(None, description="Fees earned in USD")
    
    # Token prices
    token_a_price_usd: Optional[Decimal] = Field(None, description="Token A price in USD")
    token_b_price_usd: Optional[Decimal] = Field(None, description="Token B price in USD")
    
    # Additional metrics
    price_ratio: Optional[Decimal] = Field(None, description="Current price ratio")
    apy_estimate: Optional[Decimal] = Field(None, description="Estimated APY")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = self.model_dump()
        
        # Convert Decimal to float for JSON compatibility
        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = float(value)
            elif isinstance(value, datetime):
                data[key] = value.isoformat()
        
        return data


class PositionAnalysis(BaseModel):
    """Model for position analysis results."""
    position_name: str = Field(..., description="Position name")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    
    # Current status
    is_healthy: bool = Field(..., description="Whether position is healthy")
    il_percentage: Decimal = Field(..., description="Current IL percentage")
    il_usd_amount: Decimal = Field(..., description="IL amount in USD")
    
    # Values
    current_position_value_usd: Decimal = Field(..., description="Current LP position value")
    hold_strategy_value_usd: Decimal = Field(..., description="Hold strategy value")
    total_fees_earned_usd: Decimal = Field(default=Decimal('0'), description="Total fees earned")
    
    # Performance
    total_pnl_usd: Decimal = Field(..., description="Total P&L in USD")
    total_pnl_percentage: Decimal = Field(..., description="Total P&L percentage")
    better_strategy: str = Field(..., description="Better strategy (hold/lp)")
    
    # Market data
    token_a_price_current: Decimal = Field(..., description="Current token A price")
    token_b_price_current: Decimal = Field(..., description="Current token B price")
    current_price_ratio: Decimal = Field(..., description="Current price ratio")
    
    # Risk assessment
    risk_level: str = Field(..., description="Risk level (low/medium/high)")
    recommendation: str = Field(..., description="Action recommendation")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = self.model_dump()
        
        # Convert Decimal to float for JSON compatibility
        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = float(value)
            elif isinstance(value, datetime):
                data[key] = value.isoformat()
        
        return data


class NetworkConfig(BaseModel):
    """Model for network configuration."""
    name: SupportedNetwork = Field(..., description="Network name")
    rpc_url: str = Field(..., description="RPC endpoint URL")
    chain_id: int = Field(..., description="Chain ID")
    currency_symbol: str = Field(..., description="Native currency symbol")
    block_explorer_url: str = Field(..., description="Block explorer URL")
    
    @field_validator('rpc_url', 'block_explorer_url')
    @classmethod
    def validate_urls(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


# Utility functions for working with models
def create_example_position_model() -> LPPosition:
    """Create an example LP position using Pydantic model."""
    return LPPosition(
        name="WETH-USDC Uniswap V2",
        pair_address="0xB4e16d0168e52d35CaCD2b6464f00d1e8d5362C6",
        token_a=TokenInfo(
            symbol="WETH",
            address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        ),
        token_b=TokenInfo(
            symbol="USDC", 
            address="0xA0b86a33E6c21C64E0eb4ADa7B0b0094a7f6E44C",
            decimals=6
        ),
        initial_liquidity_a=Decimal('0.1'),
        initial_liquidity_b=Decimal('200.0'),
        initial_price_a_usd=Decimal('2000.0'),
        initial_price_b_usd=Decimal('1.0'),
        wallet_address="0x742d35Cc6B75D5532c9dFEaee9FB0E1CE3b96b94",
        network=SupportedNetwork.ETHEREUM_MAINNET,
        protocol=SupportedProtocol.UNISWAP_V2,
        il_alert_threshold=Decimal('0.05'),
        notes="Main ETH-USDC position for moderate risk exposure"
    )


def validate_position_dict(position_data: Dict[str, Any]) -> List[str]:
    """
    Validate position dictionary using Pydantic model.
    
    Args:
        position_data: Position data dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    try:
        LPPosition.from_dict(position_data)
        return []
    except Exception as e:
        return [str(e)]
