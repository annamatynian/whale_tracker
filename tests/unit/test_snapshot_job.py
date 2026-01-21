"""Unit Tests for SnapshotJob

Run: pytest tests/unit/test_snapshot_job.py -v
"""

import pytest
from unittest.mock import Mock, AsyncMock
from decimal import Decimal
from datetime import datetime, timezone

from src.jobs.snapshot_job import SnapshotJob
from src.schemas.snapshot_schemas import WhaleBalanceSnapshotCreate


@pytest.fixture
def mock_dependencies():
    """Create mocked dependencies."""
    whale_provider = Mock()
    whale_provider.health_check = AsyncMock(return_value={"status": "healthy"})
    
    multicall_client = Mock()
    multicall_client.get_latest_block = AsyncMock(return_value=24000000)
    multicall_client.health_check = AsyncMock(return_value={"status": "healthy"})
    
    snapshot_repo = Mock()
    snapshot_repo.save_snapshots_batch = AsyncMock(return_value=10)
    snapshot_repo.get_latest_snapshot_time = AsyncMock(
        return_value=datetime.now(timezone.utc)
    )
    
    return whale_provider, multicall_client, snapshot_repo


@pytest.fixture
def snapshot_job(mock_dependencies):
    """Create SnapshotJob with mocked dependencies."""
    whale_provider, multicall_client, snapshot_repo = mock_dependencies
    return SnapshotJob(
        whale_provider=whale_provider,
        multicall_client=multicall_client,
        snapshot_repo=snapshot_repo,
        whale_limit=10,
        network="ethereum"
    )


class TestSnapshotJobInit:
    def test_init(self, mock_dependencies):
        """Test initialization."""
        whale_provider, multicall_client, snapshot_repo = mock_dependencies
        job = SnapshotJob(
            whale_provider=whale_provider,
            multicall_client=multicall_client,
            snapshot_repo=snapshot_repo,
            whale_limit=1000,
            network="ethereum"
        )
        
        assert job.whale_provider == whale_provider
        assert job.multicall_client == multicall_client
        assert job.snapshot_repo == snapshot_repo
        assert job.whale_limit == 1000
        assert job.network == "ethereum"


class TestRunHourlySnapshot:
    @pytest.mark.asyncio
    async def test_successful_snapshot(self, snapshot_job, mock_dependencies):
        """Test successful snapshot creation."""
        whale_provider, multicall_client, snapshot_repo = mock_dependencies
        
        # Mock whale data (VALID Ethereum addresses - 42 chars)
        whale_provider.get_top_whales = AsyncMock(return_value=[
            {'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1', 'balance_wei': int(1000 * 1e18)},
            {'address': '0x28C6c06298d514Db089934071355E5743bf21d60', 'balance_wei': int(500 * 1e18)},
            {'address': '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE', 'balance_wei': int(250 * 1e18)},
        ])
        
        # Mock repository
        snapshot_repo.save_snapshots_batch = AsyncMock(return_value=3)
        
        # Run job
        saved_count = await snapshot_job.run_hourly_snapshot()
        
        # Verify
        assert saved_count == 3
        
        # Check that save_snapshots_batch was called
        snapshot_repo.save_snapshots_batch.assert_called_once()
        
        # Verify snapshots were created correctly
        call_args = snapshot_repo.save_snapshots_batch.call_args
        snapshots = call_args.args[0]
        
        assert len(snapshots) == 3
        assert snapshots[0].address == '0x742d35cc6634c0532925a3b844bc9e7595f0beb1'  # lowercase
        assert snapshots[0].balance_wei == str(int(1000 * 1e18))
        assert snapshots[0].network == 'ethereum'
    
    @pytest.mark.asyncio
    async def test_no_whales_raises_error(self, snapshot_job, mock_dependencies):
        """Test error when no whales found."""
        whale_provider, _, _ = mock_dependencies
        whale_provider.get_top_whales = AsyncMock(return_value=[])
        
        with pytest.raises(ValueError, match="No whales found"):
            await snapshot_job.run_hourly_snapshot()
    
    @pytest.mark.asyncio
    async def test_snapshot_includes_metadata(self, snapshot_job, mock_dependencies):
        """Test that snapshots include block number and timestamp."""
        whale_provider, multicall_client, snapshot_repo = mock_dependencies
        
        # Mock whale data (VALID address)
        whale_provider.get_top_whales = AsyncMock(return_value=[
            {'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1', 'balance_wei': int(1000 * 1e18)},
        ])
        
        # Mock block number
        test_block = 24123456
        multicall_client.get_latest_block = AsyncMock(return_value=test_block)
        
        # Run job
        await snapshot_job.run_hourly_snapshot()
        
        # Verify snapshot metadata
        call_args = snapshot_repo.save_snapshots_batch.call_args
        snapshots = call_args.args[0]
        
        assert snapshots[0].block_number == test_block
        assert snapshots[0].snapshot_timestamp is not None
        assert isinstance(snapshots[0].snapshot_timestamp, datetime)


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_success(self, snapshot_job):
        """Test successful health check."""
        health = await snapshot_job.health_check()
        
        assert health["status"] == "healthy"
        assert health["whale_provider"] == "ok"
        assert health["multicall_client"] == "ok"
        assert health["snapshot_repo"] == "ok"
        assert health["whale_limit"] == 10
        assert health["network"] == "ethereum"
        assert "latest_snapshot" in health
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy_provider(self, snapshot_job, mock_dependencies):
        """Test health check with unhealthy whale provider."""
        whale_provider, _, _ = mock_dependencies
        whale_provider.health_check = AsyncMock(
            return_value={"status": "unhealthy", "error": "RPC down"}
        )
        
        health = await snapshot_job.health_check()
        
        assert health["status"] == "unhealthy"
        assert "WhaleListProvider unhealthy" in health["error"]


# Run: pytest tests/unit/test_snapshot_job.py -v
