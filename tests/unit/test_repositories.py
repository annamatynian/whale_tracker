"""
Unit Tests for Detection Repositories

Tests DetectionRepository abstraction and implementations.
"""

import pytest
from datetime import datetime
from decimal import Decimal

from src.abstractions.detection_repository import DetectionRepository
from src.repositories.in_memory_detection_repository import InMemoryDetectionRepository
from models.schemas import (
    OneHopDetectionCreate,
    OneHopDetectionUpdate,
    OneHopDetectionFilter,
    IntermediateAddressCreate,
    IntermediateAddressFilter,
    TransactionCreate,
    WhaleAlertCreate
)


class TestDetectionRepositoryInterface:
    """Test that DetectionRepository is a proper abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """DetectionRepository cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DetectionRepository()

    def test_abstract_methods_exist(self):
        """All abstract methods are defined."""
        abstract_methods = [
            'save_detection',
            'get_detection',
            'get_detections',
            'update_detection',
            'mark_alert_sent',
            'delete_detection',
            'save_intermediate_address',
            'get_intermediate_address',
            'test_connection',
            'repository_type'
        ]

        for method in abstract_methods:
            assert hasattr(DetectionRepository, method)


class TestInMemoryDetectionRepository:
    """Test InMemoryDetectionRepository implementation."""

    def test_initialization(self):
        """Repository initializes correctly."""
        repo = InMemoryDetectionRepository()
        assert repo.repository_type == 'memory'

    @pytest.mark.asyncio
    async def test_test_connection_always_true(self):
        """test_connection always succeeds for in-memory."""
        repo = InMemoryDetectionRepository()
        assert await repo.test_connection() is True

    @pytest.mark.asyncio
    async def test_save_and_get_detection(self):
        """save_detection stores detection and get_detection retrieves it."""
        repo = InMemoryDetectionRepository()

        detection = OneHopDetectionCreate(
            whale_address='0x' + '1' * 40,
            whale_tx_hash='0x' + 'a' * 64,
            intermediate_address='0x' + '2' * 40,
            exchange_address='0x' + '3' * 40,
            whale_tx_block=1000000,
            whale_tx_timestamp=datetime.utcnow(),
            whale_amount_wei='100000000000000000000',
            whale_amount_eth=Decimal('100.0'),
            total_confidence=85,
            num_signals_used=3
        )

        detection_id = await repo.save_detection(detection)
        assert detection_id == 1

        retrieved = await repo.get_detection(detection_id)
        assert retrieved is not None
        assert retrieved.whale_address == detection.whale_address
        assert retrieved.total_confidence == 85
        assert retrieved.status == 'pending'

    @pytest.mark.asyncio
    async def test_save_multiple_detections_increments_id(self):
        """Saving multiple detections increments IDs."""
        repo = InMemoryDetectionRepository()

        detection1 = OneHopDetectionCreate(
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

        detection2 = OneHopDetectionCreate(
            whale_address='0x' + '4' * 40,
            whale_tx_hash='0x' + 'b' * 64,
            intermediate_address='0x' + '5' * 40,
            whale_tx_block=1000001,
            whale_tx_timestamp=datetime.utcnow(),
            whale_amount_wei='200000000000000000000',
            whale_amount_eth=Decimal('200.0'),
            total_confidence=90,
            num_signals_used=4
        )

        id1 = await repo.save_detection(detection1)
        id2 = await repo.save_detection(detection2)

        assert id1 == 1
        assert id2 == 2

    @pytest.mark.asyncio
    async def test_get_nonexistent_detection_returns_none(self):
        """Getting nonexistent detection returns None."""
        repo = InMemoryDetectionRepository()
        result = await repo.get_detection(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_detection(self):
        """update_detection modifies detection fields."""
        repo = InMemoryDetectionRepository()

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

        # Update status and notes
        update = OneHopDetectionUpdate(
            status='confirmed',
            notes='Verified manually'
        )

        success = await repo.update_detection(detection_id, update)
        assert success is True

        updated = await repo.get_detection(detection_id)
        assert updated.status == 'confirmed'
        assert updated.notes == 'Verified manually'

    @pytest.mark.asyncio
    async def test_update_nonexistent_detection_returns_false(self):
        """Updating nonexistent detection returns False."""
        repo = InMemoryDetectionRepository()

        update = OneHopDetectionUpdate(status='confirmed')
        success = await repo.update_detection(999, update)
        assert success is False

    @pytest.mark.asyncio
    async def test_mark_alert_sent(self):
        """mark_alert_sent updates alert fields."""
        repo = InMemoryDetectionRepository()

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

        before = datetime.utcnow()
        success = await repo.mark_alert_sent(detection_id)
        after = datetime.utcnow()

        assert success is True

        updated = await repo.get_detection(detection_id)
        assert updated.alert_sent is True
        assert updated.alert_sent_at is not None
        assert before <= updated.alert_sent_at <= after

    @pytest.mark.asyncio
    async def test_delete_detection(self):
        """delete_detection removes detection."""
        repo = InMemoryDetectionRepository()

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
        assert await repo.get_detection(detection_id) is not None

        success = await repo.delete_detection(detection_id)
        assert success is True

        assert await repo.get_detection(detection_id) is None

    @pytest.mark.asyncio
    async def test_get_detections_with_filters(self):
        """get_detections filters results correctly."""
        repo = InMemoryDetectionRepository()

        # Create detections with different properties
        detection1 = OneHopDetectionCreate(
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

        detection2 = OneHopDetectionCreate(
            whale_address='0x' + '4' * 40,
            whale_tx_hash='0x' + 'b' * 64,
            intermediate_address='0x' + '5' * 40,
            whale_tx_block=1000001,
            whale_tx_timestamp=datetime.utcnow(),
            whale_amount_wei='200000000000000000000',
            whale_amount_eth=Decimal('200.0'),
            total_confidence=95,
            num_signals_used=4
        )

        await repo.save_detection(detection1)
        await repo.save_detection(detection2)

        # Filter by min_confidence
        filters = OneHopDetectionFilter(min_confidence=90)
        results = await repo.get_detections(filters)

        assert len(results) == 1
        assert results[0].total_confidence == 95

    @pytest.mark.asyncio
    async def test_get_detections_pagination(self):
        """get_detections supports pagination."""
        repo = InMemoryDetectionRepository()

        # Create 10 detections
        for i in range(10):
            detection = OneHopDetectionCreate(
                whale_address=f'0x{i}' + '1' * 39,
                whale_tx_hash=f'0x{i}' + 'a' * 63,
                intermediate_address=f'0x{i}' + '2' * 39,
                whale_tx_block=1000000 + i,
                whale_tx_timestamp=datetime.utcnow(),
                whale_amount_wei='100000000000000000000',
                whale_amount_eth=Decimal('100.0'),
                total_confidence=80 + i,
                num_signals_used=3
            )
            await repo.save_detection(detection)

        # Get first page
        filters = OneHopDetectionFilter(limit=5, offset=0)
        page1 = await repo.get_detections(filters)
        assert len(page1) == 5

        # Get second page
        filters = OneHopDetectionFilter(limit=5, offset=5)
        page2 = await repo.get_detections(filters)
        assert len(page2) == 5

    @pytest.mark.asyncio
    async def test_save_intermediate_address(self):
        """save_intermediate_address stores address profile."""
        repo = InMemoryDetectionRepository()

        address_data = IntermediateAddressCreate(
            address='0x' + '1' * 40,
            profile_type='fresh_burner',
            overall_confidence=90,
            is_fresh=True,
            fresh_confidence=95,
            age_hours=Decimal('2.5')
        )

        address = await repo.save_intermediate_address(address_data)
        assert address == address_data.address

        retrieved = await repo.get_intermediate_address(address)
        assert retrieved is not None
        assert retrieved.profile_type == 'fresh_burner'
        assert retrieved.overall_confidence == 90

    @pytest.mark.asyncio
    async def test_increment_address_usage(self):
        """increment_address_usage increases usage count."""
        repo = InMemoryDetectionRepository()

        address_data = IntermediateAddressCreate(
            address='0x' + '1' * 40,
            profile_type='burner',
            overall_confidence=80
        )

        address = await repo.save_intermediate_address(address_data)

        # Initial times_used should be 1
        retrieved = await repo.get_intermediate_address(address)
        assert retrieved.times_used == 1

        # Increment usage
        await repo.increment_address_usage(address)

        # Should now be 2
        retrieved = await repo.get_intermediate_address(address)
        assert retrieved.times_used == 2

    @pytest.mark.asyncio
    async def test_save_and_get_transaction(self):
        """Transaction save and retrieval works."""
        repo = InMemoryDetectionRepository()

        tx = TransactionCreate(
            tx_hash='0x' + 'a' * 64,
            block_number=1000000,
            block_timestamp=datetime.utcnow(),
            from_address='0x' + '1' * 40,
            to_address='0x' + '2' * 40,
            value_wei='1000000000000000000',
            value_eth=Decimal('1.0'),
            nonce=5
        )

        tx_hash = await repo.save_transaction(tx)
        assert tx_hash == tx.tx_hash

        retrieved = await repo.get_transaction(tx_hash)
        assert retrieved is not None
        assert retrieved.from_address == tx.from_address

    @pytest.mark.asyncio
    async def test_transaction_exists(self):
        """transaction_exists checks correctly."""
        repo = InMemoryDetectionRepository()

        tx = TransactionCreate(
            tx_hash='0x' + 'a' * 64,
            block_number=1000000,
            block_timestamp=datetime.utcnow(),
            from_address='0x' + '1' * 40,
            to_address='0x' + '2' * 40,
            value_wei='1000000000000000000',
            value_eth=Decimal('1.0'),
            nonce=5
        )

        assert await repo.transaction_exists(tx.tx_hash) is False

        await repo.save_transaction(tx)

        assert await repo.transaction_exists(tx.tx_hash) is True

    @pytest.mark.asyncio
    async def test_get_detection_stats(self):
        """get_detection_stats calculates statistics."""
        repo = InMemoryDetectionRepository()

        # Create detections with various confidences
        for confidence in [70, 80, 85, 90, 95]:
            detection = OneHopDetectionCreate(
                whale_address=f'0x{confidence}' + '1' * 38,
                whale_tx_hash=f'0x{confidence}' + 'a' * 62,
                intermediate_address=f'0x{confidence}' + '2' * 38,
                whale_tx_block=1000000,
                whale_tx_timestamp=datetime.utcnow(),
                whale_amount_wei='100000000000000000000',
                whale_amount_eth=Decimal('100.0'),
                total_confidence=confidence,
                num_signals_used=3
            )
            await repo.save_detection(detection)

        stats = await repo.get_detection_stats()

        assert stats['total_detections'] == 5
        assert stats['avg_confidence'] == 84.0  # (70+80+85+90+95)/5
        assert stats['high_confidence_count'] == 3  # 85, 90, 95

    @pytest.mark.asyncio
    async def test_get_top_whales(self):
        """get_top_whales returns top addresses by volume."""
        repo = InMemoryDetectionRepository()

        # Whale 1: 300 ETH total (3 detections)
        for i in range(3):
            detection = OneHopDetectionCreate(
                whale_address='0x' + '1' * 40,
                whale_tx_hash=f'0xa{i}' + 'a' * 62,
                intermediate_address='0x' + '2' * 40,
                whale_tx_block=1000000 + i,
                whale_tx_timestamp=datetime.utcnow(),
                whale_amount_wei='100000000000000000000',
                whale_amount_eth=Decimal('100.0'),
                total_confidence=85,
                num_signals_used=3
            )
            await repo.save_detection(detection)

        # Whale 2: 500 ETH total (1 detection)
        detection = OneHopDetectionCreate(
            whale_address='0x' + '3' * 40,
            whale_tx_hash='0xb' + 'b' * 63,
            intermediate_address='0x' + '4' * 40,
            whale_tx_block=1000003,
            whale_tx_timestamp=datetime.utcnow(),
            whale_amount_wei='500000000000000000000',
            whale_amount_eth=Decimal('500.0'),
            total_confidence=90,
            num_signals_used=3
        )
        await repo.save_detection(detection)

        top_whales = await repo.get_top_whales(limit=10)

        assert len(top_whales) == 2
        # Whale 2 should be first (500 ETH)
        assert top_whales[0]['address'] == '0x' + '3' * 40
        assert top_whales[0]['volume_eth'] == 500.0
        # Whale 1 should be second (300 ETH)
        assert top_whales[1]['address'] == '0x' + '1' * 40
        assert top_whales[1]['volume_eth'] == 300.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
