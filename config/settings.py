"""
Whale Tracker - YAML Configuration System
========================================================

Hierarchical configuration with YAML + .env support.
Organized by development phases (MVP, Phase 2, Phase 3, Phase 4).

Adapted from: lp_health_tracker/config/settings.py
Enhanced for: Whale Tracker Project
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
    etherscan: APIConfig = Field(default_factory=APIConfig)


class WhaleMonitoringIntervals(BaseModel):
    """Whale monitoring timing configuration."""
    check_minutes: int = 15
    alert_cooldown_minutes: int = 60
    price_update_seconds: int = 300
    onehop_check_hours: int = 2  # How long to check for one-hop transfers


class WhaleThresholds(BaseModel):
    """Whale alert threshold configuration."""
    min_amount_usd: float = 100000.0  # Minimum $100k for alerts
    anomaly_multiplier: float = 1.3  # 1.3x above average = anomaly
    onehop_confidence_threshold: float = 0.7  # 70% confidence for one-hop alerts


class WhaleMonitoringConfig(BaseModel):
    """Whale monitoring configuration."""
    whale_addresses: List[str] = Field(default_factory=list)  # Whale addresses to monitor
    intervals: WhaleMonitoringIntervals = Field(default_factory=WhaleMonitoringIntervals)
    thresholds: WhaleThresholds = Field(default_factory=WhaleThresholds)
    onehop_enabled: bool = True  # Enable one-hop tracking


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    file_logging: bool = True
    log_rotation: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


class MVPFeatures(BaseModel):
    """MVP / Phase 1 features."""
    enabled: bool = True
    simple_monitoring: bool = True  # Basic whale → exchange monitoring
    onehop_tracking: bool = True  # whale → unknown → exchange
    anomaly_detection: bool = True  # Statistical anomaly detection


class Phase2Features(BaseModel):
    """Phase 2: Price Impact Tracking."""
    enabled: bool = False
    price_impact_tracking: bool = False  # Track price changes after whale tx
    historical_data_storage: bool = False  # Save to database
    impact_checkpoints: List[int] = Field(default_factory=lambda: [1, 6, 24])  # Hours after tx


class Phase3Features(BaseModel):
    """Phase 3: Pattern Analysis."""
    enabled: bool = False
    pattern_database: bool = False  # Build whale behavior patterns
    whale_profiling: bool = False  # Create profiles for each whale
    pattern_matching: bool = False  # Match current behavior to historical patterns


class Phase4Features(BaseModel):
    """Phase 4: AI Analysis."""
    enabled: bool = False
    ai_analysis: bool = False  # Claude/DeepSeek analysis
    market_context: bool = False  # Include RSI, MACD, volume
    voice_alerts: bool = False  # OpenAI TTS for critical alerts
    ai_model: str = "claude-sonnet-4"  # AI model to use


class PhasesConfig(BaseModel):
    """Development phases configuration."""
    mvp: MVPFeatures = Field(default_factory=MVPFeatures)
    phase2_price_impact: Phase2Features = Field(default_factory=Phase2Features)
    phase3_patterns: Phase3Features = Field(default_factory=Phase3Features)
    phase4_ai: Phase4Features = Field(default_factory=Phase4Features)


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


class DatabaseConfig(BaseModel):
    """Database configuration for PostgreSQL/SQLite."""
    db_type: str = Field(default="sqlite", description="Database type: sqlite | postgresql")

    # SQLite settings
    sqlite_path: str = Field(default="data/database/whale_tracker.db", description="SQLite database path")

    # PostgreSQL settings
    db_host: str = Field(default="localhost", description="PostgreSQL host")
    db_port: int = Field(default=5432, description="PostgreSQL port")
    db_name: str = Field(default="whale_tracker", description="PostgreSQL database name")
    db_user: str = Field(default="postgres", description="PostgreSQL user")
    db_password: str = Field(default="", description="PostgreSQL password")

    # Connection pool settings
    db_pool_size: int = Field(default=5, ge=1, le=50, description="Connection pool size")
    db_max_overflow: int = Field(default=10, ge=0, le=50, description="Max overflow connections")
    db_echo: bool = Field(default=False, description="Echo SQL queries (debugging)")

    @field_validator('db_type')
    @classmethod
    def validate_db_type(cls, v):
        """Validate database type"""
        allowed = ['sqlite', 'postgresql']
        if v.lower() not in allowed:
            raise ValueError(f'db_type must be one of: {allowed}')
        return v.lower()

    def get_connection_url(self, async_mode: bool = False) -> str:
        """
        Generate database connection URL.

        Args:
            async_mode: If True, return async URL (for asyncpg)

        Returns:
            Database connection URL
        """
        if self.db_type == 'sqlite':
            prefix = 'sqlite+aiosqlite' if async_mode else 'sqlite'
            return f"{prefix}:///{self.sqlite_path}"
        else:  # postgresql
            prefix = 'postgresql+asyncpg' if async_mode else 'postgresql'
            return f"{prefix}://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


class Settings(BaseModel):
    """
    Whale Tracker Settings - YAML + .env Configuration

    Hierarchical configuration organized by development phases.
    Supports both YAML files and environment variables.
    """

    # Core configuration sections
    blockchain: BlockchainConfig = Field(default_factory=BlockchainConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    apis: APIsConfig = Field(default_factory=APIsConfig)
    whale_monitoring: WhaleMonitoringConfig = Field(default_factory=WhaleMonitoringConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    phases: PhasesConfig = Field(default_factory=PhasesConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    development: DevelopmentConfig = Field(default_factory=DevelopmentConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    known_addresses: Dict[str, Any] = Field(default_factory=dict)  # Exchange addresses
    
    # BACKWARD COMPATIBILITY: Original flat fields
    INFURA_API_KEY: str = Field(default="", description="Infura API key for RPC calls")
    ALCHEMY_API_KEY: str = Field(default="", description="Alchemy API key for RPC calls")
    ANKR_API_KEY: str = Field(default="", description="Ankr API key for RPC calls")
    ETHERSCAN_API_KEY: str = Field(default="", description="Etherscan API key")
    TELEGRAM_BOT_TOKEN: str = Field(default="", description="Telegram bot token for notifications")
    TELEGRAM_CHAT_ID: str = Field(default="", description="Telegram chat ID for notifications")
    COINGECKO_API_KEY: str = Field(default="", description="CoinGecko API key for price data")
    WHALE_ADDRESSES: List[str] = Field(default_factory=list, description="List of whale addresses to monitor")
    DEFAULT_NETWORK: str = Field(default="ethereum_mainnet", description="Default blockchain network")
    CHECK_INTERVAL_MINUTES: int = Field(default=15, description="Monitoring interval in minutes")
    MIN_AMOUNT_USD: float = Field(default=100000.0, description="Minimum transaction amount in USD")
    ONEHOP_ENABLED: bool = Field(default=True, description="Enable one-hop tracking")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_TO_FILE: bool = Field(default=True, description="Enable file logging")
    DEFAULT_IL_THRESHOLD: float = Field(default=0.05, description="IL threshold (legacy from LP tracker)")

    # DATABASE CONFIGURATION (Phase 2 compatibility)
    DB_TYPE: str = Field(default="sqlite", description="Database type: sqlite | postgresql")
    DB_HOST: str = Field(default="localhost", description="PostgreSQL host")
    DB_PORT: int = Field(default=5432, description="PostgreSQL port")
    DB_NAME: str = Field(default="whale_tracker", description="PostgreSQL database name")
    DB_USER: str = Field(default="postgres", description="PostgreSQL user")
    DB_PASSWORD: str = Field(default="", description="PostgreSQL password")
    DB_POOL_SIZE: int = Field(default=5, description="Connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=10, description="Max overflow connections")
    DB_ECHO: bool = Field(default=False, description="Echo SQL queries (debugging)")
    SQLITE_PATH: str = Field(default="data/database/whale_tracker.db", description="SQLite database path")
    
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
            etherscan = yaml_data['apis'].get('etherscan', {})
            flat['ETHERSCAN_API_KEY'] = etherscan.get('api_key', '')

        if 'whale_monitoring' in yaml_data:
            monitoring = yaml_data['whale_monitoring']
            flat['WHALE_ADDRESSES'] = monitoring.get('whale_addresses', [])
            flat['ONEHOP_ENABLED'] = monitoring.get('onehop_enabled', True)
            if 'intervals' in monitoring:
                flat['CHECK_INTERVAL_MINUTES'] = monitoring['intervals'].get('check_minutes', 15)
            if 'thresholds' in monitoring:
                flat['MIN_AMOUNT_USD'] = monitoring['thresholds'].get('min_amount_usd', 100000.0)

        if 'logging' in yaml_data:
            logging_config = yaml_data['logging']
            flat['LOG_LEVEL'] = logging_config.get('level', 'INFO')
            flat['LOG_TO_FILE'] = logging_config.get('file_logging', True)

        if 'database' in yaml_data:
            db_config = yaml_data['database']
            flat['DB_TYPE'] = db_config.get('db_type', 'sqlite')
            flat['DB_HOST'] = db_config.get('db_host', 'localhost')
            flat['DB_PORT'] = db_config.get('db_port', 5432)
            flat['DB_NAME'] = db_config.get('db_name', 'whale_tracker')
            flat['DB_USER'] = db_config.get('db_user', 'postgres')
            flat['DB_PASSWORD'] = db_config.get('db_password', '')
            flat['DB_POOL_SIZE'] = db_config.get('db_pool_size', 5)
            flat['DB_MAX_OVERFLOW'] = db_config.get('db_max_overflow', 10)
            flat['DB_ECHO'] = db_config.get('db_echo', False)
            flat['SQLITE_PATH'] = db_config.get('sqlite_path', 'data/database/whale_tracker.db')

        # Copy other sections as-is
        for key in ['performance', 'phases', 'development', 'known_addresses']:
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

        if not self.apis.etherscan.api_key:
            self.apis.etherscan.api_key = self.ETHERSCAN_API_KEY

        if not self.whale_monitoring.whale_addresses:
            self.whale_monitoring.whale_addresses = self.WHALE_ADDRESSES

        if self.whale_monitoring.intervals.check_minutes == 15:  # Default value
            self.whale_monitoring.intervals.check_minutes = self.CHECK_INTERVAL_MINUTES

        if self.whale_monitoring.thresholds.min_amount_usd == 100000.0:  # Default value
            self.whale_monitoring.thresholds.min_amount_usd = self.MIN_AMOUNT_USD

        if not self.logging.level or self.logging.level == 'INFO':
            self.logging.level = self.LOG_LEVEL
            self.logging.file_logging = self.LOG_TO_FILE

        self.blockchain.default_network = self.DEFAULT_NETWORK
        self.whale_monitoring.onehop_enabled = self.ONEHOP_ENABLED

        # Sync database settings
        if not self.database.db_type or self.database.db_type == 'sqlite':  # Default
            self.database.db_type = self.DB_TYPE
            self.database.db_host = self.DB_HOST
            self.database.db_port = self.DB_PORT
            self.database.db_name = self.DB_NAME
            self.database.db_user = self.DB_USER
            self.database.db_password = self.DB_PASSWORD
            self.database.db_pool_size = self.DB_POOL_SIZE
            self.database.db_max_overflow = self.DB_MAX_OVERFLOW
            self.database.db_echo = self.DB_ECHO
            self.database.sqlite_path = self.SQLITE_PATH
    
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
        """Convert settings to dictionary."""
        return {
            'default_network': self.DEFAULT_NETWORK,
            'check_interval_minutes': self.CHECK_INTERVAL_MINUTES,
            'min_amount_usd': self.MIN_AMOUNT_USD,
            'onehop_enabled': self.ONEHOP_ENABLED,
            'log_level': self.LOG_LEVEL,
            'log_to_file': self.LOG_TO_FILE,
            'whale_count': len(self.WHALE_ADDRESSES),
            'has_infura_key': bool(self.INFURA_API_KEY),
            'has_alchemy_key': bool(self.ALCHEMY_API_KEY),
            'has_etherscan_key': bool(self.ETHERSCAN_API_KEY),
            'has_telegram_config': bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID),
            'has_coingecko_key': bool(self.COINGECKO_API_KEY)
        }


# WHALE TRACKER CONSTANTS
# Top exchange addresses for whale tracking
KNOWN_EXCHANGE_ADDRESSES = {
    # Binance (top priority)
    '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE': 'Binance Hot Wallet',
    '0x28C6c06298d514Db089934071355E5743bf21d60': 'Binance Cold Wallet',
    '0xdfd5293d8e347dfe59e90efd55b2956a1343963d': 'Binance Wallet 3',
    '0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549': 'Binance Wallet 4',
    '0xD551234Ae421e3BCBA99A0Da6d736074f22192FF': 'Binance Wallet 5',
    '0x564286362092D8e7936f0549571a803B203aAceD': 'Binance Wallet 6',
    '0x0681d8Db095565FE8A346fA0277bFfdE9C0eDBBF': 'Binance Wallet 7',

    # Coinbase
    '0x71660c4005BA85c37ccec55d0C4493E66Fe775d3': 'Coinbase Wallet 1',
    '0x503828976D22510aad0201ac7EC88293211D23Da': 'Coinbase Wallet 2',
    '0xddfAbCdc4D8FfC6d5beaf154f18B778f892A0740': 'Coinbase Wallet 3',
    '0x3cD751E6b0078Be393132286c442345e5DC49699': 'Coinbase Wallet 4',

    # Kraken
    '0x2910543Af39abA0Cd09dBb2D50200b3E800A63D2': 'Kraken Wallet 1',
    '0x0A869d79a7052C7f1b55a8eBAbbEa3420F0D1E13': 'Kraken Wallet 2',
    '0xE853c56864A2ebe4576a807D26Fdc4A0adA51919': 'Kraken Wallet 3',

    # Bitfinex
    '0x1151314c646Ce4E0eFD76d1aF4760aE66a9Fe30F': 'Bitfinex Wallet 1',
    '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0': 'Bitfinex Wallet 2',

    # OKX
    '0x98ec059Dc3aDFBdd63429454aEB0c990FBA4A128': 'OKX Wallet 1',
    '0x6cC5F688a315f3dC28A7781717a9A798a59fDA7b': 'OKX Wallet 2',

    # Huobi
    '0xAB5C66752a9e8167967685F1450532fB96d5d24f': 'Huobi Wallet 1',
    '0x6748F50f686bfbcA6Fe8ad62b22228b87F31ff2b': 'Huobi Wallet 2',

    # Bybit
    '0xf89d7b9c864f589bbF53a82105107622B35EaA40': 'Bybit Wallet 1',

    # KuCoin
    '0x2B5634C42055806a59e9107ED44D43c426E58258': 'KuCoin Wallet 1',

    # Gate.io
    '0x0D0707963952f2fBA59dD06f2b425ace40b492Fe': 'Gate.io Wallet 1',

    # Bittrex
    '0xFBb1b73C4f0BDa4f67dcA266ce6Ef42f520fBB98': 'Bittrex Wallet 1',
}

# Known contract types (for is_contract filtering)
KNOWN_CONTRACT_TYPES = {
    'dex': ['Uniswap', 'SushiSwap', 'Curve', 'Balancer'],
    'bridge': ['Arbitrum Bridge', 'Optimism Bridge', 'Polygon Bridge'],
    'staking': ['Lido', 'Rocket Pool', 'Frax'],
    'defi': ['Aave', 'Compound', 'MakerDAO']
}

# API endpoints and limits
API_LIMITS = {
    'coingecko_free': {
        'requests_per_minute': 50,
        'requests_per_hour': 1000
    },
    'etherscan_free': {
        'requests_per_second': 5,
        'requests_per_day': 100000
    },
    'infura_free': {
        'requests_per_day': 100000
    },
    'alchemy_free': {
        'requests_per_day': 300000000
    }
}


# Global settings instance
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
    # Test settings
    print("Testing Whale Tracker YAML Settings...")

    try:
        settings = Settings()
        print(f"✅ Settings created successfully")
        print(f"   Whale addresses: {len(settings.WHALE_ADDRESSES)}")
        print(f"   Check interval: {settings.CHECK_INTERVAL_MINUTES} minutes")
        print(f"   Min amount: ${settings.MIN_AMOUNT_USD:,.0f}")
        print(f"   One-hop enabled: {settings.ONEHOP_ENABLED}")
        print(f"   RPC URL: {settings.get_rpc_url()[:50]}...")

        # Test constants
        print(f"   Known exchanges: {len(KNOWN_EXCHANGE_ADDRESSES)}")

        # Test validation
        errors = settings.validate()
        if errors:
            print(f"   ⚠️ Validation errors: {errors}")
        else:
            print(f"   ✅ Validation passed")

        print("🎉 Whale Tracker settings initialized!")

    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        import traceback
        traceback.print_exc()
