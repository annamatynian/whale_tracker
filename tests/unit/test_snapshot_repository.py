"""
Unit Tests for SnapshotRepository

Tests snapshot storage and retrieval for historical balance tracking.

Run: pytest tests/unit/test_snapshot_repository.py -v
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

from src.repositories.snapshot_repository import SnapshotRepository
from src.schemas.snapshot_schemas import WhaleBalanceSnapshotCreate, SnapshotSummary
from models.database import WhaleBalanceSnapshot


@pytest.fixture
def mock_session():
    """Create mocked AsyncSession."""
    session = AsyncMock()
    session.add = Mock()  # Synchronous method
    session.add_all = Mock()  # Synchronous method
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    """Create SnapshotRepository with mocked session."""
    return SnapshotRepository(session=mock_session)


@pytest.fixture
def sample_snapshot():
    """Create sample snapshot data."""
    return WhaleBalanceSnapshotCreate(
        address="0x" + "a" * 40,
        balance_wei="1000000000000000000",  # 1 ETH
        balance_eth=Decimal("1.0"),
        block_number=19000000,
        snapshot_timestamp=datetime.now(timezone.utc),
        network="ethereum"
    )


@pytest.fixture
def sample_snapshots():
    """Create list of sample snapshots."""
    base_time = datetime.now(timezone.utc)
    return [
        WhaleBalanceSnapshotCreate(
            address=f"0x{'a' * 40}",
            balance_wei="1000000000000000000",
            balance_eth=Decimal("1.0"),
            block_number=19000000,
            snapshot_timestamp=base_time,
            network="ethereum"
        ),
        WhaleBalanceSnapshotCreate(
            address=f"0x{'b' * 40}",
            balance_wei="2000000000000000000",
            balance_eth=Decimal("2.0"),
            block_number=19000000,
            snapshot_timestamp=base_time,
            network="ethereum"
        ),
        WhaleBalanceSnapshotCreate(
            address=f"0x{'c' * 40}",
            balance_wei="3000000000000000000",
            balance_eth=Decimal("3.0"),
            block_number=19000000,
            snapshot_timestamp=base_time,
            network="ethereum"
        )
    ]


class TestSnapshotRepository:
    """Test SnapshotRepository functionality."""
    
    @pytest.mark.asyncio
    async def test_save_snapshot(self, repository, mock_session, sample_snapshot):
        """Test saving single snapshot."""
        # Execute
        result = await repository.save_snapshot(sample_snapshot)
        
        # Verify
        assert mock_session.add.called
        assert mock_session.commit.called
        assert mock_session.refresh.called
    
    @pytest.mark.asyncio
    async def test_save_snapshots_batch(self, repository, mock_session, sample_snapshots):
        """Test batch snapshot saving."""
        # Execute
        count = await repository.save_snapshots_batch(sample_snapshots)
        
        # Verify
        assert count == 3
        assert mock_session.add_all.called
        assert mock_session.commit.called
    
    @pytest.mark.asyncio
    async def test_save_snapshots_batch_empty(self, repository, mock_session):
        """Test batch save with empty list."""
        # Execute
        count = await repository.save_snapshots_batch([])
        
        # Verify
        assert count == 0
        assert not mock_session.add_all.called
    
    @pytest.mark.asyncio
    async def test_save_snapshots_batch_rollback_on_error(self, repository, mock_session, sample_snapshots):
        """Test rollback on batch save error."""
        # Setup: Make commit fail
        mock_session.commit.side_effect = Exception("Database error")
        
        # Execute & Verify
        with pytest.raises(Exception):
            await repository.save_snapshots_batch(sample_snapshots)
        
        assert mock_session.rollback.called
    
    @pytest.mark.asyncio
    async def test_get_snapshot_at_time_found(self, repository, mock_session):
        """Test finding snapshot within tolerance."""
        # Setup
        target_time = datetime.now(timezone.utc)
        mock_snapshot = Mock(spec=WhaleBalanceSnapshot)
        mock_snapshot.address = "0x" + "a" * 40
        mock_snapshot.balance_eth = Decimal("1.0")
        mock_snapshot.snapshot_timestamp = target_time
        
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_snapshot)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await repository.get_snapshot_at_time(
            address="0x" + "a" * 40,
            timestamp=target_time,
            tolerance_hours=1
        )
        
        # Verify
        assert result is not None
        assert result.address == mock_snapshot.address
        assert mock_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_snapshot_at_time_not_found(self, repository, mock_session):
        """Test snapshot not found."""
        # Setup
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await repository.get_snapshot_at_time(
            address="0x" + "a" * 40,
            timestamp=datetime.now(timezone.utc),
            tolerance_hours=1
        )
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_snapshots_batch_at_time(self, repository, mock_session):
        """Test batch snapshot retrieval."""
        # Setup
        target_time = datetime.now(timezone.utc)
        addresses = [f"0x{'a' * 40}", f"0x{'b' * 40}", f"0x{'c' * 40}"]
        
        mock_snapshots = [
            Mock(
                spec=WhaleBalanceSnapshot,
                address=addr,
                balance_eth=Decimal("1.0"),
                snapshot_timestamp=target_time
            )
            for addr in addresses
        ]
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=mock_snapshots)
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await repository.get_snapshots_batch_at_time(
            addresses=addresses,
            timestamp=target_time,
            tolerance_hours=1
        )
        
        # Verify
        assert len(result) == 3
        assert all(addr in result for addr in addresses)
    
    @pytest.mark.asyncio
    async def test_get_snapshots_batch_at_time_empty(self, repository, mock_session):
        """Test batch retrieval with empty address list."""
        # Execute
        result = await repository.get_snapshots_batch_at_time(
            addresses=[],
            timestamp=datetime.now(timezone.utc)
        )
        
        # Verify
        assert result == {}
        assert not mock_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_snapshots_batch_keeps_closest(self, repository, mock_session):
        """Test that batch retrieval keeps snapshot closest to target time."""
        # Setup
        target_time = datetime.now(timezone.utc)
        address = f"0x{'a' * 40}"
        
        # Create snapshots at different times
        snapshot_1h_ago = Mock(
            spec=WhaleBalanceSnapshot,
            address=address,
            snapshot_timestamp=target_time - timedelta(hours=1)
        )
        snapshot_30min_ago = Mock(
            spec=WhaleBalanceSnapshot,
            address=address,
            snapshot_timestamp=target_time - timedelta(minutes=30)
        )
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[snapshot_1h_ago, snapshot_30min_ago])
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await repository.get_snapshots_batch_at_time(
            addresses=[address],
            timestamp=target_time,
            tolerance_hours=2
        )
        
        # Verify: Should keep snapshot_30min_ago (closer to target)
        assert len(result) == 1
        assert result[address].snapshot_timestamp == snapshot_30min_ago.snapshot_timestamp
    
    @pytest.mark.asyncio
    async def test_get_addresses_in_top_at_time(self, repository, mock_session):
        """Test getting top addresses at historical time."""
        # Setup
        target_time = datetime.now(timezone.utc)
        
        mock_snapshots = [
            Mock(
                spec=WhaleBalanceSnapshot,
                address=f"0x{'a' * 40}",
                balance_eth=Decimal("10.0"),
                snapshot_timestamp=target_time
            ),
            Mock(
                spec=WhaleBalanceSnapshot,
                address=f"0x{'b' * 40}",
                balance_eth=Decimal("5.0"),
                snapshot_timestamp=target_time
            ),
            Mock(
                spec=WhaleBalanceSnapshot,
                address=f"0x{'c' * 40}",
                balance_eth=Decimal("1.0"),
                snapshot_timestamp=target_time
            )
        ]
        
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=mock_snapshots)
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await repository.get_addresses_in_top_at_time(
            timestamp=target_time,
            limit=2,  # Only top 2
            tolerance_hours=1
        )
        
        # Verify: Should return top 2 by balance
        assert len(result) == 2
        assert f"0x{'a' * 40}" in result  # Highest balance
        assert f"0x{'b' * 40}" in result  # Second highest
        assert f"0x{'c' * 40}" not in result  # Excluded (rank 3)
    
    @pytest.mark.asyncio
    async def test_get_latest_snapshot_time(self, repository, mock_session):
        """Test getting latest snapshot timestamp."""
        # Setup
        latest_time = datetime.now(timezone.utc)
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=latest_time)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await repository.get_latest_snapshot_time()
        
        # Verify
        assert result == latest_time
        assert mock_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_latest_snapshot_time_none(self, repository, mock_session):
        """Test getting latest time when no snapshots exist."""
        # Setup
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await repository.get_latest_snapshot_time()
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_summary(self, repository, mock_session):
        """Test getting snapshot summary statistics."""
        # Setup
        target_time = datetime.now(timezone.utc)
        
        mock_row = Mock()
        mock_row.total = 100
        mock_row.unique_addresses = 95
        mock_row.total_balance = 1000.0
        mock_row.avg_balance = 10.0
        mock_row.min_balance = 0.1
        mock_row.max_balance = 100.0
        
        mock_result = Mock()
        mock_result.one_or_none = Mock(return_value=mock_row)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await repository.get_summary(
            timestamp=target_time,
            network="ethereum"
        )
        
        # Verify
        assert result is not None
        assert result.total_snapshots == 100
        assert result.total_addresses == 95
        assert result.total_balance_eth == Decimal("1000.0")
        assert result.avg_balance_eth == Decimal("10.0")
        assert result.min_balance_eth == Decimal("0.1")
        assert result.max_balance_eth == Decimal("100.0")
        assert result.snapshot_timestamp == target_time
        assert result.network == "ethereum"
    
    @pytest.mark.asyncio
    async def test_get_summary_no_data(self, repository, mock_session):
        """Test summary when no snapshots exist."""
        # Setup
        mock_result = Mock()
        mock_result.one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await repository.get_summary(
            timestamp=datetime.now(timezone.utc)
        )
        
        # Verify
        assert result is None


class TestSnapshotSchemaValidation:
    """Test Pydantic schema validation."""
    
    def test_valid_snapshot_creation(self):
        """Test creating valid snapshot."""
        snapshot = WhaleBalanceSnapshotCreate(
            address="0x" + "a" * 40,
            balance_wei="1000000000000000000",
            balance_eth=Decimal("1.0"),
            block_number=19000000,
            snapshot_timestamp=datetime.now(timezone.utc),
            network="ethereum"
        )
        
        assert snapshot.address == "0x" + "a" * 40
        assert snapshot.balance_wei == "1000000000000000000"
        assert snapshot.balance_eth == Decimal("1.0")
    
    def test_address_validation_no_0x(self):
        """Test address validation rejects addresses without 0x."""
        with pytest.raises(ValueError, match="String should have at least 42 characters"):
            WhaleBalanceSnapshotCreate(
                address="a" * 40,  # Missing 0x - will fail length check first
                balance_wei="1000000000000000000",
                balance_eth=Decimal("1.0"),
                block_number=19000000,
                snapshot_timestamp=datetime.now(timezone.utc)
            )
    
    def test_address_validation_wrong_length(self):
        """Test address validation rejects wrong length."""
        with pytest.raises(ValueError, match="42 characters"):
            WhaleBalanceSnapshotCreate(
                address="0x123",  # Too short
                balance_wei="1000000000000000000",
                balance_eth=Decimal("1.0"),
                block_number=19000000,
                snapshot_timestamp=datetime.now(timezone.utc)
            )
    
    def test_address_normalized_to_lowercase(self):
        """Test addresses are normalized to lowercase."""
        snapshot = WhaleBalanceSnapshotCreate(
            address="0x" + "A" * 40,  # Uppercase
            balance_wei="1000000000000000000",
            balance_eth=Decimal("1.0"),
            block_number=19000000,
            snapshot_timestamp=datetime.now(timezone.utc)
        )
        
        assert snapshot.address == "0x" + "a" * 40  # Lowercase
    
    def test_network_validation(self):
        """Test network validation."""
        with pytest.raises(ValueError, match="must be one of"):
            WhaleBalanceSnapshotCreate(
                address="0x" + "a" * 40,
                balance_wei="1000000000000000000",
                balance_eth=Decimal("1.0"),
                block_number=19000000,
                snapshot_timestamp=datetime.now(timezone.utc),
                network="invalid_network"
            )
    
    def test_negative_balance_rejected(self):
        """Test negative balance is rejected."""
        with pytest.raises(ValueError):
            WhaleBalanceSnapshotCreate(
                address="0x" + "a" * 40,
                balance_wei="-1000000000000000000",
                balance_eth=Decimal("-1.0"),  # Negative
                block_number=19000000,
                snapshot_timestamp=datetime.now(timezone.utc)
            )
    
    def test_zero_block_number_rejected(self):
        """Test zero block number is rejected."""
        with pytest.raises(ValueError):
            WhaleBalanceSnapshotCreate(
                address="0x" + "a" * 40,
                balance_wei="1000000000000000000",
                balance_eth=Decimal("1.0"),
                block_number=0,  # Invalid
                snapshot_timestamp=datetime.now(timezone.utc)
            )
