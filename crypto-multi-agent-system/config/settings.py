"""
Settings and Configuration Management
====================================

This module contains all configuration settings for the crypto multi-agent system.
Loads settings from environment variables with validation and defaults.

Author: Crypto Multi-Agent Team
"""

import os
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator 


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    # =============================================================================
    # ENVIRONMENT
    # =============================================================================
    ENV: str = Field(default="development", env="ENV")
    DEBUG: bool = Field(default=False, env="DEBUG")
    TEST_MODE: bool = Field(default=False, env="TEST_MODE")
    DRY_RUN: bool = Field(default=True, env="DRY_RUN")
    
    # =============================================================================
    # LOGGING
    # =============================================================================
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_TO_FILE: bool = Field(default=True, env="LOG_TO_FILE")
    
    # =============================================================================
    # BLOCKCHAIN RPC
    # =============================================================================
    INFURA_API_KEY: Optional[str] = Field(default=None, env="INFURA_API_KEY")
    ALCHEMY_API_KEY: Optional[str] = Field(default=None, env="ALCHEMY_API_KEY")
    ANKR_API_KEY: Optional[str] = Field(default=None, env="ANKR_API_KEY")
    
    # =============================================================================
    # MARKET DATA
    # =============================================================================
    COINGECKO_API_KEY: Optional[str] = Field(default=None, env="COINGECKO_API_KEY")
    COINMARKETCAP_API_KEY: Optional[str] = Field(default=None, env="COINMARKETCAP_API_KEY")
    DEX_SCREENER_API_KEY: Optional[str] = Field(default=None, env="DEX_SCREENER_API_KEY")
    
    # =============================================================================
    # SECURITY SERVICES
    # =============================================================================
    GOPLUS_API_KEY: Optional[str] = Field(default=None, env="GOPLUS_API_KEY")
    
    # =============================================================================
    # SOCIAL MEDIA
    # =============================================================================
    TWITTER_BEARER_TOKEN: Optional[str] = Field(default=None, env="TWITTER_BEARER_TOKEN")
    TWITTER_API_KEY: Optional[str] = Field(default=None, env="TWITTER_API_KEY")
    TWITTER_API_SECRET: Optional[str] = Field(default=None, env="TWITTER_API_SECRET")
    
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = Field(default=None, env="TELEGRAM_CHAT_ID")
    TELEGRAM_CHANNEL_ID: Optional[str] = Field(default=None, env="TELEGRAM_CHANNEL_ID")
    
    # =============================================================================
    # AI/ML SERVICES
    # =============================================================================
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    HUGGINGFACE_API_KEY: Optional[str] = Field(default=None, env="HUGGINGFACE_API_KEY")
    
    # =============================================================================
    # DATABASE
    # =============================================================================
    DATABASE_URL: str = Field(
        default="sqlite:///data/database/crypto_agents.db", 
        env="DATABASE_URL"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    INFLUXDB_URL: str = Field(default="http://localhost:8086", env="INFLUXDB_URL")
    INFLUXDB_TOKEN: Optional[str] = Field(default=None, env="INFLUXDB_TOKEN")
    INFLUXDB_ORG: str = Field(default="crypto-agents", env="INFLUXDB_ORG")
    INFLUXDB_BUCKET: str = Field(default="crypto_metrics", env="INFLUXDB_BUCKET")
    
    # =============================================================================
    # VECTOR DATABASE
    # =============================================================================
    PINECONE_API_KEY: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: Optional[str] = Field(default=None, env="PINECONE_ENVIRONMENT")
    
    CHROMA_HOST: str = Field(default="localhost", env="CHROMA_HOST")
    CHROMA_PORT: int = Field(default=8000, env="CHROMA_PORT")
    
    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    MAX_API_CALLS_PER_MINUTE: int = Field(default=50, env="MAX_API_CALLS_PER_MINUTE")
    DISCOVERY_CHECK_INTERVAL: int = Field(default=60, env="DISCOVERY_CHECK_INTERVAL")
    MARKET_CHECK_INTERVAL: int = Field(default=300, env="MARKET_CHECK_INTERVAL")
    
    # =============================================================================
    # KONENKOV STRATEGY PARAMETERS
    # =============================================================================
    DEFAULT_RISK_THRESHOLD: float = Field(default=0.05, env="DEFAULT_RISK_THRESHOLD")
    MAX_POSITION_SIZE_PERCENT: float = Field(default=0.05, env="MAX_POSITION_SIZE_PERCENT")
    USDT_DOMINANCE_THRESHOLD: float = Field(default=4.5, env="USDT_DOMINANCE_THRESHOLD")
    
    # =============================================================================
    # MVP REALISTIC PUMP DETECTION (Based on Gemini feedback)
    # =============================================================================
    PUMP_DETECTION_MVP_MODE: bool = Field(default=True, env="PUMP_DETECTION_MVP_MODE")
    COINGECKO_DAILY_CALL_LIMIT: int = Field(default=323, env="COINGECKO_DAILY_CALL_LIMIT")
    GOPLUS_DAILY_CU_LIMIT: int = Field(default=5000, env="GOPLUS_DAILY_CU_LIMIT")
    DEXSCREENER_RATE_LIMIT_PER_MIN: int = Field(default=300, env="DEXSCREENER_RATE_LIMIT_PER_MIN")
    
    # Realistic scoring weights (only available data)
    NARRATIVE_WEIGHT: int = Field(default=40, env="NARRATIVE_WEIGHT")
    SECURITY_WEIGHT: int = Field(default=35, env="SECURITY_WEIGHT")
    SOCIAL_WEIGHT: int = Field(default=25, env="SOCIAL_WEIGHT")
    
    # =============================================================================
    # SECURITY
    # =============================================================================
    JWT_SECRET: Optional[str] = Field(default=None, env="JWT_SECRET")
    ENCRYPTION_KEY: Optional[str] = Field(default=None, env="ENCRYPTION_KEY")
    
    # =============================================================================
    # MONITORING
    # =============================================================================
    PROMETHEUS_PORT: int = Field(default=9090, env="PROMETHEUS_PORT")
    GRAFANA_URL: str = Field(default="http://localhost:3000", env="GRAFANA_URL")
    ALERT_WEBHOOK_URL: Optional[str] = Field(default=None, env="ALERT_WEBHOOK_URL")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'
    )
        
    def __init__(self, config_file: str = ".env", **kwargs):
        """Initialize settings with optional config file."""
        # Load from custom config file if provided
        if config_file and Path(config_file).exists():
            kwargs.setdefault('_env_file', config_file)
        super().__init__(**kwargs)
    
    @field_validator('LOG_LEVEL')
    @classmethod 
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'LOG_LEVEL must be one of: {valid_levels}')
        return v.upper()
    
    @field_validator('USDT_DOMINANCE_THRESHOLD')
    @classmethod
    def validate_usdt_threshold(cls, v):
        if not 0 < v < 100:
            raise ValueError('USDT_DOMINANCE_THRESHOLD must be between 0 and 100')
        return v
    
    @field_validator('DEFAULT_RISK_THRESHOLD', 'MAX_POSITION_SIZE_PERCENT')
    @classmethod
    def validate_percentage(cls, v):
        if not 0 < v <= 1:
            raise ValueError('Percentage values must be between 0 and 1')
        return v
    
    def get_rpc_url(self, network: str = "ethereum") -> Optional[str]:
        """Get RPC URL for specified network."""
        rpc_urls = {
            "ethereum": {
                "infura": f"https://mainnet.infura.io/v3/{self.INFURA_API_KEY}",
                "alchemy": f"https://eth-mainnet.alchemyapi.io/v2/{self.ALCHEMY_API_KEY}",
                "ankr": "https://rpc.ankr.com/eth"
            },
            "solana": {
                "ankr": "https://rpc.ankr.com/solana",
                "public": "https://api.mainnet-beta.solana.com"
            },
            "base": {
                "ankr": "https://rpc.ankr.com/base",
                "public": "https://mainnet.base.org"
            }
        }
        
        network_urls = rpc_urls.get(network, {})
        
        # Try providers in order of preference
        if self.INFURA_API_KEY and "infura" in network_urls:
            return network_urls["infura"]
        elif self.ALCHEMY_API_KEY and "alchemy" in network_urls:
            return network_urls["alchemy"]
        elif "ankr" in network_urls:
            return network_urls["ankr"]
        elif "public" in network_urls:
            return network_urls["public"]
        
        return None
    
    def has_required_apis(self) -> bool:
        """Check if required API keys are present."""
        # At least one RPC provider
        has_rpc = any([self.INFURA_API_KEY, self.ALCHEMY_API_KEY, self.ANKR_API_KEY])
        
        # Telegram for notifications
        has_telegram = self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID
        
        return has_rpc and has_telegram
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (for logging/debugging)."""
        return {
            'env': self.ENV,
            'debug': self.DEBUG,
            'test_mode': self.TEST_MODE,
            'dry_run': self.DRY_RUN,
            'log_level': self.LOG_LEVEL,
            'usdt_dominance_threshold': self.USDT_DOMINANCE_THRESHOLD,
            'discovery_interval': self.DISCOVERY_CHECK_INTERVAL,
            'market_interval': self.MARKET_CHECK_INTERVAL,
            'has_infura': bool(self.INFURA_API_KEY),
            'has_alchemy': bool(self.ALCHEMY_API_KEY),
            'has_telegram': bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID),
            'has_twitter': bool(self.TWITTER_BEARER_TOKEN),
        }


@dataclass
class AgentConfig:
    """Configuration for individual agents."""
    
    name: str
    enabled: bool = True
    priority: int = 1
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    
    # Agent-specific settings
    settings: Dict[str, Any] = field(default_factory=dict)


# Default agent configurations
DEFAULT_AGENT_CONFIGS = {
    "market_conditions": AgentConfig(
        name="Market Conditions Agent",
        enabled=True,
        priority=1,
        timeout=15,
        settings={
            "check_interval": 300,  # 5 minutes
            "usdt_threshold": 4.5,
            "btc_threshold_low": 40,
            "btc_threshold_high": 70
        }
    ),
    "discovery": AgentConfig(
        name="Discovery Agent", 
        enabled=True,
        priority=2,
        timeout=30,
        settings={
            "check_interval": 60,  # 1 minute
            "min_liquidity": 10000,  # $10k
            "min_volume": 5000,      # $5k
            "max_token_age": 86400   # 24 hours
        }
    ),
    "security": AgentConfig(
        name="Security Agent",
        enabled=True,
        priority=3,
        timeout=20,
        settings={
            "auto_check": True,
            "strict_mode": True,
            "scam_threshold": 70
        }
    ),
    "social_intelligence": AgentConfig(
        name="Social Intelligence Agent",
        enabled=True,
        priority=4,
        timeout=45,
        settings={
            "twitter_enabled": True,
            "telegram_enabled": True,
            "sentiment_threshold": 0.6,
            "influence_weight": 0.8
        }
    ),
    "analysis": AgentConfig(
        name="Analysis Agent",
        enabled=True,
        priority=5,
        timeout=60,
        settings={
            "deep_analysis": True,
            "tokenomics_check": True,
            "team_analysis": True
        }
    ),
    "risk_assessment": AgentConfig(
        name="Risk Assessment Agent",
        enabled=True,
        priority=6,
        timeout=30,
        settings={
            "monte_carlo_simulations": 1000,
            "confidence_interval": 0.95,
            "kelly_fraction": 0.25
        }
    ),
    "decision": AgentConfig(
        name="Decision Agent",
        enabled=True,
        priority=7,
        timeout=15,
        settings={
            "min_confidence": 60,
            "strong_buy_threshold": 80,
            "avoid_threshold": 45
        }
    )
}


def setup_logging(settings: Settings) -> None:
    """Setup logging configuration."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if settings.LOG_TO_FILE:
        handlers.append(logging.FileHandler(log_dir / "crypto_agents.log"))
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=log_format,
        handlers=handlers
    )
    
    # Set specific logger levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
