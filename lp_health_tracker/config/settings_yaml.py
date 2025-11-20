"""
YAML-based Settings Configuration
================================

Modern configuration management using YAML files with environment support.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator


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


class Settings(BaseModel):
    """
    Main settings class with YAML configuration support.
    
    Automatically loads base.yaml + environment-specific config.
    """
    
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
    
    @classmethod
    def load(cls, environment: str = "development") -> "Settings":
        """
        Load settings from YAML files.
        
        Args:
            environment: Environment name (development, production, testing)
        """
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
        merged_config = cls._deep_merge(base_config, env_config)
        
        # Replace environment variable placeholders
        merged_config = cls._replace_env_vars(merged_config)
        
        return cls(**merged_config)
    
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
    
    @field_validator('blockchain')
    @classmethod
    def validate_blockchain_config(cls, v):
        """Validate blockchain configuration."""
        if not v.providers:
            # Set default providers if none specified
            v.providers = {
                "infura": BlockchainProvider(),
                "alchemy": BlockchainProvider(priority=2),
                "ankr": BlockchainProvider(priority=3, public_endpoints=True)
            }
        return v
    
    @field_validator('monitoring')
    @classmethod
    def validate_monitoring(cls, v):
        """Validate monitoring configuration."""
        # Validate wallet addresses
        validated_addresses = []
        for addr in v.wallet_addresses:
            if isinstance(addr, str) and addr.startswith('0x') and len(addr) == 42:
                validated_addresses.append(addr.lower())
        v.wallet_addresses = validated_addresses
        
        return v
    
    def get_rpc_url(self, network: Optional[str] = None) -> str:
        """Get RPC URL for specified network."""
        network = network or self.blockchain.default_network
        
        # Sort providers by priority
        sorted_providers = sorted(
            self.blockchain.providers.items(),
            key=lambda x: x[1].priority
        )
        
        for provider_name, provider_config in sorted_providers:
            if not provider_config.api_key and not provider_config.public_endpoints:
                continue
                
            url = self._build_rpc_url(provider_name, provider_config, network)
            if url:
                return url
        
        # Fallback to public endpoints
        fallback_urls = {
            'ethereum_mainnet': 'https://rpc.ankr.com/eth',
            'ethereum_sepolia': 'https://rpc.ankr.com/eth_sepolia',
            'polygon': 'https://rpc.ankr.com/polygon',
            'arbitrum': 'https://rpc.ankr.com/arbitrum'
        }
        
        return fallback_urls.get(network, fallback_urls['ethereum_sepolia'])
    
    def _build_rpc_url(self, provider_name: str, provider_config: BlockchainProvider, network: str) -> Optional[str]:
        """Build RPC URL for specific provider and network."""
        if provider_name == "infura" and provider_config.api_key:
            infura_urls = {
                'ethereum_mainnet': f'https://mainnet.infura.io/v3/{provider_config.api_key}',
                'ethereum_sepolia': f'https://sepolia.infura.io/v3/{provider_config.api_key}',
                'polygon': f'https://polygon-mainnet.infura.io/v3/{provider_config.api_key}',
                'arbitrum': f'https://arbitrum-mainnet.infura.io/v3/{provider_config.api_key}'
            }
            return infura_urls.get(network)
            
        elif provider_name == "alchemy" and provider_config.api_key:
            alchemy_urls = {
                'ethereum_mainnet': f'https://eth-mainnet.alchemyapi.io/v2/{provider_config.api_key}',
                'ethereum_sepolia': f'https://eth-sepolia.alchemyapi.io/v2/{provider_config.api_key}',
                'polygon': f'https://polygon-mainnet.alchemyapi.io/v2/{provider_config.api_key}',
                'arbitrum': f'https://arb-mainnet.alchemyapi.io/v2/{provider_config.api_key}'
            }
            return alchemy_urls.get(network)
            
        return None
    
    @property 
    def wallet_addresses(self) -> List[str]:
        """Get wallet addresses - for backward compatibility."""
        return self.monitoring.wallet_addresses
    
    @property
    def check_interval_minutes(self) -> int:
        """Get check interval - for backward compatibility."""
        return self.monitoring.intervals.check_minutes
    
    @property
    def default_il_threshold(self) -> float:
        """Get IL threshold - for backward compatibility."""
        return self.monitoring.thresholds.default_il_threshold
    
    @property
    def log_level(self) -> str:
        """Get log level - for backward compatibility."""
        return self.logging.level
    
    @property
    def telegram_bot_token(self) -> str:
        """Get Telegram bot token - for backward compatibility."""
        return self.notifications.telegram.bot_token
    
    @property
    def telegram_chat_id(self) -> str:
        """Get Telegram chat ID - for backward compatibility."""
        return self.notifications.telegram.chat_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            'environment': getattr(self, '_environment', 'unknown'),
            'default_network': self.blockchain.default_network,
            'check_interval_minutes': self.check_interval_minutes,
            'default_il_threshold': self.default_il_threshold,
            'log_level': self.log_level,
            'wallet_count': len(self.wallet_addresses),
            'has_telegram_config': bool(self.telegram_bot_token and self.telegram_chat_id),
            'features_enabled': {
                'v2_analytics': self.features.v2_analytics.enabled,
                'v3_analytics': self.features.v3_analytics.enabled,
                'ml_models': self.features.ml_models.enabled,
            }
        }


# Global settings instance
_settings = None

def get_settings(environment: str = None) -> Settings:
    """Get global settings instance."""
    global _settings
    
    if _settings is None or environment is not None:
        # Determine environment from env var if not specified
        if environment is None:
            environment = os.getenv('ENVIRONMENT', 'development')
        
        _settings = Settings.load(environment)
        _settings._environment = environment
    
    return _settings


# For backward compatibility
def Settings_old_interface():
    """Create Settings instance with old interface."""
    return get_settings()


if __name__ == "__main__":
    # Test the YAML settings
    print("Testing YAML Settings...")
    settings = get_settings("development")
    
    print(f"✅ Loaded settings for: {settings._environment}")
    print(f"Default network: {settings.blockchain.default_network}")
    print(f"Wallet addresses: {settings.wallet_addresses}")
    print(f"Check interval: {settings.check_interval_minutes} minutes")
    print(f"Telegram configured: {bool(settings.telegram_bot_token)}")
    print(f"V3 analytics enabled: {settings.features.v3_analytics.enabled}")
    
    # Test serialization
    config_dict = settings.to_dict()
    print(f"✅ Serialization works: {type(config_dict)}")
    
    print("🎉 YAML Settings working perfectly!")
