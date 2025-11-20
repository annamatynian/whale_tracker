"""
Configuration Validation
========================

This module validates environment configuration and system requirements.

Author: Crypto Multi-Agent Team
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from config.settings import get_settings


def validate_environment() -> List[str]:
    """
    Validate environment configuration.
    
    Returns:
        List[str]: List of validation errors (empty if valid)
    """
    errors = []
    settings = get_settings()
    
    # Check Python version
    if sys.version_info < (3, 8):
        errors.append("Python 3.8 or higher is required")
    
    # Check required directories
    required_dirs = [
        "data",
        "data/logs", 
        "data/database",
        "data/vector_stores",
        "data/models"
    ]
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory {dir_path}: {e}")
    
    # Check RPC providers (at least one required)
    rpc_providers = [
        settings.INFURA_API_KEY,
        settings.ALCHEMY_API_KEY,
        settings.ANKR_API_KEY
    ]
    
    if not any(rpc_providers):
        errors.append("At least one RPC provider API key is required (INFURA_API_KEY, ALCHEMY_API_KEY, or ANKR_API_KEY)")
    
    # Check Telegram configuration (required for notifications)
    if not settings.TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is required")
    
    if not settings.TELEGRAM_CHAT_ID:
        errors.append("TELEGRAM_CHAT_ID is required")
    
    # Validate Telegram bot token format
    if settings.TELEGRAM_BOT_TOKEN and not _is_valid_telegram_token(settings.TELEGRAM_BOT_TOKEN):
        errors.append("TELEGRAM_BOT_TOKEN format is invalid (should be like: 1234567890:ABCdefGHI...)")
    
    # Check database URL format
    if settings.DATABASE_URL and not _is_valid_database_url(settings.DATABASE_URL):
        errors.append("DATABASE_URL format is invalid")
    
    # Check Redis URL format
    if settings.REDIS_URL and not _is_valid_redis_url(settings.REDIS_URL):
        errors.append("REDIS_URL format is invalid")
    
    # Validate numeric settings
    if settings.DISCOVERY_CHECK_INTERVAL < 10:
        errors.append("DISCOVERY_CHECK_INTERVAL must be at least 10 seconds")
    
    if settings.MARKET_CHECK_INTERVAL < 60:
        errors.append("MARKET_CHECK_INTERVAL must be at least 60 seconds")
    
    if settings.MAX_API_CALLS_PER_MINUTE < 1:
        errors.append("MAX_API_CALLS_PER_MINUTE must be at least 1")
    
    # Check percentage values
    if not 0 < settings.DEFAULT_RISK_THRESHOLD <= 1:
        errors.append("DEFAULT_RISK_THRESHOLD must be between 0 and 1")
    
    if not 0 < settings.MAX_POSITION_SIZE_PERCENT <= 1:
        errors.append("MAX_POSITION_SIZE_PERCENT must be between 0 and 1")
    
    if not 0 < settings.USDT_DOMINANCE_THRESHOLD < 100:
        errors.append("USDT_DOMINANCE_THRESHOLD must be between 0 and 100")
    
    # Check environment-specific requirements
    if settings.ENV == "production":
        production_errors = _validate_production_requirements(settings)
        errors.extend(production_errors)
    
    return errors


def _is_valid_telegram_token(token: str) -> bool:
    """Validate Telegram bot token format."""
    if not token:
        return False
    
    parts = token.split(":")
    if len(parts) != 2:
        return False
    
    # First part should be numeric (bot ID)
    try:
        int(parts[0])
    except ValueError:
        return False
    
    # Second part should be alphanumeric (at least 35 chars)
    if len(parts[1]) < 35 or not parts[1].replace("_", "").replace("-", "").isalnum():
        return False
    
    return True


def _is_valid_database_url(url: str) -> bool:
    """Validate database URL format."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ["sqlite", "postgresql", "mysql"]
    except Exception:
        return False


def _is_valid_redis_url(url: str) -> bool:
    """Validate Redis URL format."""
    try:
        parsed = urlparse(url)
        return parsed.scheme == "redis"
    except Exception:
        return False


def _validate_production_requirements(settings) -> List[str]:
    """Validate production-specific requirements."""
    errors = []
    
    # Production must have security keys
    if not settings.JWT_SECRET:
        errors.append("JWT_SECRET is required in production")
    
    if not settings.ENCRYPTION_KEY:
        errors.append("ENCRYPTION_KEY is required in production")
    
    # Production should not use default values
    if settings.DEBUG:
        errors.append("DEBUG should be False in production")
    
    if settings.DRY_RUN:
        errors.append("DRY_RUN should be False in production")
    
    # Production should have monitoring
    if not settings.ALERT_WEBHOOK_URL:
        errors.append("ALERT_WEBHOOK_URL is recommended in production")
    
    # Production should use external databases
    if "sqlite" in settings.DATABASE_URL.lower():
        errors.append("SQLite is not recommended for production, use PostgreSQL")
    
    return errors


def check_api_key_validity() -> Dict[str, bool]:
    """
    Check validity of API keys (format, not actual connectivity).
    
    Returns:
        Dict[str, bool]: API key validity status
    """
    settings = get_settings()
    
    checks = {
        "infura": _check_infura_key_format(settings.INFURA_API_KEY),
        "alchemy": _check_alchemy_key_format(settings.ALCHEMY_API_KEY),
        "coingecko": _check_coingecko_key_format(settings.COINGECKO_API_KEY),
        "twitter": _check_twitter_key_format(settings.TWITTER_BEARER_TOKEN),
        "telegram": _is_valid_telegram_token(settings.TELEGRAM_BOT_TOKEN),
    }
    
    return checks


def _check_infura_key_format(key: Optional[str]) -> bool:
    """Check Infura API key format."""
    if not key:
        return False
    # Infura project IDs are 32 character hex strings
    return len(key) == 32 and all(c in '0123456789abcdef' for c in key.lower())


def _check_alchemy_key_format(key: Optional[str]) -> bool:
    """Check Alchemy API key format."""
    if not key:
        return False
    # Alchemy keys are typically 32+ character alphanumeric strings
    return len(key) >= 32 and key.isalnum()


def _check_coingecko_key_format(key: Optional[str]) -> bool:
    """Check CoinGecko API key format."""
    if not key:
        return True  # CoinGecko API key is optional
    # CoinGecko keys are typically UUID-like strings
    return len(key) > 20 and ('-' in key or key.isalnum())


def _check_twitter_key_format(token: Optional[str]) -> bool:
    """Check Twitter bearer token format."""
    if not token:
        return False
    # Twitter bearer tokens start with specific patterns
    return (token.startswith("AAAA") or token.startswith("Bearer ")) and len(token) > 50


def generate_system_info() -> Dict[str, Any]:
    """
    Generate system information for diagnostics.
    
    Returns:
        Dict[str, Any]: System information
    """
    settings = get_settings()
    
    return {
        "python_version": sys.version,
        "platform": sys.platform,
        "settings": settings.to_dict(),
        "api_key_status": check_api_key_validity(),
        "directories": {
            "data": Path("data").exists(),
            "logs": Path("data/logs").exists(),
            "database": Path("data/database").exists(),
            "vector_stores": Path("data/vector_stores").exists(),
            "models": Path("data/models").exists(),
        },
        "validation_errors": validate_environment()
    }


def print_system_status() -> None:
    """Print comprehensive system status."""
    info = generate_system_info()
    
    print("🔍 Crypto Multi-Agent System - Configuration Status")
    print("=" * 60)
    
    # Environment
    print(f"Environment: {info['settings']['env']}")
    print(f"Python Version: {info['python_version'].split()[0]}")
    print(f"Platform: {info['platform']}")
    
    # API Keys Status
    print("\n📡 API Keys Status:")
    for service, valid in info['api_key_status'].items():
        status = "✅ OK" if valid else "❌ Missing/Invalid"
        print(f"  {service.capitalize()}: {status}")
    
    # Directories
    print("\n📁 Directories:")
    for dir_name, exists in info['directories'].items():
        status = "✅ Exists" if exists else "❌ Missing"
        print(f"  {dir_name}: {status}")
    
    # Validation Errors
    if info['validation_errors']:
        print("\n❌ Configuration Errors:")
        for error in info['validation_errors']:
            print(f"  • {error}")
    else:
        print("\n✅ Configuration is valid!")
    
    print("=" * 60)


if __name__ == "__main__":
    """Run configuration validation as standalone script."""
    print_system_status()
