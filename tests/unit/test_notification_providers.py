"""
Unit Tests for Notification Providers

Tests NotificationProvider abstraction and implementations.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.abstractions.notification_provider import NotificationProvider
from src.providers.telegram_provider import TelegramProvider
from src.providers.multi_channel_notifier import MultiChannelNotifier


class TestNotificationProviderInterface:
    """Test that NotificationProvider is a proper abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """NotificationProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            NotificationProvider()

    def test_abstract_methods_exist(self):
        """All abstract methods are defined."""
        abstract_methods = [
            'send_message',
            'send_whale_direct_transfer_alert',
            'send_whale_onehop_alert',
            'send_statistical_alert',
            'send_daily_report',
            'test_connection',
            'provider_name',
            'is_configured'
        ]

        for method in abstract_methods:
            assert hasattr(NotificationProvider, method)


class TestTelegramProvider:
    """Test TelegramProvider implementation."""

    def test_initialization_with_env_vars(self):
        """TelegramProvider initializes with environment variables."""
        with patch.dict('os.environ', {
            'TELEGRAM_BOT_TOKEN': 'test_token',
            'TELEGRAM_CHAT_ID': '12345'
        }):
            provider = TelegramProvider()
            assert provider.bot_token == 'test_token'
            assert provider.chat_id == '12345'
            assert provider.provider_name == 'telegram'

    def test_initialization_with_parameters(self):
        """TelegramProvider can be initialized with explicit parameters."""
        provider = TelegramProvider(
            bot_token='custom_token',
            chat_id='67890'
        )
        assert provider.bot_token == 'custom_token'
        assert provider.chat_id == '67890'

    def test_is_configured_true(self):
        """is_configured returns True when token and chat_id are set."""
        provider = TelegramProvider(
            bot_token='token',
            chat_id='123'
        )
        assert provider.is_configured is True

    def test_is_configured_false(self):
        """is_configured returns False when credentials missing."""
        provider = TelegramProvider(
            bot_token=None,
            chat_id=None
        )
        assert provider.is_configured is False

    @pytest.mark.asyncio
    async def test_send_message_not_configured(self):
        """send_message returns False when not configured."""
        provider = TelegramProvider(bot_token=None, chat_id=None)
        result = await provider.send_message("Test")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """send_message sends message successfully."""
        provider = TelegramProvider(
            bot_token='test_token',
            chat_id='123'
        )

        # Mock aiohttp
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={'ok': True})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        mock_session.post = Mock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await provider.send_message("Test message")
            assert result is True

    @pytest.mark.asyncio
    async def test_send_whale_onehop_alert(self):
        """send_whale_onehop_alert formats and sends alert."""
        provider = TelegramProvider(
            bot_token='test_token',
            chat_id='123'
        )

        # Mock successful send
        provider.send_message = AsyncMock(return_value=True)

        result = await provider.send_whale_onehop_alert(
            whale_address='0x1234567890abcdef1234567890abcdef12345678',
            intermediate_address='0xabcdef1234567890abcdef1234567890abcdef12',
            exchange_address='0xexchange123456789012345678901234567890',
            whale_amount_eth=100.5,
            exchange_amount_eth=100.0,
            whale_tx_hash='0xwhaletx123',
            exchange_tx_hash='0xexchangetx123',
            confidence=85,
            signal_scores={
                'time_correlation': 90,
                'gas_correlation': 80,
                'nonce_correlation': 85
            },
            additional_data={
                'exchange_name': 'Binance',
                'whale_amount_usd': 150000,
                'time_delay_minutes': 5
            }
        )

        assert result is True
        provider.send_message.assert_called_once()

        # Check message content
        call_args = provider.send_message.call_args[0][0]
        assert '0x12345678' in call_args  # Whale address truncated
        assert '85%' in call_args  # Confidence
        assert 'Binance' in call_args  # Exchange name


class TestMultiChannelNotifier:
    """Test MultiChannelNotifier implementation."""

    def test_initialization(self):
        """MultiChannelNotifier initializes with providers list."""
        provider1 = Mock(spec=NotificationProvider)
        provider1.provider_name = 'telegram'
        provider2 = Mock(spec=NotificationProvider)
        provider2.provider_name = 'discord'

        notifier = MultiChannelNotifier([provider1, provider2])

        assert len(notifier.providers) == 2
        assert notifier.provider_name == 'multi_channel[telegram,discord]'

    def test_is_configured_true(self):
        """is_configured returns True if at least one provider is configured."""
        provider1 = Mock(spec=NotificationProvider)
        provider1.is_configured = True
        provider2 = Mock(spec=NotificationProvider)
        provider2.is_configured = False

        notifier = MultiChannelNotifier([provider1, provider2])
        assert notifier.is_configured is True

    def test_is_configured_false(self):
        """is_configured returns False if no providers configured."""
        provider1 = Mock(spec=NotificationProvider)
        provider1.is_configured = False
        provider2 = Mock(spec=NotificationProvider)
        provider2.is_configured = False

        notifier = MultiChannelNotifier([provider1, provider2])
        assert notifier.is_configured is False

    @pytest.mark.asyncio
    async def test_test_connection_all_success(self):
        """test_connection succeeds if at least one provider connects."""
        provider1 = Mock(spec=NotificationProvider)
        provider1.test_connection = AsyncMock(return_value=True)
        provider1.provider_name = 'telegram'

        provider2 = Mock(spec=NotificationProvider)
        provider2.test_connection = AsyncMock(return_value=True)
        provider2.provider_name = 'discord'

        notifier = MultiChannelNotifier([provider1, provider2])
        result = await notifier.test_connection()

        assert result is True
        assert len(notifier._active_providers) == 2

    @pytest.mark.asyncio
    async def test_test_connection_partial_success(self):
        """test_connection succeeds even if some providers fail."""
        provider1 = Mock(spec=NotificationProvider)
        provider1.test_connection = AsyncMock(return_value=True)
        provider1.provider_name = 'telegram'
        provider1.is_configured = True

        provider2 = Mock(spec=NotificationProvider)
        provider2.test_connection = AsyncMock(return_value=False)
        provider2.provider_name = 'discord'
        provider2.is_configured = True

        notifier = MultiChannelNotifier([provider1, provider2])
        result = await notifier.test_connection()

        assert result is True
        assert len(notifier._active_providers) == 1
        assert len(notifier._failed_providers) == 1

    @pytest.mark.asyncio
    async def test_send_message_to_all_providers(self):
        """send_message sends to all active providers."""
        provider1 = Mock(spec=NotificationProvider)
        provider1.send_message = AsyncMock(return_value=True)
        provider1.is_configured = True
        provider1.provider_name = 'telegram'

        provider2 = Mock(spec=NotificationProvider)
        provider2.send_message = AsyncMock(return_value=True)
        provider2.is_configured = True
        provider2.provider_name = 'discord'

        notifier = MultiChannelNotifier([provider1, provider2])
        notifier._active_providers = [provider1, provider2]

        result = await notifier.send_message("Test message")

        assert result is True
        provider1.send_message.assert_called_once_with("Test message", None)
        provider2.send_message.assert_called_once_with("Test message", None)

    @pytest.mark.asyncio
    async def test_send_message_partial_failure(self):
        """send_message succeeds if at least one provider succeeds."""
        provider1 = Mock(spec=NotificationProvider)
        provider1.send_message = AsyncMock(return_value=True)
        provider1.is_configured = True
        provider1.provider_name = 'telegram'

        provider2 = Mock(spec=NotificationProvider)
        provider2.send_message = AsyncMock(return_value=False)
        provider2.is_configured = True
        provider2.provider_name = 'discord'

        notifier = MultiChannelNotifier([provider1, provider2])
        notifier._active_providers = [provider1, provider2]

        result = await notifier.send_message("Test message")

        assert result is True  # At least one succeeded

    def test_get_provider_status(self):
        """get_provider_status returns status information."""
        provider1 = Mock(spec=NotificationProvider)
        provider1.provider_name = 'telegram'
        provider1.is_configured = True

        provider2 = Mock(spec=NotificationProvider)
        provider2.provider_name = 'discord'
        provider2.is_configured = False

        notifier = MultiChannelNotifier([provider1, provider2])
        notifier._active_providers = [provider1]
        notifier._failed_providers = [provider2]

        status = notifier.get_provider_status()

        assert status['total_providers'] == 2
        assert status['active_providers'] == 1
        assert status['failed_providers'] == 1
        assert len(status['providers']) == 2


class TestNotificationIntegration:
    """Integration tests for notification system."""

    @pytest.mark.asyncio
    async def test_telegram_provider_full_flow(self):
        """Test complete flow with TelegramProvider."""
        provider = TelegramProvider(
            bot_token='test_token',
            chat_id='123'
        )

        # Mock HTTP requests
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={'ok': True})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        mock_session.post = Mock(return_value=mock_response)
        mock_session.get = Mock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch('aiohttp.ClientSession', return_value=mock_session):
            # Test connection
            assert await provider.test_connection() is True

            # Send simple message
            assert await provider.send_message("Test") is True

            # Send whale alert
            assert await provider.send_whale_onehop_alert(
                whale_address='0x' + '1' * 40,
                intermediate_address='0x' + '2' * 40,
                exchange_address='0x' + '3' * 40,
                whale_amount_eth=100,
                exchange_amount_eth=99,
                whale_tx_hash='0x' + 'a' * 64,
                exchange_tx_hash='0x' + 'b' * 64,
                confidence=90,
                signal_scores={}
            ) is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
