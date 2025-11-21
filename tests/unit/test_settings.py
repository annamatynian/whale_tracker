"""
Unit tests for Whale Tracker Settings
======================================

Tests YAML configuration system, validation, and backward compatibility.
"""

import os
import pytest
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import (
    Settings,
    get_settings,
    KNOWN_EXCHANGE_ADDRESSES,
    API_LIMITS
)


class TestSettings:
    """Test Settings class initialization and configuration."""

    def test_settings_default_initialization(self, monkeypatch):
        """Test that settings can be initialized with defaults."""
        # Set production environment for production defaults
        monkeypatch.setenv("ENVIRONMENT", "production")
        settings = Settings()

        assert settings.DEFAULT_NETWORK == "ethereum_mainnet"
        assert settings.CHECK_INTERVAL_MINUTES == 15
        assert settings.MIN_AMOUNT_USD == 100000.0
        assert settings.ONEHOP_ENABLED == True
        assert settings.LOG_LEVEL == "INFO"

    def test_settings_from_env_vars(self, monkeypatch):
        """Test settings loading from environment variables."""
        # Set environment variables
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")
        monkeypatch.setenv("INFURA_API_KEY", "test_infura_key")
        monkeypatch.setenv("CHECK_INTERVAL_MINUTES", "30")
        monkeypatch.setenv("MIN_AMOUNT_USD", "50000.0")

        settings = Settings()

        assert settings.TELEGRAM_BOT_TOKEN == "test_bot_token"
        assert settings.TELEGRAM_CHAT_ID == "123456789"
        assert settings.INFURA_API_KEY == "test_infura_key"

    def test_whale_monitoring_config(self, monkeypatch):
        """Test whale monitoring configuration structure."""
        # Set production environment for production defaults
        monkeypatch.setenv("ENVIRONMENT", "production")
        settings = Settings()

        assert hasattr(settings, 'whale_monitoring')
        assert settings.whale_monitoring.intervals.check_minutes == 15
        assert settings.whale_monitoring.thresholds.min_amount_usd == 100000.0
        assert settings.whale_monitoring.thresholds.anomaly_multiplier == 1.3
        assert settings.whale_monitoring.onehop_enabled == True

    def test_phases_config(self):
        """Test development phases configuration."""
        settings = Settings()

        # MVP should be enabled by default
        assert settings.phases.mvp.enabled == True
        assert settings.phases.mvp.simple_monitoring == True
        assert settings.phases.mvp.onehop_tracking == True
        assert settings.phases.mvp.anomaly_detection == True

        # Future phases should be disabled
        assert settings.phases.phase2_price_impact.enabled == False
        assert settings.phases.phase3_patterns.enabled == False
        assert settings.phases.phase4_ai.enabled == False

    def test_validation_required_fields(self):
        """Test validation catches missing required fields."""
        settings = Settings()
        settings.TELEGRAM_BOT_TOKEN = ""
        settings.TELEGRAM_CHAT_ID = ""

        errors = settings.validate()

        assert len(errors) > 0
        assert any("TELEGRAM_BOT_TOKEN" in err for err in errors)
        assert any("TELEGRAM_CHAT_ID" in err for err in errors)

    def test_validation_thresholds(self):
        """Test validation of configuration thresholds."""
        settings = Settings()
        settings.CHECK_INTERVAL_MINUTES = -1  # Invalid

        errors = settings.validate()

        assert len(errors) > 0
        assert any("CHECK_INTERVAL_MINUTES" in err for err in errors)

    def test_get_rpc_url_priority(self):
        """Test RPC URL priority (Infura → Alchemy → Ankr)."""
        settings = Settings()
        settings.INFURA_API_KEY = "test_infura"
        settings.ALCHEMY_API_KEY = "test_alchemy"
        settings.ANKR_API_KEY = "test_ankr"

        # Should prioritize Infura
        rpc_url = settings.get_rpc_url("ethereum_mainnet")
        assert "infura" in rpc_url.lower()
        assert "test_infura" in rpc_url

    def test_get_rpc_url_fallback(self):
        """Test RPC URL falls back to public endpoints."""
        settings = Settings()
        settings.INFURA_API_KEY = ""
        settings.ALCHEMY_API_KEY = ""

        # Should fall back to Ankr public endpoint
        rpc_url = settings.get_rpc_url("ethereum_mainnet")
        assert "ankr.com" in rpc_url.lower()

    def test_to_dict(self):
        """Test settings serialization to dictionary."""
        settings = Settings()
        settings.WHALE_ADDRESSES = ["0x123", "0x456"]

        settings_dict = settings.to_dict()

        assert 'default_network' in settings_dict
        assert 'check_interval_minutes' in settings_dict
        assert 'min_amount_usd' in settings_dict
        assert 'onehop_enabled' in settings_dict
        assert settings_dict['whale_count'] == 2


class TestConstants:
    """Test constants and known addresses."""

    def test_known_exchange_addresses_exist(self):
        """Test that known exchange addresses are defined."""
        assert len(KNOWN_EXCHANGE_ADDRESSES) > 0
        assert isinstance(KNOWN_EXCHANGE_ADDRESSES, dict)

    def test_known_exchange_addresses_format(self):
        """Test that exchange addresses have correct format."""
        for address, name in KNOWN_EXCHANGE_ADDRESSES.items():
            assert address.startswith('0x')
            assert len(address) == 42  # Ethereum address length
            assert isinstance(name, str)
            assert len(name) > 0

    def test_known_exchange_addresses_coverage(self):
        """Test that major exchanges are covered."""
        exchange_names = [name.lower() for name in KNOWN_EXCHANGE_ADDRESSES.values()]

        # Check for major exchanges
        assert any('binance' in name for name in exchange_names)
        assert any('coinbase' in name for name in exchange_names)
        assert any('kraken' in name for name in exchange_names)

    def test_api_limits_defined(self):
        """Test that API limits are defined."""
        assert 'coingecko_free' in API_LIMITS
        assert 'etherscan_free' in API_LIMITS
        assert 'infura_free' in API_LIMITS

    def test_api_limits_structure(self):
        """Test API limits have correct structure."""
        for provider, limits in API_LIMITS.items():
            assert isinstance(limits, dict)
            assert len(limits) > 0


class TestGetSettings:
    """Test global settings instance getter."""

    def test_get_settings_singleton(self):
        """Test that get_settings returns same instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_get_settings_creates_instance(self):
        """Test that get_settings creates instance on first call."""
        settings = get_settings()

        assert isinstance(settings, Settings)
        assert hasattr(settings, 'DEFAULT_NETWORK')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
