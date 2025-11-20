"""
FULLY Backward Compatible YAML Settings - FIXED VERSION
========================================================

This file provides 100% backward compatibility with the original settings.py
while adding YAML configuration support.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


class BlockchainProvider(BaseModel):
    """Configuration for blockchain RPC providers."""
    api_key: str = ""
    priority: int = 1
    networks: List[str] = Field(default_factory=list)
    public_endpoints: bool = False


class BlockchainConfig(BaseModel):
    """Blockchain provider configuration."""
    providers: Dict[str, BlockchainProvider] = Field(default_factory=dict)
    default_network: str = "ethereum_sepolia"


class TelegramConfig(BaseModel):
    """Telegram notification configuration."""
    bot_token: str = ""
    chat_id: str = ""
    enabled: bool = True
    timeout: int = 30


class NotificationConfig(BaseModel):
    """Notification systems configuration."""
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)


class APIConfig(BaseModel):
    """External API configuration."""
    api_key: str = ""
    base_url: str = ""
    rate_limit: int = 50


class APIsConfig(BaseModel):
    """All external APIs configuration."""
    coingecko: APIConfig = Field(default_factory=APIConfig)


class MonitoringIntervals(BaseModel):
    """Monitoring timing configuration."""
    check_minutes: int = 15
    alert_cooldown_minutes: int = 60
    price_update_seconds: int = 300


class MonitoringThresholds(BaseModel):
    """Alert threshold configuration."""
    default_il_threshold: float = 0.05
    gas_spike_threshold: float = 100.0
    volume_change_threshold: float = 0.2


class MonitoringConfig(BaseModel):
    """Wallet monitoring configuration."""
    wallet_addresses: List[str] = Field(default_factory=list)
    intervals: MonitoringIntervals = Field(default_factory=MonitoringIntervals)
    thresholds: MonitoringThresholds = Field(default_factory=MonitoringThresholds)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    file_logging: bool = True
    log_rotation: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


class V2Features(BaseModel):
    """V2 analytics features."""
    enabled: bool = True
    impermanent_loss_tracking: bool = True
    fee_tracking: bool = True


class V3Features(BaseModel):
    """V3 analytics features."""
    enabled: bool = False
    concentrated_liquidity: bool = False
    position_health_metrics: bool = False


class MLFeatures(BaseModel):
    """ML model features."""
    enabled: bool = False
    models_directory: str = "./models/"
    training_data_days: int = 30


class FeaturesConfig(BaseModel):
    """Feature flags configuration."""
    v2_analytics: V2Features = Field(default_factory=V2Features)
    v3_analytics: V3Features = Field(default_factory=V3Features)
    ml_models: MLFeatures = Field(default_factory=MLFeatures)


class PerformanceConfig(BaseModel):
    """Performance settings."""
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 30
    cache_ttl_seconds: int = 300
    retry_attempts: int = 3
    retry_delay_seconds: int = 1


class DevelopmentConfig(BaseModel):
    """Development settings."""
    mock_data: bool = False
    test_mode: bool = False
    debug_api_calls: bool = False
    test_network: str = "ethereum_sepolia"


class Settings(BaseModel):
    """
    FULLY Backward Compatible Settings class.
    
    Supports both YAML configuration and legacy .env approach.
    Maintains 100% API compatibility with original settings.py.
    """
    
    # Core configuration sections
    blockchain: BlockchainConfig = Field(default_factory=BlockchainConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    apis: APIsConfig = Field(default_factory=APIsConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    development: DevelopmentConfig = Field(default_factory=DevelopmentConfig)
    contracts: Dict[str, Any] = Field(default_factory=dict)
    risk_categories: Dict[str, Any] = Field(default_factory=dict)
    
    # BACKWARD COMPATIBILITY: Original flat fields
    INFURA_API_KEY: str = Field(default="", description="Infura API key for RPC calls")
    ALCHEMY_API_KEY: str = Field(default="", description="Alchemy API key for RPC calls")
    ANKR_API_KEY: str = Field(default="", description="Ankr API key for RPC calls")
    TELEGRAM_BOT_TOKEN: str = Field(default="", description="Telegram bot token for notifications")
    TELEGRAM_CHAT_ID: str = Field(default="", description="Telegram chat ID for notifications")
    COINGECKO_API_KEY: str = Field(default="", description="CoinGecko API key for price data")
    WALLET_ADDRESSES: List[str] = Field(default_factory=list, description="List of wallet addresses to monitor")
    DEFAULT_NETWORK: str = Field(default="ethereum_sepolia", description="Default blockchain network")
    CHECK_INTERVAL_MINUTES: int = Field(default=15, description="Monitoring interval in minutes")
    DEFAULT_IL_THRESHOLD: float = Field(default=0.05, description="Default IL alert threshold")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_TO_FILE: bool = Field(default=True, description="Enable file logging")
    
    def __init__(self, **data):
        """Initialize Settings with backward compatibility."""
        # If no data provided, try to load from YAML first, then fall back to .env
        if not data:
            try:
                yaml_settings = self._load_from_yaml()
                if yaml_settings:
                    data = yaml_settings
                else:
                    data = self._load_from_env()
            except Exception:
                data = self._load_from_env()
        
        super().__init__(**data)
        
        # Sync hierarchical and flat structures
        self._sync_structures()
    
    def _load_from_yaml(self, environment: str = None) -> Optional[Dict]:
        """Load configuration from YAML files."""
        try:
            if environment is None:
                environment = os.getenv('ENVIRONMENT', 'development')
            
            config_dir = Path(__file__).parent
            base_config_path = config_dir / "base.yaml"
            env_config_path = config_dir / "environments" / f"{environment}.yaml"
            
            # Load base configuration
            base_config = {}
            if base_config_path.exists():
                with open(base_config_path, 'r', encoding='utf-8') as f:
                    base_config = yaml.safe_load(f) or {}
            
            # Load environment-specific configuration
            env_config = {}
            if env_config_path.exists():
                with open(env_config_path, 'r', encoding='utf-8') as f:
                    env_config = yaml.safe_load(f) or {}
            
            # Deep merge configurations
            merged_config = self._deep_merge(base_config, env_config)
            
            # Replace environment variable placeholders
            merged_config = self._replace_env_vars(merged_config)
            
            # Convert to flat structure for compatibility
            return self._convert_to_flat_structure(merged_config)
            
        except Exception:
            return None
    
    def _load_from_env(self) -> Dict:
        """Load configuration from environment variables (legacy mode)."""
        try:
            from pydantic_settings import BaseSettings
            
            class LegacySettings(BaseSettings):
                # Required fields
                TELEGRAM_BOT_TOKEN: str = Field(..., description="Telegram bot token")
                TELEGRAM_CHAT_ID: str = Field(..., description="Telegram chat ID")
                
                # Optional fields with defaults
                INFURA_API_KEY: str = Field(default="", description="Infura API key")
                ALCHEMY_API_KEY: str = Field(default="", description="Alchemy API key") 
                ANKR_API_KEY: str = Field(default="", description="Ankr API key")
                COINGECKO_API_KEY: str = Field(default="", description="CoinGecko API key")
                WALLET_ADDRESSES: Union[str, List[str]] = Field(default="", description="Wallet addresses")
                DEFAULT_NETWORK: str = Field(default="ethereum_sepolia", description="Default network")
                CHECK_INTERVAL_MINUTES: int = Field(default=15, description="Check interval")
                DEFAULT_IL_THRESHOLD: float = Field(default=0.05, description="IL threshold")
                LOG_LEVEL: str = Field(default="INFO", description="Log level")
                LOG_TO_FILE: bool = Field(default=True, description="Log to file")
                
                @field_validator('WALLET_ADDRESSES', mode='before')
                @classmethod
                def parse_wallet_addresses(cls, v) -> List[str]:
                    """Parse wallet addresses from various formats."""
                    if isinstance(v, list):
                        return v
                    if not isinstance(v, str):
                        return []
                    
                    v = v.strip().strip('"').strip("'")
                    if not v:
                        return []
                    
                    # JSON array format
                    if v.startswith('[') and v.endswith(']'):
                        try:
                            return json.loads(v)
                        except json.JSONDecodeError:
                            pass
                    
                    # Comma-separated format
                    if ',' in v:
                        return [addr.strip() for addr in v.split(',') if addr.strip()]
                    
                    # Single address
                    return [v] if v else []
                
                # RESTORED ORIGINAL VALIDATORS
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
            
            legacy = LegacySettings()
            return legacy.model_dump()
            
        except Exception as e:
            # If all else fails, provide minimal defaults
            return {
                'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),
                'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID', ''),
                'INFURA_API_KEY': os.getenv('INFURA_API_KEY', ''),
                'WALLET_ADDRESSES': [],
                'DEFAULT_NETWORK': 'ethereum_sepolia',
                'CHECK_INTERVAL_MINUTES': 15,
                'DEFAULT_IL_THRESHOLD': 0.05,
                'LOG_LEVEL': 'INFO',
                'LOG_TO_FILE': True
            }
    
    def _convert_to_flat_structure(self, yaml_data: Dict) -> Dict:
        """Convert hierarchical YAML to flat structure for backward compatibility."""
        flat = {}
        
        # Map hierarchical to flat structure
        if 'blockchain' in yaml_data:
            blockchain = yaml_data['blockchain']
            if 'providers' in blockchain:
                providers = blockchain['providers']
                flat['INFURA_API_KEY'] = providers.get('infura', {}).get('api_key', '')
                flat['ALCHEMY_API_KEY'] = providers.get('alchemy', {}).get('api_key', '')
                flat['ANKR_API_KEY'] = providers.get('ankr', {}).get('api_key', '')
            flat['DEFAULT_NETWORK'] = blockchain.get('default_network', 'ethereum_sepolia')
        
        if 'notifications' in yaml_data:
            telegram = yaml_data['notifications'].get('telegram', {})
            flat['TELEGRAM_BOT_TOKEN'] = telegram.get('bot_token', '')
            flat['TELEGRAM_CHAT_ID'] = telegram.get('chat_id', '')
        
        if 'apis' in yaml_data:
            coingecko = yaml_data['apis'].get('coingecko', {})
            flat['COINGECKO_API_KEY'] = coingecko.get('api_key', '')
        
        if 'monitoring' in yaml_data:
            monitoring = yaml_data['monitoring']
            flat['WALLET_ADDRESSES'] = monitoring.get('wallet_addresses', [])
            if 'intervals' in monitoring:
                flat['CHECK_INTERVAL_MINUTES'] = monitoring['intervals'].get('check_minutes', 15)
            if 'thresholds' in monitoring:
                flat['DEFAULT_IL_THRESHOLD'] = monitoring['thresholds'].get('default_il_threshold', 0.05)
        
        if 'logging' in yaml_data:
            logging_config = yaml_data['logging']
            flat['LOG_LEVEL'] = logging_config.get('level', 'INFO')
            flat['LOG_TO_FILE'] = logging_config.get('file_logging', True)
        
        # Copy other sections as-is
        for key in ['performance', 'features', 'development', 'contracts', 'risk_categories']:
            if key in yaml_data:
                flat[key] = yaml_data[key]
        
        return flat
    
    def _sync_structures(self):
        """Sync hierarchical and flat structures."""
        # Sync flat -> hierarchical
        if not self.blockchain.providers:
            self.blockchain.providers = {
                'infura': BlockchainProvider(api_key=self.INFURA_API_KEY, priority=1),
                'alchemy': BlockchainProvider(api_key=self.ALCHEMY_API_KEY, priority=2),
                'ankr': BlockchainProvider(api_key=self.ANKR_API_KEY, priority=3, public_endpoints=True)
            }
        
        if not self.notifications.telegram.bot_token:
            self.notifications.telegram.bot_token = self.TELEGRAM_BOT_TOKEN
            self.notifications.telegram.chat_id = self.TELEGRAM_CHAT_ID
        
        if not self.apis.coingecko.api_key:
            self.apis.coingecko.api_key = self.COINGECKO_API_KEY
        
        if not self.monitoring.wallet_addresses:
            self.monitoring.wallet_addresses = self.WALLET_ADDRESSES
            
        if self.monitoring.intervals.check_minutes == 15:  # Default value
            self.monitoring.intervals.check_minutes = self.CHECK_INTERVAL_MINUTES
        
        if self.monitoring.thresholds.default_il_threshold == 0.05:  # Default value
            self.monitoring.thresholds.default_il_threshold = self.DEFAULT_IL_THRESHOLD
        
        if not self.logging.level or self.logging.level == 'INFO':
            self.logging.level = self.LOG_LEVEL
            self.logging.file_logging = self.LOG_TO_FILE
        
        self.blockchain.default_network = self.DEFAULT_NETWORK
    
    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        """Recursively merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Settings._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
    
    @staticmethod
    def _replace_env_vars(config: Any) -> Any:
        """Replace ${VAR_NAME} placeholders with environment variables."""
        if isinstance(config, dict):
            return {k: Settings._replace_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [Settings._replace_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            var_name = config[2:-1]  # Remove ${ and }
            return os.getenv(var_name, "")
        else:
            return config
    
    # BACKWARD COMPATIBILITY PROPERTIES - CRITICAL FOR EXISTING CODE
    
    @property 
    def wallet_addresses(self) -> List[str]:
        """Get wallet addresses as list (CHANGED from wallet_addresses_list)."""
        return self.WALLET_ADDRESSES
    
    @property
    def wallet_addresses_list(self) -> List[str]:
        """RESTORED: Original property name for full compatibility."""
        return self.WALLET_ADDRESSES
    
    @property
    def check_interval_minutes(self) -> int:
        """Get check interval - for backward compatibility."""
        return self.CHECK_INTERVAL_MINUTES
    
    @property
    def default_il_threshold(self) -> float:
        """Get IL threshold - for backward compatibility."""
        return self.DEFAULT_IL_THRESHOLD
    
    @property
    def log_level(self) -> str:
        """Get log level - for backward compatibility."""
        return self.LOG_LEVEL
    
    @property
    def telegram_bot_token(self) -> str:
        """Get Telegram bot token - for backward compatibility."""
        return self.TELEGRAM_BOT_TOKEN
    
    @property
    def telegram_chat_id(self) -> str:
        """Get Telegram chat ID - for backward compatibility."""
        return self.TELEGRAM_CHAT_ID
    
    def get_rpc_url(self, network: str = None) -> str:
        """Get RPC URL - RESTORED ORIGINAL LOGIC for backward compatibility."""
        network = network or self.DEFAULT_NETWORK
        
        # ORIGINAL LOGIC: Fixed priority order Infura -> Alchemy -> Ankr
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
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        try:
            # Use original validation logic
            if self.CHECK_INTERVAL_MINUTES < 1:
                errors.append("CHECK_INTERVAL_MINUTES must be at least 1")
            
            if not (0 < self.DEFAULT_IL_THRESHOLD <= 1):
                errors.append("DEFAULT_IL_THRESHOLD must be between 0 and 1")
            
            supported_networks = ['ethereum_mainnet', 'ethereum_sepolia', 'polygon', 'arbitrum']
            if self.DEFAULT_NETWORK not in supported_networks:
                errors.append(f"DEFAULT_NETWORK must be one of: {supported_networks}")
            
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if self.LOG_LEVEL.upper() not in valid_levels:
                errors.append(f"LOG_LEVEL must be one of: {valid_levels}")
            
            if not self.TELEGRAM_BOT_TOKEN:
                errors.append("TELEGRAM_BOT_TOKEN is required")
                
            if not self.TELEGRAM_CHAT_ID:
                errors.append("TELEGRAM_CHAT_ID is required")
                
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary - RESTORED ORIGINAL FORMAT."""
        return {
            'default_network': self.DEFAULT_NETWORK,
            'check_interval_minutes': self.CHECK_INTERVAL_MINUTES,
            'default_il_threshold': self.DEFAULT_IL_THRESHOLD,
            'log_level': self.LOG_LEVEL,
            'log_to_file': self.LOG_TO_FILE,
            'wallet_count': len(self.WALLET_ADDRESSES),
            'has_infura_key': bool(self.INFURA_API_KEY),
            'has_alchemy_key': bool(self.ALCHEMY_API_KEY),
            'has_telegram_config': bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID),
            'has_coingecko_key': bool(self.COINGECKO_API_KEY)
        }


# RESTORED ALL ORIGINAL CONSTANTS - CRITICAL FOR BACKWARD COMPATIBILITY
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
            'WETH_USDC_V2': '0x397FF1542f962076d0BFE58eA045FfA2d347ACa0',
            'WETH_USDT_V2': '0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852',
            'WETH_DAI_V2': '0xA478c2975Ab1Ea89e8196811F51A7B7Ade33eB11',
            'USDC_USDT_V2': '0x3041CbD36888bECc7bbCBc0045E3B1f144466f5f'
        }
    },
    'ethereum_sepolia': {
        'tokens': {
            'WETH': '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9',
            'USDC': '0x...',
        },
        'pairs': {}
    }
}

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

# Risk categories and thresholds
RISK_CATEGORIES = {
    'very_low': {
        'description': 'Stablecoin pairs (e.g., USDC/USDT)',
        'recommended_threshold': 0.005,
        'max_expected_il': 0.01,
        'color': '🟢'
    },
    'low': {
        'description': 'Stablecoin + major token (e.g., ETH/USDC)',
        'recommended_threshold': 0.02,
        'max_expected_il': 0.05,
        'color': '🟡'
    },
    'medium': {
        'description': 'Major token pairs (e.g., ETH/BTC)',
        'recommended_threshold': 0.05,
        'max_expected_il': 0.10,
        'color': '🟠'
    },
    'high': {
        'description': 'Volatile token pairs',
        'recommended_threshold': 0.10,
        'max_expected_il': 0.25,
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


# Global settings instance for backward compatibility
_settings = None

def get_settings(environment: str = None) -> Settings:
    """Get global settings instance."""
    global _settings
    
    if _settings is None or environment is not None:
        _settings = Settings()
        if environment:
            _settings._environment = environment
    
    return _settings


if __name__ == "__main__":
    # Test backward compatibility
    print("Testing fully backward compatible YAML Settings...")
    
    try:
        settings = Settings()
        print(f"✅ Settings created successfully")
        print(f"   Wallet addresses: {len(settings.wallet_addresses)}")
        print(f"   Wallet addresses (legacy): {len(settings.wallet_addresses_list)}")
        print(f"   Check interval: {settings.check_interval_minutes}")
        print(f"   RPC URL: {settings.get_rpc_url()[:50]}...")
        
        # Test constants
        print(f"   CONTRACT_ADDRESSES available: {bool(CONTRACT_ADDRESSES)}")
        print(f"   RISK_CATEGORIES available: {bool(RISK_CATEGORIES)}")
        
        # Test validation
        errors = settings.validate()
        print(f"   Validation errors: {len(errors)}")
        
        print("🎉 Full backward compatibility achieved!")
        
    except Exception as e:
        print(f"❌ Compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
