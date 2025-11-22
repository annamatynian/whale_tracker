"""
Unit Tests for Cooldown Storage

Tests CooldownStorage abstraction and implementations.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.abstractions.cooldown_storage import CooldownStorage
from src.storages.in_memory_cooldown import InMemoryCooldownStorage


class TestCooldownStorageInterface:
    """Test that CooldownStorage is a proper abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """CooldownStorage cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CooldownStorage()

    def test_abstract_methods_exist(self):
        """All abstract methods are defined."""
        abstract_methods = [
            'was_sent_recently',
            'mark_sent',
            'get_last_sent_time',
            'clear_alert',
            'clear_all',
            'get_all_alerts',
            'cleanup_expired',
            'test_connection',
            'get_stats',
            'storage_type',
            'is_distributed'
        ]

        for method in abstract_methods:
            assert hasattr(CooldownStorage, method)


class TestInMemoryCooldownStorage:
    """Test InMemoryCooldownStorage implementation."""

    def test_initialization(self):
        """InMemoryCooldownStorage initializes correctly."""
        storage = InMemoryCooldownStorage()
        assert storage.storage_type == 'memory'
        assert storage.is_distributed is False

    @pytest.mark.asyncio
    async def test_test_connection_always_true(self):
        """test_connection always returns True for in-memory."""
        storage = InMemoryCooldownStorage()
        assert await storage.test_connection() is True

    @pytest.mark.asyncio
    async def test_mark_sent_and_get_last_sent_time(self):
        """mark_sent stores timestamp and get_last_sent_time retrieves it."""
        storage = InMemoryCooldownStorage()
        alert_key = 'test_alert'

        before = datetime.utcnow()
        await storage.mark_sent(alert_key)
        after = datetime.utcnow()

        last_sent = await storage.get_last_sent_time(alert_key)

        assert last_sent is not None
        assert before <= last_sent <= after

    @pytest.mark.asyncio
    async def test_mark_sent_with_custom_timestamp(self):
        """mark_sent accepts custom timestamp."""
        storage = InMemoryCooldownStorage()
        alert_key = 'test_alert'
        custom_time = datetime(2024, 1, 1, 12, 0, 0)

        await storage.mark_sent(alert_key, custom_time)

        last_sent = await storage.get_last_sent_time(alert_key)
        assert last_sent == custom_time

    @pytest.mark.asyncio
    async def test_was_sent_recently_false_when_never_sent(self):
        """was_sent_recently returns False for never-sent alert."""
        storage = InMemoryCooldownStorage()

        result = await storage.was_sent_recently('new_alert', 3600)
        assert result is False

    @pytest.mark.asyncio
    async def test_was_sent_recently_true_within_cooldown(self):
        """was_sent_recently returns True when within cooldown period."""
        storage = InMemoryCooldownStorage()
        alert_key = 'test_alert'

        await storage.mark_sent(alert_key)

        # Check immediately - should be in cooldown
        result = await storage.was_sent_recently(alert_key, 3600)
        assert result is True

    @pytest.mark.asyncio
    async def test_was_sent_recently_false_after_cooldown(self):
        """was_sent_recently returns False after cooldown expires."""
        storage = InMemoryCooldownStorage()
        alert_key = 'test_alert'

        # Mark as sent 2 hours ago
        old_time = datetime.utcnow() - timedelta(hours=2)
        await storage.mark_sent(alert_key, old_time)

        # Check with 1 hour cooldown - should NOT be in cooldown
        result = await storage.was_sent_recently(alert_key, 3600)  # 1 hour
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_alert(self):
        """clear_alert removes specific alert."""
        storage = InMemoryCooldownStorage()
        alert_key = 'test_alert'

        await storage.mark_sent(alert_key)
        assert await storage.get_last_sent_time(alert_key) is not None

        await storage.clear_alert(alert_key)
        assert await storage.get_last_sent_time(alert_key) is None

    @pytest.mark.asyncio
    async def test_clear_all(self):
        """clear_all removes all alerts."""
        storage = InMemoryCooldownStorage()

        await storage.mark_sent('alert1')
        await storage.mark_sent('alert2')
        await storage.mark_sent('alert3')

        alerts = await storage.get_all_alerts()
        assert len(alerts) == 3

        await storage.clear_all()

        alerts = await storage.get_all_alerts()
        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_get_all_alerts(self):
        """get_all_alerts returns all stored alerts."""
        storage = InMemoryCooldownStorage()

        time1 = datetime(2024, 1, 1, 12, 0, 0)
        time2 = datetime(2024, 1, 1, 13, 0, 0)

        await storage.mark_sent('alert1', time1)
        await storage.mark_sent('alert2', time2)

        alerts = await storage.get_all_alerts()

        assert len(alerts) == 2
        assert 'alert1' in alerts
        assert 'alert2' in alerts
        assert alerts['alert1'] == time1
        assert alerts['alert2'] == time2

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """cleanup_expired removes old entries."""
        storage = InMemoryCooldownStorage()

        # Add recent alert
        await storage.mark_sent('recent_alert')

        # Add old alerts
        old_time = datetime.utcnow() - timedelta(hours=25)
        await storage.mark_sent('old_alert1', old_time)
        await storage.mark_sent('old_alert2', old_time)

        # Cleanup entries older than 24 hours
        removed = await storage.cleanup_expired(24 * 3600)

        assert removed == 2

        alerts = await storage.get_all_alerts()
        assert len(alerts) == 1
        assert 'recent_alert' in alerts
        assert 'old_alert1' not in alerts

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """get_stats returns storage statistics."""
        storage = InMemoryCooldownStorage()

        # Add some alerts
        await storage.mark_sent('alert1')
        await storage.mark_sent('alert2')

        # Add old alert
        old_time = datetime.utcnow() - timedelta(hours=2)
        await storage.mark_sent('old_alert', old_time)

        # Check stats
        await storage.was_sent_recently('alert1', 3600)
        await storage.was_sent_recently('alert2', 3600)

        stats = await storage.get_stats()

        assert stats['storage_type'] == 'memory'
        assert stats['total_alerts'] == 3
        assert stats['is_distributed'] is False
        assert 'active_cooldowns' in stats


class TestCooldownStorageEdgeCases:
    """Test edge cases for cooldown storage."""

    @pytest.mark.asyncio
    async def test_multiple_mark_sent_updates_timestamp(self):
        """Marking sent multiple times updates the timestamp."""
        storage = InMemoryCooldownStorage()
        alert_key = 'test_alert'

        time1 = datetime(2024, 1, 1, 12, 0, 0)
        await storage.mark_sent(alert_key, time1)

        first_time = await storage.get_last_sent_time(alert_key)
        assert first_time == time1

        time2 = datetime(2024, 1, 1, 13, 0, 0)
        await storage.mark_sent(alert_key, time2)

        second_time = await storage.get_last_sent_time(alert_key)
        assert second_time == time2
        assert second_time != first_time

    @pytest.mark.asyncio
    async def test_clear_nonexistent_alert_no_error(self):
        """Clearing nonexistent alert doesn't raise error."""
        storage = InMemoryCooldownStorage()

        # Should not raise exception
        await storage.clear_alert('nonexistent_alert')

    @pytest.mark.asyncio
    async def test_cooldown_zero_seconds(self):
        """Cooldown with 0 seconds always returns False."""
        storage = InMemoryCooldownStorage()
        alert_key = 'test_alert'

        await storage.mark_sent(alert_key)

        # Even just sent, 0 second cooldown means always expired
        result = await storage.was_sent_recently(alert_key, 0)
        assert result is False

    @pytest.mark.asyncio
    async def test_cooldown_very_large_value(self):
        """Cooldown with very large value keeps alert in cooldown."""
        storage = InMemoryCooldownStorage()
        alert_key = 'test_alert'

        old_time = datetime.utcnow() - timedelta(days=365)
        await storage.mark_sent(alert_key, old_time)

        # 10 year cooldown - should still be in cooldown
        result = await storage.was_sent_recently(alert_key, 10 * 365 * 24 * 3600)
        assert result is True

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Storage handles concurrent operations correctly."""
        storage = InMemoryCooldownStorage()

        # Create multiple concurrent mark_sent operations
        tasks = [
            storage.mark_sent(f'alert_{i}')
            for i in range(100)
        ]

        await asyncio.gather(*tasks)

        alerts = await storage.get_all_alerts()
        assert len(alerts) == 100


class TestCooldownStorageIntegration:
    """Integration tests for cooldown storage."""

    @pytest.mark.asyncio
    async def test_typical_alert_flow(self):
        """Test typical alert cooldown flow."""
        storage = InMemoryCooldownStorage()
        alert_key = 'whale_0x123_onehop'
        cooldown_seconds = 3600  # 1 hour

        # First alert - should send
        is_recent = await storage.was_sent_recently(alert_key, cooldown_seconds)
        assert is_recent is False

        # Mark as sent
        await storage.mark_sent(alert_key)

        # Try to send again immediately - should be blocked
        is_recent = await storage.was_sent_recently(alert_key, cooldown_seconds)
        assert is_recent is True

        # Simulate time passing (1 hour + 1 second)
        old_time = datetime.utcnow() - timedelta(seconds=cooldown_seconds + 1)
        await storage.mark_sent(alert_key, old_time)

        # Should be able to send again
        is_recent = await storage.was_sent_recently(alert_key, cooldown_seconds)
        assert is_recent is False

    @pytest.mark.asyncio
    async def test_different_alerts_independent(self):
        """Different alert keys are independent."""
        storage = InMemoryCooldownStorage()
        cooldown = 3600

        await storage.mark_sent('whale_1')
        await storage.mark_sent('whale_2')

        # Both should be in cooldown
        assert await storage.was_sent_recently('whale_1', cooldown) is True
        assert await storage.was_sent_recently('whale_2', cooldown) is True

        # Clear one
        await storage.clear_alert('whale_1')

        # Only whale_1 should be cleared
        assert await storage.was_sent_recently('whale_1', cooldown) is False
        assert await storage.was_sent_recently('whale_2', cooldown) is True

    @pytest.mark.asyncio
    async def test_periodic_cleanup(self):
        """Test periodic cleanup scenario."""
        storage = InMemoryCooldownStorage()

        # Simulate 24 hours of alerts
        for hour in range(24):
            timestamp = datetime.utcnow() - timedelta(hours=23 - hour)
            await storage.mark_sent(f'alert_hour_{hour}', timestamp)

        # All 24 alerts should exist
        alerts = await storage.get_all_alerts()
        assert len(alerts) == 24

        # Cleanup alerts older than 12 hours
        removed = await storage.cleanup_expired(12 * 3600)

        # Should remove approximately half
        assert removed >= 10

        remaining = await storage.get_all_alerts()
        assert len(remaining) < 24


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
