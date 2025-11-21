"""
Unit tests for TelegramNotifier
================================

Tests Telegram notification system and whale-specific alerts.
"""

import pytest
import asyncio
from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.notifications.telegram_notifier import TelegramNotifier, AlertManager, MessageFormatter


class TestTelegramNotifierInit:
    """Test TelegramNotifier initialization."""

    def test_init_with_env_vars(self, monkeypatch):
        """Test initialization with environment variables."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")

        notifier = TelegramNotifier()

        assert notifier.bot_token == "test_token"
        assert notifier.chat_id == "123456789"
        assert "test_token" in notifier.base_url

    def test_init_without_env_vars(self, monkeypatch):
        """Test initialization without environment variables."""
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

        notifier = TelegramNotifier()

        assert notifier.bot_token is None or notifier.bot_token == ""
        assert notifier.chat_id is None or notifier.chat_id == ""


class TestWhaleAlerts:
    """Test whale-specific alert methods."""

    @pytest.mark.asyncio
    async def test_send_whale_direct_transfer_alert(self, monkeypatch):
        """Test direct whale → exchange alert."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")

        notifier = TelegramNotifier()

        # Mock send_message
        notifier.send_message = AsyncMock(return_value=True)

        whale_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        tx_data = {
            'value_usd': 500000,
            'hash': '0xabc123'
        }
        destination_info = {
            'name': 'Binance Hot Wallet',
            'type': 'exchange'
        }

        result = await notifier.send_whale_direct_transfer_alert(
            whale_address,
            tx_data,
            destination_info,
            current_price=3500.0
        )

        assert result == True
        assert notifier.send_message.called
        call_args = notifier.send_message.call_args[0][0]  # Get message text
        assert "WHALE → EXCHANGE DIRECT" in call_args
        assert "Binance Hot Wallet" in call_args
        assert "$500,000" in call_args

    @pytest.mark.asyncio
    async def test_send_whale_onehop_alert(self, monkeypatch):
        """Test one-hop detection alert."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")

        notifier = TelegramNotifier()
        notifier.send_message = AsyncMock(return_value=True)

        whale_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        whale_tx = {
            'value_usd': 2000000,
            'hash': '0xdef456'
        }
        intermediate_address = "0x123456789abcdef"
        onehop_result = {
            'exchange_name': 'Coinbase',
            'time_delay_minutes': 15
        }

        result = await notifier.send_whale_onehop_alert(
            whale_address,
            whale_tx,
            intermediate_address,
            onehop_result,
            current_price=3500.0
        )

        assert result == True
        assert notifier.send_message.called
        call_args = notifier.send_message.call_args[0][0]
        assert "WHALE → UNKNOWN → EXCHANGE" in call_args
        assert "Coinbase" in call_args
        assert "$2,000,000" in call_args
        assert "15" in call_args  # time delay

    @pytest.mark.asyncio
    async def test_send_anomaly_alert(self, monkeypatch):
        """Test statistical anomaly alert."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")

        notifier = TelegramNotifier()
        notifier.send_message = AsyncMock(return_value=True)

        whale_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        tx_data = {
            'value_usd': 5000000
        }
        anomaly_info = {
            'average_amount': 1000000,
            'threshold': 1300000
        }

        result = await notifier.send_anomaly_alert(
            whale_address,
            tx_data,
            anomaly_info
        )

        assert result == True
        assert notifier.send_message.called
        call_args = notifier.send_message.call_args[0][0]
        assert "STATISTICAL ANOMALY DETECTED" in call_args
        assert "$5,000,000" in call_args
        assert "$1,000,000" in call_args  # average
        assert "5.0x" in call_args  # multiplier


class TestMessageFormatter:
    """Test message formatting utilities."""

    def test_format_currency_millions(self):
        """Test currency formatting for millions."""
        assert MessageFormatter.format_currency(2500000) == "$2.50M"
        assert MessageFormatter.format_currency(1000000) == "$1.00M"

    def test_format_currency_thousands(self):
        """Test currency formatting for thousands."""
        assert MessageFormatter.format_currency(50000) == "$50.0K"
        assert MessageFormatter.format_currency(1500) == "$1.5K"

    def test_format_currency_small(self):
        """Test currency formatting for small amounts."""
        assert MessageFormatter.format_currency(500) == "$500.00"
        assert MessageFormatter.format_currency(99.99) == "$99.99"

    def test_format_percentage(self):
        """Test percentage formatting."""
        assert "5.00%" in MessageFormatter.format_percentage(0.05)
        assert "0.125%" in MessageFormatter.format_percentage(0.00125)

    def test_format_change(self):
        """Test change formatting with arrows."""
        # Increase
        change_up = MessageFormatter.format_change(110, 100)
        assert "📈" in change_up
        assert "10.00%" in change_up

        # Decrease
        change_down = MessageFormatter.format_change(90, 100)
        assert "📉" in change_down
        assert "-10.00%" in change_down

        # No change
        change_none = MessageFormatter.format_change(100, 100)
        assert "➡️" in change_none


class TestAlertManager:
    """Test AlertManager functionality."""

    def test_alert_manager_init(self):
        """Test AlertManager initialization."""
        notifier = TelegramNotifier()
        manager = AlertManager(notifier)

        assert manager.notifier is notifier
        assert isinstance(manager.last_alerts, dict)

    def test_mark_alert_sent(self):
        """Test marking alert as sent."""
        notifier = TelegramNotifier()
        manager = AlertManager(notifier)

        alert_key = "test_alert_123"
        manager._mark_alert_sent(alert_key)

        assert alert_key in manager.last_alerts

    def test_was_alert_sent_recently(self):
        """Test checking if alert was sent recently."""
        notifier = TelegramNotifier()
        manager = AlertManager(notifier)

        alert_key = "test_alert_456"

        # Not sent yet
        assert manager._was_alert_sent_recently(alert_key) == False

        # Mark as sent
        manager._mark_alert_sent(alert_key)

        # Should be marked as sent recently
        assert manager._was_alert_sent_recently(alert_key, cooldown_minutes=60) == True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
