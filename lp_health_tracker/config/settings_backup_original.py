"""
Settings and Configuration Management
====================================

This module contains all configuration settings for the LP Health Tracker.

"""

import os
import json
from typing import Dict, Any, List
try:
    # Pydantic v2
    from pydantic import Field, field_validator
    from pydantic_settings import BaseSettings
    PYDANTIC_V2 = True
except ImportError:
    # Pydantic v1 fallback
    from pydantic import BaseSettings, Field, validator
    PYDANTIC_V2 = False


class Settings(BaseSettings):
    """
    Application settings with Pydantic validation.
    Automatically loads from environment variables and .env file.
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
    
    # Wallet settings
    WALLET_ADDRESSES: str = Field(default="", description="Wallet addresses to monitor (comma-separated or JSON array)")
    
    # Network settings
    DEFAULT_NETWORK: str = Field(default="ethereum_sepolia", description="Default blockchain network")
    
    # Monitoring settings
    CHECK_INTERVAL_MINUTES: int = Field(default=15, description="Monitoring interval in minutes")
    DEFAULT_IL_THRESHOLD: float = Field(default=0.05, description="Default IL alert threshold")
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_TO_FILE: bool = Field(default=True, description="Enable file logging")
    
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
    
    @field_validator('WALLET_ADDRESSES', mode='before')
    @classmethod
    def parse_wallet_addresses(cls, v):
        """Handles multiple wallet address formats from environment variables."""
        if not v:
            return ""
        
        if isinstance(v, list):
            return ",".join(v)  # Convert list back to string
            
        if not isinstance(v, str):
            return str(v)

        # Remove extra quotes and whitespace
        v = v.strip().strip('"').strip("'")
        
        return v  # Return as string, will be parsed by get_wallet_list property
    
    @field_validator('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID')
    @classmethod
    def validate_required_fields(cls, v):
        if not v:
            raise ValueError('Required field cannot be empty')
        return v
    
    model_config = {
        'env_file': '.env',
        'env_file_encoding': 'utf-8',
        'case_sensitive': True
    }
    
    @property
    def wallet_addresses_list(self) -> List[str]:
        """Get wallet addresses as a list."""
        if not self.WALLET_ADDRESSES:
            return []
        
        v = self.WALLET_ADDRESSES.strip()
        
        # Handle JSON array format
        if v.startswith('[') and v.endswith(']'):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                pass
        
        # Handle comma-separated format
        if ',' in v:
            return [addr.strip() for addr in v.split(',') if addr.strip()]
        
        # Single address
        return [v] if v else []
    
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
            'wallet_count': len(self.wallet_addresses_list),
            'has_infura_key': bool(self.INFURA_API_KEY),
            'has_alchemy_key': bool(self.ALCHEMY_API_KEY),
            'has_telegram_config': bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID),
            'has_coingecko_key': bool(self.COINGECKO_API_KEY)
        }
# python run.py --test-config
# Default position configuration template
DEFAULT_POSITION_CONFIG = {
    "name": "",
    "pair_address": "",
    "token_a_symbol": "",
    "token_b_symbol": "",
    "token_a_address": "",
    "token_b_address": "",
    "initial_liquidity_a": 0.0,
    "initial_liquidity_b": 0.0,
    "initial_price_a_usd": 0.0,
    "initial_price_b_usd": 0.0,
    "wallet_address": "",
    "network": "ethereum_mainnet",
    "il_alert_threshold": 0.05,
    "protocol": "uniswap_v2",
    "pool_fee": 0.003,
    "active": True,
    "notes": ""
}

# Known contract addresses for different networks
CONTRACT_ADDRESSES = {
    'ethereum_mainnet': {
        'tokens': {
            'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
            'USDC': '0xA0b86a33E6c21C64E0eb4ADa7B0b0094a7f6E44C',
            'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
            'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
            'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
            'UNI': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984'
        },
        'pairs': {
            'WETH_USDC_V2': '0xB4e16d0168e52d35CaCD2b6464f00d6eB9002C6D',
            'WETH_USDT_V2': '0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852',
            'WETH_DAI_V2': '0xA478c2975Ab1Ea89e8196811F51A7B7Ade33eB11',
            'USDC_USDT_V2': '0x3041CbD36888bECc7bbCBc0045E3B1f144466f5f'
        }
    },
    'ethereum_sepolia': {
        'tokens': {
            # Sepolia testnet addresses (these are placeholders)
            'WETH': '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9',
            'USDC': '0x...',  # Need actual Sepolia USDC address
        },
        'pairs': {
            # Sepolia testnet pairs
        }
    }
}

# Risk categories and thresholds
RISK_CATEGORIES = {
    'very_low': {
        'description': 'Stablecoin pairs (e.g., USDC/USDT)',
        'recommended_threshold': 0.005,  # 0.5%
        'max_expected_il': 0.01,         # 1%
        'color': '🟢'
    },
    'low': {
        'description': 'Stablecoin + major token (e.g., ETH/USDC)',
        'recommended_threshold': 0.02,   # 2%
        'max_expected_il': 0.05,         # 5%
        'color': '🟡'
    },
    'medium': {
        'description': 'Major token pairs (e.g., ETH/BTC)',
        'recommended_threshold': 0.05,   # 5%
        'max_expected_il': 0.10,         # 10%
        'color': '🟠'
    },
    'high': {
        'description': 'Volatile token pairs',
        'recommended_threshold': 0.10,   # 10%
        'max_expected_il': 0.25,         # 25%
        'color': '🔴'
    }
}

# Supported protocols
SUPPORTED_PROTOCOLS = {
    'uniswap_v2': {
        'name': 'Uniswap V2',
        'type': 'constant_product',
        'fee': 0.003,
        'description': '50/50 constant product AMM'
    },
    'sushiswap': {
        'name': 'SushiSwap',
        'type': 'constant_product',
        'fee': 0.003,
        'description': 'Uniswap V2 fork'
    }
    # Future: Add Uniswap V3, Curve, etc.
}

# API endpoints and limits
API_LIMITS = {
    'coingecko_free': {
        'requests_per_minute': 50,
        'requests_per_hour': 1000
    },
    'infura_free': {
        'requests_per_day': 100000
    },
    'alchemy_free': {
        'requests_per_day': 300000000
    }
}
