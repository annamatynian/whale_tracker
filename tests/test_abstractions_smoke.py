"""
Smoke Tests for Abstractions

Quick tests to verify basic functionality of all abstractions.
Run this for fast validation that imports and basic operations work.
"""

import pytest
import asyncio
from datetime import datetime
from decimal import Decimal

# Import all abstractions
from src.abstractions import (
    NotificationProvider,
    RPCProvider,
    CooldownStorage,
    BlockchainDataProvider,
    DetectionRepository,
    PriceProvider
)

# Import concrete implementations
from src.providers import (
    TelegramProvider,
    MultiChannelNotifier,
    EtherscanProvider,
    CompositeDataProvider
)

from src.storages import (
    InMemoryCooldownStorage,
)

from src.repositories import (
    InMemoryDetectionRepository
)

from models.schemas import OneHopDetectionCreate


class TestAbstractionsImport:
    """Test that all abstractions can be imported."""

    def test_import_notification_provider(self):
        """NotificationProvider imports correctly."""
        assert NotificationProvider is not None

    def test_import_rpc_provider(self):
        """RPCProvider imports correctly."""
        assert RPCProvider is not None

    def test_import_cooldown_storage(self):
        """CooldownStorage imports correctly."""
        assert CooldownStorage is not None

    def test_import_blockchain_data_provider(self):
        """BlockchainDataProvider imports correctly."""
        assert BlockchainDataProvider is not None

    def test_import_detection_repository(self):
        """DetectionRepository imports correctly."""
        assert DetectionRepository is not None

    def test_import_price_provider(self):
        """PriceProvider imports correctly."""
        assert PriceProvider is not None


class TestProvidersImport:
    """Test that all providers can be imported."""

    def test_import_telegram_provider(self):
        """TelegramProvider imports correctly."""
        assert TelegramProvider is not None

    def test_import_multi_channel_notifier(self):
        """MultiChannelNotifier imports correctly."""
        assert MultiChannelNotifier is not None

    def test_import_etherscan_provider(self):
        """EtherscanProvider imports correctly."""
        assert EtherscanProvider is not None

    def test_import_composite_data_provider(self):
        """CompositeDataProvider imports correctly."""
        assert CompositeDataProvider is not None


class TestStoragesImport:
    """Test that all storages can be imported."""

    def test_import_in_memory_cooldown(self):
        """InMemoryCooldownStorage imports correctly."""
        assert InMemoryCooldownStorage is not None


class TestRepositoriesImport:
    """Test that all repositories can be imported."""

    def test_import_in_memory_repository(self):
        """InMemoryDetectionRepository imports correctly."""
        assert InMemoryDetectionRepository is not None


class TestBasicInstantiation:
    """Test that concrete implementations can be instantiated."""

    def test_telegram_provider_instantiation(self):
        """TelegramProvider can be instantiated."""
        provider = TelegramProvider(bot_token='test', chat_id='123')
        assert provider is not None
        assert provider.provider_name == 'telegram'

    def test_in_memory_cooldown_instantiation(self):
        """InMemoryCooldownStorage can be instantiated."""
        storage = InMemoryCooldownStorage()
        assert storage is not None
        assert storage.storage_type == 'memory'

    def test_in_memory_repository_instantiation(self):
        """InMemoryDetectionRepository can be instantiated."""
        repo = InMemoryDetectionRepository()
        assert repo is not None
        assert repo.repository_type == 'memory'

    def test_etherscan_provider_instantiation(self):
        """EtherscanProvider can be instantiated."""
        provider = EtherscanProvider(api_key='test', network='ethereum')
        assert provider is not None
        assert provider.provider_name == 'etherscan'

    def test_multi_channel_notifier_instantiation(self):
        """MultiChannelNotifier can be instantiated."""
        telegram = TelegramProvider(bot_token='test', chat_id='123')
        notifier = MultiChannelNotifier([telegram])
        assert notifier is not None


@pytest.mark.asyncio
class TestBasicOperations:
    """Test basic operations work without errors."""

    async def test_cooldown_storage_basic_flow(self):
        """CooldownStorage basic operations work."""
        storage = InMemoryCooldownStorage()

        # Test connection
        assert await storage.test_connection() is True

        # Mark sent
        await storage.mark_sent('test_alert')

        # Check recently sent
        is_recent = await storage.was_sent_recently('test_alert', 3600)
        assert is_recent is True

        # Get last sent time
        last_sent = await storage.get_last_sent_time('test_alert')
        assert last_sent is not None

        # Clear
        await storage.clear_alert('test_alert')
        assert await storage.get_last_sent_time('test_alert') is None

    async def test_repository_basic_flow(self):
        """DetectionRepository basic operations work."""
        repo = InMemoryDetectionRepository()

        # Test connection
        assert await repo.test_connection() is True

        # Save detection
        detection = OneHopDetectionCreate(
            whale_address='0x' + '1' * 40,
            whale_tx_hash='0x' + 'a' * 64,
            intermediate_address='0x' + '2' * 40,
            whale_tx_block=1000000,
            whale_tx_timestamp=datetime.utcnow(),
            whale_amount_wei='100000000000000000000',
            whale_amount_eth=Decimal('100.0'),
            total_confidence=85,
            num_signals_used=3
        )

        detection_id = await repo.save_detection(detection)
        assert detection_id == 1

        # Retrieve detection
        retrieved = await repo.get_detection(detection_id)
        assert retrieved is not None
        assert retrieved.whale_address == detection.whale_address

        # Mark alert sent
        success = await repo.mark_alert_sent(detection_id)
        assert success is True

    async def test_notification_provider_properties(self):
        """NotificationProvider properties work."""
        provider = TelegramProvider(bot_token='test', chat_id='123')

        assert provider.provider_name == 'telegram'
        assert provider.is_configured is True

        provider_no_config = TelegramProvider(bot_token=None, chat_id=None)
        assert provider_no_config.is_configured is False


class TestIntegrationSmoke:
    """Smoke test for integrated usage."""

    @pytest.mark.asyncio
    async def test_multi_channel_with_cooldown(self):
        """Multi-channel notifier with cooldown storage."""
        # Setup
        notifier = MultiChannelNotifier([
            TelegramProvider(bot_token='test1', chat_id='123'),
            TelegramProvider(bot_token='test2', chat_id='456')
        ])
        cooldown = InMemoryCooldownStorage()

        # Check cooldown
        alert_key = 'whale_0x123_onehop'
        if not await cooldown.was_sent_recently(alert_key, 3600):
            # Would send alert here
            await cooldown.mark_sent(alert_key)

        # Verify cooldown active
        assert await cooldown.was_sent_recently(alert_key, 3600) is True

    @pytest.mark.asyncio
    async def test_repository_with_cooldown(self):
        """Repository and cooldown storage integration."""
        repo = InMemoryDetectionRepository()
        cooldown = InMemoryCooldownStorage()

        # Save detection
        detection = OneHopDetectionCreate(
            whale_address='0x' + '1' * 40,
            whale_tx_hash='0x' + 'a' * 64,
            intermediate_address='0x' + '2' * 40,
            whale_tx_block=1000000,
            whale_tx_timestamp=datetime.utcnow(),
            whale_amount_wei='100000000000000000000',
            whale_amount_eth=Decimal('100.0'),
            total_confidence=85,
            num_signals_used=3
        )

        detection_id = await repo.save_detection(detection)

        # Check cooldown for this detection
        alert_key = f"detection_{detection_id}"
        if not await cooldown.was_sent_recently(alert_key, 3600):
            # Mark alert sent in both repo and cooldown
            await repo.mark_alert_sent(detection_id)
            await cooldown.mark_sent(alert_key)

        # Verify
        retrieved = await repo.get_detection(detection_id)
        assert retrieved.alert_sent is True

        is_recent = await cooldown.was_sent_recently(alert_key, 3600)
        assert is_recent is True


class TestFailureHandling:
    """Test that failures are handled gracefully."""

    @pytest.mark.asyncio
    async def test_notification_without_config(self):
        """Notification fails gracefully without config."""
        provider = TelegramProvider(bot_token=None, chat_id=None)

        # Should return False, not raise exception
        result = await provider.send_message("Test")
        assert result is False

    @pytest.mark.asyncio
    async def test_repository_nonexistent_detection(self):
        """Repository returns None for nonexistent detection."""
        repo = InMemoryDetectionRepository()

        detection = await repo.get_detection(999)
        assert detection is None

    @pytest.mark.asyncio
    async def test_cooldown_nonexistent_alert(self):
        """Cooldown returns False for never-sent alert."""
        storage = InMemoryCooldownStorage()

        is_recent = await storage.was_sent_recently('nonexistent', 3600)
        assert is_recent is False


def test_all_abstractions_exist():
    """Verify all 6 abstractions are implemented."""
    abstractions = [
        NotificationProvider,
        RPCProvider,
        CooldownStorage,
        BlockchainDataProvider,
        DetectionRepository,
        PriceProvider
    ]

    for abstraction in abstractions:
        assert abstraction is not None


def test_provider_status():
    """Test MultiChannelNotifier status reporting."""
    telegram = TelegramProvider(bot_token='test', chat_id='123')
    telegram2 = TelegramProvider(bot_token=None, chat_id=None)

    notifier = MultiChannelNotifier([telegram, telegram2])

    status = notifier.get_provider_status()

    assert status['total_providers'] == 2
    assert 'providers' in status


if __name__ == '__main__':
    # Run smoke tests
    pytest.main([__file__, '-v', '--tb=short'])
