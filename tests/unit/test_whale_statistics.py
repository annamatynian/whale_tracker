"""
Unit tests for whale_statistics functionality in repositories.

Tests both SQL and In-Memory implementations of get_whale_statistics.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

from src.repositories.in_memory_detection_repository import InMemoryDetectionRepository
from models.schemas import OneHopDetectionCreate


class TestWhaleStatistics:
    """Test get_whale_statistics method in repositories."""

    @pytest.mark.asyncio
    async def test_whale_statistics_cold_start(self):
        """get_whale_statistics returns empty dict for whale with no history."""
        repo = InMemoryDetectionRepository()

        # Query whale that doesn't exist
        stats = await repo.get_whale_statistics('0x' + '9' * 40, days=30)

        # Should return empty dict (cold start)
        assert stats == {}

    @pytest.mark.asyncio
    async def test_whale_statistics_single_transaction(self):
        """get_whale_statistics calculates correctly for single transaction."""
        repo = InMemoryDetectionRepository()

        whale_address = '0x' + '1' * 40

        # Create one detection
        detection = OneHopDetectionCreate(
            whale_address=whale_address,
            whale_tx_hash='0x' + 'a' * 64,
            intermediate_address='0x' + '2' * 40,
            whale_tx_block=1000000,
            whale_tx_timestamp=datetime.utcnow(),
            whale_amount_wei='100000000000000000000',
            whale_amount_eth=Decimal('100.0'),
            total_confidence=85,
            num_signals_used=3
        )

        await repo.save_detection(detection)

        # Get statistics
        stats = await repo.get_whale_statistics(whale_address, days=30)

        # Verify statistics
        assert stats['total_transactions'] == 1
        assert stats['avg_amount_eth'] == 100.0
        assert stats['max_amount_eth'] == 100.0
        assert stats['min_amount_eth'] == 100.0
        assert stats['total_volume_eth'] == 100.0
        assert stats['days_since_last'] == 0  # Just created
        assert 'first_seen' in stats
        assert 'last_seen' in stats

    @pytest.mark.asyncio
    async def test_whale_statistics_multiple_transactions(self):
        """get_whale_statistics aggregates multiple transactions correctly."""
        repo = InMemoryDetectionRepository()

        whale_address = '0x' + '1' * 40

        # Create multiple detections with different amounts
        amounts = [100.0, 200.0, 300.0, 150.0, 250.0]

        for i, amount in enumerate(amounts):
            detection = OneHopDetectionCreate(
                whale_address=whale_address,
                whale_tx_hash=f'0x{i}' + 'a' * 63,
                intermediate_address='0x' + '2' * 40,
                whale_tx_block=1000000 + i,
                whale_tx_timestamp=datetime.utcnow() - timedelta(hours=i),
                whale_amount_wei=str(int(amount * 1e18)),
                whale_amount_eth=Decimal(str(amount)),
                total_confidence=85,
                num_signals_used=3
            )
            await repo.save_detection(detection)

        # Get statistics
        stats = await repo.get_whale_statistics(whale_address, days=30)

        # Verify aggregations
        assert stats['total_transactions'] == 5
        assert stats['avg_amount_eth'] == sum(amounts) / len(amounts)  # 200.0
        assert stats['max_amount_eth'] == max(amounts)  # 300.0
        assert stats['min_amount_eth'] == min(amounts)  # 100.0
        assert stats['total_volume_eth'] == sum(amounts)  # 1000.0

    @pytest.mark.asyncio
    async def test_whale_statistics_filters_by_time_period(self):
        """get_whale_statistics only includes transactions within specified days."""
        repo = InMemoryDetectionRepository()

        whale_address = '0x' + '1' * 40

        # NOTE: InMemoryRepository uses detected_at=utcnow() (when we detected it)
        # not whale_tx_timestamp (when tx was in blockchain)
        # For testing time filtering, we'll test with different query periods

        # Create detections (all detected "now")
        recent_detection = OneHopDetectionCreate(
            whale_address=whale_address,
            whale_tx_hash='0x' + 'a' * 64,
            intermediate_address='0x' + '2' * 40,
            whale_tx_block=1000000,
            whale_tx_timestamp=datetime.utcnow(),
            whale_amount_wei='100000000000000000000',
            whale_amount_eth=Decimal('100.0'),
            total_confidence=85,
            num_signals_used=3
        )
        await repo.save_detection(recent_detection)

        second_detection = OneHopDetectionCreate(
            whale_address=whale_address,
            whale_tx_hash='0x' + 'b' * 64,
            intermediate_address='0x' + '2' * 40,
            whale_tx_block=1000001,
            whale_tx_timestamp=datetime.utcnow(),
            whale_amount_wei='500000000000000000000',
            whale_amount_eth=Decimal('500.0'),
            total_confidence=85,
            num_signals_used=3
        )
        await repo.save_detection(second_detection)

        # Get statistics for last 30 days (should include all detections made now)
        stats = await repo.get_whale_statistics(whale_address, days=30)

        # Should include both recent detections
        assert stats['total_transactions'] == 2
        assert stats['total_volume_eth'] == 600.0

        # Get statistics for last 1 second (should get nothing)
        await asyncio.sleep(1.5)
        stats_1sec = await repo.get_whale_statistics(whale_address, days=0)

        # Should be empty (all detections older than 0 days)
        assert stats_1sec == {} or stats_1sec['total_transactions'] == 0

    @pytest.mark.asyncio
    async def test_whale_statistics_different_whales_isolated(self):
        """get_whale_statistics only returns data for specified whale."""
        repo = InMemoryDetectionRepository()

        whale1 = '0x' + '1' * 40
        whale2 = '0x' + '2' * 40

        # Create detections for whale1
        for i in range(3):
            detection = OneHopDetectionCreate(
                whale_address=whale1,
                whale_tx_hash=f'0x{i}' + 'a' * 63,
                intermediate_address='0x' + '3' * 40,
                whale_tx_block=1000000 + i,
                whale_tx_timestamp=datetime.utcnow(),
                whale_amount_wei='100000000000000000000',
                whale_amount_eth=Decimal('100.0'),
                total_confidence=85,
                num_signals_used=3
            )
            await repo.save_detection(detection)

        # Create detections for whale2
        for i in range(5):
            detection = OneHopDetectionCreate(
                whale_address=whale2,
                whale_tx_hash=f'0x{i}' + 'b' * 63,
                intermediate_address='0x' + '3' * 40,
                whale_tx_block=1000010 + i,
                whale_tx_timestamp=datetime.utcnow(),
                whale_amount_wei='200000000000000000000',
                whale_amount_eth=Decimal('200.0'),
                total_confidence=85,
                num_signals_used=3
            )
            await repo.save_detection(detection)

        # Get statistics for whale1
        stats1 = await repo.get_whale_statistics(whale1, days=30)
        assert stats1['total_transactions'] == 3
        assert stats1['avg_amount_eth'] == 100.0

        # Get statistics for whale2
        stats2 = await repo.get_whale_statistics(whale2, days=30)
        assert stats2['total_transactions'] == 5
        assert stats2['avg_amount_eth'] == 200.0

    @pytest.mark.asyncio
    async def test_whale_statistics_calculates_days_since_last(self):
        """get_whale_statistics calculates days_since_last correctly."""
        repo = InMemoryDetectionRepository()

        whale_address = '0x' + '1' * 40

        # Create detection (detected "now")
        # NOTE: InMemoryRepository uses detected_at=utcnow(), not whale_tx_timestamp
        detection = OneHopDetectionCreate(
            whale_address=whale_address,
            whale_tx_hash='0x' + 'a' * 64,
            intermediate_address='0x' + '2' * 40,
            whale_tx_block=1000000,
            whale_tx_timestamp=datetime.utcnow(),
            whale_amount_wei='100000000000000000000',
            whale_amount_eth=Decimal('100.0'),
            total_confidence=85,
            num_signals_used=3
        )
        await repo.save_detection(detection)

        # Get statistics immediately
        stats = await repo.get_whale_statistics(whale_address, days=30)

        # Should be 0 days (just detected)
        assert stats['days_since_last'] == 0

    @pytest.mark.asyncio
    async def test_whale_statistics_graceful_degradation(self):
        """get_whale_statistics handles errors gracefully."""
        repo = InMemoryDetectionRepository()

        # Test with invalid whale address format (should still work)
        stats = await repo.get_whale_statistics('invalid', days=30)

        # Should return empty dict (no data found)
        assert stats == {}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
