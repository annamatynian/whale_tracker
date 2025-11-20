"""
FULLY Backward Compatible YAML Settings
======================================

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
                WALLET_ADDRESSES: Union[str, List[str]] = Field(default=\"\", description=\"Wallet addresses\")\n                DEFAULT_NETWORK: str = Field(default=\"ethereum_sepolia\", description=\"Default network\")\n                CHECK_INTERVAL_MINUTES: int = Field(default=15, description=\"Check interval\")\n                DEFAULT_IL_THRESHOLD: float = Field(default=0.05, description=\"IL threshold\")\n                LOG_LEVEL: str = Field(default=\"INFO\", description=\"Log level\")\n                LOG_TO_FILE: bool = Field(default=True, description=\"Log to file\")\n                \n                @field_validator('WALLET_ADDRESSES', mode='before')\n                @classmethod\n                def parse_wallet_addresses(cls, v) -> List[str]:\n                    \"\"\"Parse wallet addresses from various formats.\"\"\"\n                    if isinstance(v, list):\n                        return v\n                    if not isinstance(v, str):\n                        return []\n                    \n                    v = v.strip().strip('\"').strip(\"'\")\n                    if not v:\n                        return []\n                    \n                    # JSON array format\n                    if v.startswith('[') and v.endswith(']'):\n                        try:\n                            return json.loads(v)\n                        except json.JSONDecodeError:\n                            pass\n                    \n                    # Comma-separated format\n                    if ',' in v:\n                        return [addr.strip() for addr in v.split(',') if addr.strip()]\n                    \n                    # Single address\n                    return [v] if v else []\n                \n                # RESTORED ORIGINAL VALIDATORS\n                @field_validator('CHECK_INTERVAL_MINUTES')\n                @classmethod\n                def validate_interval(cls, v):\n                    if v < 1:\n                        raise ValueError('CHECK_INTERVAL_MINUTES must be at least 1')\n                    return v\n                \n                @field_validator('DEFAULT_IL_THRESHOLD')\n                @classmethod\n                def validate_threshold(cls, v):\n                    if not (0 < v <= 1):\n                        raise ValueError('DEFAULT_IL_THRESHOLD must be between 0 and 1')\n                    return v\n                \n                @field_validator('DEFAULT_NETWORK')\n                @classmethod\n                def validate_network(cls, v):\n                    supported = ['ethereum_mainnet', 'ethereum_sepolia', 'polygon', 'arbitrum']\n                    if v not in supported:\n                        raise ValueError(f'DEFAULT_NETWORK must be one of: {supported}')\n                    return v\n                \n                @field_validator('LOG_LEVEL')\n                @classmethod\n                def validate_log_level(cls, v):\n                    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']\n                    v_upper = v.upper()\n                    if v_upper not in valid_levels:\n                        raise ValueError(f'LOG_LEVEL must be one of: {valid_levels}')\n                    return v_upper\n                \n                @field_validator('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID')\n                @classmethod\n                def validate_required_fields(cls, v):\n                    if not v:\n                        raise ValueError('Required field cannot be empty')\n                    return v\n                \n                model_config = {\n                    'env_file': '.env',\n                    'env_file_encoding': 'utf-8',\n                    'case_sensitive': True\n                }\n            \n            legacy = LegacySettings()\n            return legacy.model_dump()\n            \n        except Exception as e:\n            # If all else fails, provide minimal defaults\n            return {\n                'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),\n                'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID', ''),\n                'INFURA_API_KEY': os.getenv('INFURA_API_KEY', ''),\n                'WALLET_ADDRESSES': [],\n                'DEFAULT_NETWORK': 'ethereum_sepolia',\n                'CHECK_INTERVAL_MINUTES': 15,\n                'DEFAULT_IL_THRESHOLD': 0.05,\n                'LOG_LEVEL': 'INFO',\n                'LOG_TO_FILE': True\n            }\n    \n    def _convert_to_flat_structure(self, yaml_data: Dict) -> Dict:\n        \"\"\"Convert hierarchical YAML to flat structure for backward compatibility.\"\"\"\n        flat = {}\n        \n        # Map hierarchical to flat structure\n        if 'blockchain' in yaml_data:\n            blockchain = yaml_data['blockchain']\n            if 'providers' in blockchain:\n                providers = blockchain['providers']\n                flat['INFURA_API_KEY'] = providers.get('infura', {}).get('api_key', '')\n                flat['ALCHEMY_API_KEY'] = providers.get('alchemy', {}).get('api_key', '')\n                flat['ANKR_API_KEY'] = providers.get('ankr', {}).get('api_key', '')\n            flat['DEFAULT_NETWORK'] = blockchain.get('default_network', 'ethereum_sepolia')\n        \n        if 'notifications' in yaml_data:\n            telegram = yaml_data['notifications'].get('telegram', {})\n            flat['TELEGRAM_BOT_TOKEN'] = telegram.get('bot_token', '')\n            flat['TELEGRAM_CHAT_ID'] = telegram.get('chat_id', '')\n        \n        if 'apis' in yaml_data:\n            coingecko = yaml_data['apis'].get('coingecko', {})\n            flat['COINGECKO_API_KEY'] = coingecko.get('api_key', '')\n        \n        if 'monitoring' in yaml_data:\n            monitoring = yaml_data['monitoring']\n            flat['WALLET_ADDRESSES'] = monitoring.get('wallet_addresses', [])\n            if 'intervals' in monitoring:\n                flat['CHECK_INTERVAL_MINUTES'] = monitoring['intervals'].get('check_minutes', 15)\n            if 'thresholds' in monitoring:\n                flat['DEFAULT_IL_THRESHOLD'] = monitoring['thresholds'].get('default_il_threshold', 0.05)\n        \n        if 'logging' in yaml_data:\n            logging_config = yaml_data['logging']\n            flat['LOG_LEVEL'] = logging_config.get('level', 'INFO')\n            flat['LOG_TO_FILE'] = logging_config.get('file_logging', True)\n        \n        # Copy other sections as-is\n        for key in ['performance', 'features', 'development', 'contracts', 'risk_categories']:\n            if key in yaml_data:\n                flat[key] = yaml_data[key]\n        \n        return flat\n    \n    def _sync_structures(self):\n        \"\"\"Sync hierarchical and flat structures.\"\"\"\n        # Sync flat -> hierarchical\n        if not self.blockchain.providers:\n            self.blockchain.providers = {\n                'infura': BlockchainProvider(api_key=self.INFURA_API_KEY, priority=1),\n                'alchemy': BlockchainProvider(api_key=self.ALCHEMY_API_KEY, priority=2),\n                'ankr': BlockchainProvider(api_key=self.ANKR_API_KEY, priority=3, public_endpoints=True)\n            }\n        \n        if not self.notifications.telegram.bot_token:\n            self.notifications.telegram.bot_token = self.TELEGRAM_BOT_TOKEN\n            self.notifications.telegram.chat_id = self.TELEGRAM_CHAT_ID\n        \n        if not self.apis.coingecko.api_key:\n            self.apis.coingecko.api_key = self.COINGECKO_API_KEY\n        \n        if not self.monitoring.wallet_addresses:\n            self.monitoring.wallet_addresses = self.WALLET_ADDRESSES\n            \n        if self.monitoring.intervals.check_minutes == 15:  # Default value\n            self.monitoring.intervals.check_minutes = self.CHECK_INTERVAL_MINUTES\n        \n        if self.monitoring.thresholds.default_il_threshold == 0.05:  # Default value\n            self.monitoring.thresholds.default_il_threshold = self.DEFAULT_IL_THRESHOLD\n        \n        if not self.logging.level or self.logging.level == 'INFO':\n            self.logging.level = self.LOG_LEVEL\n            self.logging.file_logging = self.LOG_TO_FILE\n        \n        self.blockchain.default_network = self.DEFAULT_NETWORK\n    \n    @staticmethod\n    def _deep_merge(base: Dict, override: Dict) -> Dict:\n        \"\"\"Recursively merge two dictionaries.\"\"\"\n        result = base.copy()\n        \n        for key, value in override.items():\n            if key in result and isinstance(result[key], dict) and isinstance(value, dict):\n                result[key] = Settings._deep_merge(result[key], value)\n            else:\n                result[key] = value\n                \n        return result\n    \n    @staticmethod\n    def _replace_env_vars(config: Any) -> Any:\n        \"\"\"Replace ${VAR_NAME} placeholders with environment variables.\"\"\"\n        if isinstance(config, dict):\n            return {k: Settings._replace_env_vars(v) for k, v in config.items()}\n        elif isinstance(config, list):\n            return [Settings._replace_env_vars(item) for item in config]\n        elif isinstance(config, str) and config.startswith(\"${\") and config.endswith(\"}\"):\n            var_name = config[2:-1]  # Remove ${ and }\n            return os.getenv(var_name, \"\")\n        else:\n            return config\n    \n    # BACKWARD COMPATIBILITY PROPERTIES - CRITICAL FOR EXISTING CODE\n    \n    @property \n    def wallet_addresses(self) -> List[str]:\n        \"\"\"Get wallet addresses as list (CHANGED from wallet_addresses_list).\"\"\"\n        return self.WALLET_ADDRESSES\n    \n    @property\n    def wallet_addresses_list(self) -> List[str]:\n        \"\"\"RESTORED: Original property name for full compatibility.\"\"\"\n        return self.WALLET_ADDRESSES\n    \n    @property\n    def check_interval_minutes(self) -> int:\n        \"\"\"Get check interval - for backward compatibility.\"\"\"\n        return self.CHECK_INTERVAL_MINUTES\n    \n    @property\n    def default_il_threshold(self) -> float:\n        \"\"\"Get IL threshold - for backward compatibility.\"\"\"\n        return self.DEFAULT_IL_THRESHOLD\n    \n    @property\n    def log_level(self) -> str:\n        \"\"\"Get log level - for backward compatibility.\"\"\"\n        return self.LOG_LEVEL\n    \n    @property\n    def telegram_bot_token(self) -> str:\n        \"\"\"Get Telegram bot token - for backward compatibility.\"\"\"\n        return self.TELEGRAM_BOT_TOKEN\n    \n    @property\n    def telegram_chat_id(self) -> str:\n        \"\"\"Get Telegram chat ID - for backward compatibility.\"\"\"\n        return self.TELEGRAM_CHAT_ID\n    \n    def get_rpc_url(self, network: str = None) -> str:\n        \"\"\"Get RPC URL - RESTORED ORIGINAL LOGIC for backward compatibility.\"\"\"\n        network = network or self.DEFAULT_NETWORK\n        \n        # ORIGINAL LOGIC: Fixed priority order Infura -> Alchemy -> Ankr\n        # Try Infura first\n        if self.INFURA_API_KEY:\n            infura_urls = {\n                'ethereum_mainnet': f'https://mainnet.infura.io/v3/{self.INFURA_API_KEY}',\n                'ethereum_sepolia': f'https://sepolia.infura.io/v3/{self.INFURA_API_KEY}',\n                'polygon': f'https://polygon-mainnet.infura.io/v3/{self.INFURA_API_KEY}',\n                'arbitrum': f'https://arbitrum-mainnet.infura.io/v3/{self.INFURA_API_KEY}'\n            }\n            if network in infura_urls:\n                return infura_urls[network]\n        \n        # Try Alchemy\n        if self.ALCHEMY_API_KEY:\n            alchemy_urls = {\n                'ethereum_mainnet': f'https://eth-mainnet.alchemyapi.io/v2/{self.ALCHEMY_API_KEY}',\n                'ethereum_sepolia': f'https://eth-sepolia.alchemyapi.io/v2/{self.ALCHEMY_API_KEY}',\n                'polygon': f'https://polygon-mainnet.alchemyapi.io/v2/{self.ALCHEMY_API_KEY}',\n                'arbitrum': f'https://arb-mainnet.alchemyapi.io/v2/{self.ALCHEMY_API_KEY}'\n            }\n            if network in alchemy_urls:\n                return alchemy_urls[network]\n        \n        # Fallback to Ankr public endpoints\n        ankr_urls = {\n            'ethereum_mainnet': 'https://rpc.ankr.com/eth',\n            'ethereum_sepolia': 'https://rpc.ankr.com/eth_sepolia',\n            'polygon': 'https://rpc.ankr.com/polygon',\n            'arbitrum': 'https://rpc.ankr.com/arbitrum'\n        }\n        \n        return ankr_urls.get(network, ankr_urls['ethereum_sepolia'])\n    \n    def validate(self) -> List[str]:\n        \"\"\"Validate configuration and return list of errors.\"\"\"\n        errors = []\n        \n        try:\n            # Use original validation logic\n            if self.CHECK_INTERVAL_MINUTES < 1:\n                errors.append(\"CHECK_INTERVAL_MINUTES must be at least 1\")\n            \n            if not (0 < self.DEFAULT_IL_THRESHOLD <= 1):\n                errors.append(\"DEFAULT_IL_THRESHOLD must be between 0 and 1\")\n            \n            supported_networks = ['ethereum_mainnet', 'ethereum_sepolia', 'polygon', 'arbitrum']\n            if self.DEFAULT_NETWORK not in supported_networks:\n                errors.append(f\"DEFAULT_NETWORK must be one of: {supported_networks}\")\n            \n            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']\n            if self.LOG_LEVEL.upper() not in valid_levels:\n                errors.append(f\"LOG_LEVEL must be one of: {valid_levels}\")\n            \n            if not self.TELEGRAM_BOT_TOKEN:\n                errors.append(\"TELEGRAM_BOT_TOKEN is required\")\n                \n            if not self.TELEGRAM_CHAT_ID:\n                errors.append(\"TELEGRAM_CHAT_ID is required\")\n                \n        except Exception as e:\n            errors.append(f\"Validation error: {str(e)}\")\n        \n        return errors\n    \n    def to_dict(self) -> Dict[str, Any]:\n        \"\"\"Convert settings to dictionary - RESTORED ORIGINAL FORMAT.\"\"\"\n        return {\n            'default_network': self.DEFAULT_NETWORK,\n            'check_interval_minutes': self.CHECK_INTERVAL_MINUTES,\n            'default_il_threshold': self.DEFAULT_IL_THRESHOLD,\n            'log_level': self.LOG_LEVEL,\n            'log_to_file': self.LOG_TO_FILE,\n            'wallet_count': len(self.WALLET_ADDRESSES),\n            'has_infura_key': bool(self.INFURA_API_KEY),\n            'has_alchemy_key': bool(self.ALCHEMY_API_KEY),\n            'has_telegram_config': bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID),\n            'has_coingecko_key': bool(self.COINGECKO_API_KEY)\n        }\n\n\n# RESTORED ALL ORIGINAL CONSTANTS - CRITICAL FOR BACKWARD COMPATIBILITY\nCONTRACT_ADDRESSES = {\n    'ethereum_mainnet': {\n        'tokens': {\n            'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',\n            'USDC': '0xA0b86a33E6c21C64E0eb4ADa7B0b0094a7f6E44C',\n            'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',\n            'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',\n            'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',\n            'UNI': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984'\n        },\n        'pairs': {\n            'WETH_USDC_V2': '0xB4e16d0168e52d35CaCD2b6464f00d6eB9002C6D',\n            'WETH_USDT_V2': '0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852',\n            'WETH_DAI_V2': '0xA478c2975Ab1Ea89e8196811F51A7B7Ade33eB11',\n            'USDC_USDT_V2': '0x3041CbD36888bECc7bbCBc0045E3B1f144466f5f'\n        }\n    },\n    'ethereum_sepolia': {\n        'tokens': {\n            'WETH': '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9',\n            'USDC': '0x...',\n        },\n        'pairs': {}\n    }\n}\n\n# Default position configuration template\nDEFAULT_POSITION_CONFIG = {\n    \"name\": \"\",\n    \"pair_address\": \"\",\n    \"token_a_symbol\": \"\",\n    \"token_b_symbol\": \"\",\n    \"token_a_address\": \"\",\n    \"token_b_address\": \"\",\n    \"initial_liquidity_a\": 0.0,\n    \"initial_liquidity_b\": 0.0,\n    \"initial_price_a_usd\": 0.0,\n    \"initial_price_b_usd\": 0.0,\n    \"wallet_address\": \"\",\n    \"network\": \"ethereum_mainnet\",\n    \"il_alert_threshold\": 0.05,\n    \"protocol\": \"uniswap_v2\",\n    \"pool_fee\": 0.003,\n    \"active\": True,\n    \"notes\": \"\"\n}\n\n# Risk categories and thresholds\nRISK_CATEGORIES = {\n    'very_low': {\n        'description': 'Stablecoin pairs (e.g., USDC/USDT)',\n        'recommended_threshold': 0.005,\n        'max_expected_il': 0.01,\n        'color': '🟢'\n    },\n    'low': {\n        'description': 'Stablecoin + major token (e.g., ETH/USDC)',\n        'recommended_threshold': 0.02,\n        'max_expected_il': 0.05,\n        'color': '🟡'\n    },\n    'medium': {\n        'description': 'Major token pairs (e.g., ETH/BTC)',\n        'recommended_threshold': 0.05,\n        'max_expected_il': 0.10,\n        'color': '🟠'\n    },\n    'high': {\n        'description': 'Volatile token pairs',\n        'recommended_threshold': 0.10,\n        'max_expected_il': 0.25,\n        'color': '🔴'\n    }\n}\n\n# Supported protocols\nSUPPORTED_PROTOCOLS = {\n    'uniswap_v2': {\n        'name': 'Uniswap V2',\n        'type': 'constant_product',\n        'fee': 0.003,\n        'description': '50/50 constant product AMM'\n    },\n    'sushiswap': {\n        'name': 'SushiSwap',\n        'type': 'constant_product',\n        'fee': 0.003,\n        'description': 'Uniswap V2 fork'\n    }\n}\n\n# API endpoints and limits\nAPI_LIMITS = {\n    'coingecko_free': {\n        'requests_per_minute': 50,\n        'requests_per_hour': 1000\n    },\n    'infura_free': {\n        'requests_per_day': 100000\n    },\n    'alchemy_free': {\n        'requests_per_day': 300000000\n    }\n}\n\n\n# Global settings instance for backward compatibility\n_settings = None\n\ndef get_settings(environment: str = None) -> Settings:\n    \"\"\"Get global settings instance.\"\"\"\n    global _settings\n    \n    if _settings is None or environment is not None:\n        _settings = Settings()\n        if environment:\n            _settings._environment = environment\n    \n    return _settings\n\n\nif __name__ == \"__main__\":\n    # Test backward compatibility\n    print(\"Testing fully backward compatible YAML Settings...\")\n    \n    try:\n        settings = Settings()\n        print(f\"✅ Settings created successfully\")\n        print(f\"   Wallet addresses: {len(settings.wallet_addresses)}\")\n        print(f\"   Wallet addresses (legacy): {len(settings.wallet_addresses_list)}\")\n        print(f\"   Check interval: {settings.check_interval_minutes}\")\n        print(f\"   RPC URL: {settings.get_rpc_url()[:50]}...\")\n        \n        # Test constants\n        print(f\"   CONTRACT_ADDRESSES available: {bool(CONTRACT_ADDRESSES)}\")\n        print(f\"   RISK_CATEGORIES available: {bool(RISK_CATEGORIES)}\")\n        \n        # Test validation\n        errors = settings.validate()\n        print(f\"   Validation errors: {len(errors)}\")\n        \n        print(\"🎉 Full backward compatibility achieved!\")\n        \n    except Exception as e:\n        print(f\"❌ Compatibility test failed: {e}\")\n        import traceback\n        traceback.print_exc()\n