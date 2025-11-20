"""
Better Settings Implementation - Scalable Version
===============================================

This version maintains List[str] interface while properly handling .env parsing.
"""

import os
import json
from typing import Dict, Any, List
try:
    # Pydantic v2
    from pydantic import Field, field_validator, model_validator
    from pydantic_settings import BaseSettings, SettingsConfigDict
    PYDANTIC_V2 = True
except ImportError:
    # Pydantic v1 fallback
    from pydantic import BaseSettings, Field, validator
    PYDANTIC_V2 = False


class Settings(BaseSettings):
    """
    Scalable Settings with proper List[str] handling.
    """
    
    # Blockchain settings
    INFURA_API_KEY: str = Field(default="", description="Infura API key for RPC calls")
    ALCHEMY_API_KEY: str = Field(default="", description="Alchemy API key for RPC calls")
    ANKR_API_KEY: str = Field(default="", description="Ankr API key for RPC calls")
    
    # Telegram settings (required)
    TELEGRAM_BOT_TOKEN: str = Field(..., description="Telegram bot token for notifications")
    TELEGRAM_CHAT_ID: str = Field(..., description="Telegram chat ID for notifications")
    
    # API settings
    COINGECKO_API_KEY: str = Field(default="", description="CoinGecko API key for price data")
    
    # Wallet settings - KEEP AS List[str] for scalability
    WALLET_ADDRESSES: List[str] = Field(default_factory=list, description="List of wallet addresses to monitor")
    
    # Network settings
    DEFAULT_NETWORK: str = Field(default="ethereum_sepolia", description="Default blockchain network")
    
    # Monitoring settings
    CHECK_INTERVAL_MINUTES: int = Field(default=15, description="Monitoring interval in minutes")
    DEFAULT_IL_THRESHOLD: float = Field(default=0.05, description="Default IL alert threshold")
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_TO_FILE: bool = Field(default=True, description="Enable file logging")

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True,
        # Custom env parsing
        env_parse_none_str='',
    )
    
    @model_validator(mode='before')
    @classmethod
    def parse_wallet_addresses(cls, values):
        """Custom parser for WALLET_ADDRESSES that handles .env string format."""
        if isinstance(values, dict) and 'WALLET_ADDRESSES' in values:
            wallet_val = values['WALLET_ADDRESSES']
            
            # Skip if already processed or empty
            if isinstance(wallet_val, list) or not wallet_val:
                return values
                
            if isinstance(wallet_val, str):
                # Clean string
                cleaned = wallet_val.strip().strip('"').strip("'")
                
                if not cleaned:
                    values['WALLET_ADDRESSES'] = []
                elif cleaned.startswith('[') and cleaned.endswith(']'):
                    # JSON array format: ["0x...", "0x..."]
                    try:
                        values['WALLET_ADDRESSES'] = json.loads(cleaned)
                    except json.JSONDecodeError:
                        values['WALLET_ADDRESSES'] = []
                elif ',' in cleaned:
                    # Comma-separated: 0x...,0x...
                    values['WALLET_ADDRESSES'] = [addr.strip() for addr in cleaned.split(',') if addr.strip()]
                else:
                    # Single address: 0x...
                    values['WALLET_ADDRESSES'] = [cleaned]
        
        return values
    
    @field_validator('CHECK_INTERVAL_MINUTES')
    @classmethod
    def validate_interval(cls, v):
        if v < 1:
            raise ValueError('CHECK_INTERVAL_MINUTES must be at least 1')
        return v
    
    @field_validator('DEFAULT_IL_THRESHOLD')
    @classmethod
    def validate_threshold(cls, v):
        if not (0 < v <= 1):
            raise ValueError('DEFAULT_IL_THRESHOLD must be between 0 and 1')
        return v
    
    @field_validator('DEFAULT_NETWORK')
    @classmethod
    def validate_network(cls, v):
        supported = ['ethereum_mainnet', 'ethereum_sepolia', 'polygon', 'arbitrum']
        if v not in supported:
            raise ValueError(f'DEFAULT_NETWORK must be one of: {supported}')
        return v
    
    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f'LOG_LEVEL must be one of: {valid_levels}')
        return v_upper
    
    @field_validator('WALLET_ADDRESSES')
    @classmethod
    def validate_wallet_addresses(cls, v):
        """Validate each wallet address format."""
        if not isinstance(v, list):
            raise ValueError('WALLET_ADDRESSES must be a list')
        
        validated_addresses = []
        for addr in v:
            if not isinstance(addr, str):
                continue
            addr = addr.strip()
            if addr and addr.startswith('0x') and len(addr) == 42:
                validated_addresses.append(addr.lower())
        
        return validated_addresses
    
    @field_validator('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID')
    @classmethod
    def validate_required_fields(cls, v):
        if not v:
            raise ValueError('Required field cannot be empty')
        return v
    
    def get_rpc_url(self, network: str = None) -> str:
        """Get RPC URL for specified network."""
        network = network or self.DEFAULT_NETWORK
        
        # Try Infura first
        if self.INFURA_API_KEY:
            infura_urls = {
                'ethereum_mainnet': f'https://mainnet.infura.io/v3/{self.INFURA_API_KEY}',
                'ethereum_sepolia': f'https://sepolia.infura.io/v3/{self.INFURA_API_KEY}',
                'polygon': f'https://polygon-mainnet.infura.io/v3/{self.INFURA_API_KEY}',
                'arbitrum': f'https://arbitrum-mainnet.infura.io/v3/{self.INFURA_API_KEY}'
            }
            if network in infura_urls:
                return infura_urls[network]
        
        # Try Alchemy
        if self.ALCHEMY_API_KEY:
            alchemy_urls = {
                'ethereum_mainnet': f'https://eth-mainnet.alchemyapi.io/v2/{self.ALCHEMY_API_KEY}',
                'ethereum_sepolia': f'https://eth-sepolia.alchemyapi.io/v2/{self.ALCHEMY_API_KEY}',
                'polygon': f'https://polygon-mainnet.alchemyapi.io/v2/{self.ALCHEMY_API_KEY}',
                'arbitrum': f'https://arb-mainnet.alchemyapi.io/v2/{self.ALCHEMY_API_KEY}'
            }
            if network in alchemy_urls:
                return alchemy_urls[network]
        
        # Fallback to Ankr public endpoints
        ankr_urls = {
            'ethereum_mainnet': 'https://rpc.ankr.com/eth',
            'ethereum_sepolia': 'https://rpc.ankr.com/eth_sepolia',
            'polygon': 'https://rpc.ankr.com/polygon',
            'arbitrum': 'https://rpc.ankr.com/arbitrum'
        }
        
        return ankr_urls.get(network, ankr_urls['ethereum_sepolia'])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (for logging/debugging)."""
        return {
            'default_network': self.DEFAULT_NETWORK,
            'check_interval_minutes': self.CHECK_INTERVAL_MINUTES,
            'default_il_threshold': self.DEFAULT_IL_THRESHOLD,
            'log_level': self.LOG_LEVEL,
            'log_to_file': self.LOG_TO_FILE,
            'wallet_count': len(self.WALLET_ADDRESSES),  # Direct access to list
            'has_infura_key': bool(self.INFURA_API_KEY),
            'has_alchemy_key': bool(self.ALCHEMY_API_KEY),
            'has_telegram_config': bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID),
            'has_coingecko_key': bool(self.COINGECKO_API_KEY)
        }

# Test the improved implementation
if __name__ == "__main__":
    import os
    os.environ['WALLET_ADDRESSES'] = '0x742d35Cc6634C0532925a3b8D41141D8F10C473d'
    os.environ['TELEGRAM_BOT_TOKEN'] = 'test'
    os.environ['TELEGRAM_CHAT_ID'] = 'test'
    
    settings = Settings()
    
    print("✅ Improved Settings Test:")
    print(f"Type of WALLET_ADDRESSES: {type(settings.WALLET_ADDRESSES)}")
    print(f"WALLET_ADDRESSES value: {settings.WALLET_ADDRESSES}")
    print(f"Wallet count: {len(settings.WALLET_ADDRESSES)}")
    print(f"Serializable: {settings.model_dump()}")
