"""
Test for Snapshot Density Validation (GEMINI FIX #7)

Validates that incomplete snapshot history blocks [High Conviction] tags.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from src.repositories.snapshot_repository import SnapshotRepository
from src.exceptions import InsufficientSnapshotCoverageError
from src.analyzers.accumulation_score_calculator import AccumulationScoreCalculator
from src.schemas.accumulation_schemas import AccumulationMetricCreate


@pytest.fixture
def mock_session():
    """Create mocked SQLAlchemy session."""
    session = AsyncMock()
    return session


@pytest.fixture
def snapshot_repo(mock_session):
    """Create SnapshotRepository with mocked session."""
    return SnapshotRepository(session=mock_session)


@pytest.fixture
def calculator():
    """Create AccumulationScoreCalculator with mocked dependencies."""
    return AccumulationScoreCalculator(
        whale_provider=AsyncMock(),
        multicall_client=AsyncMock(),
        repository=AsyncMock(),
        snapshot_repo=AsyncMock(),
        price_provider=AsyncMock(),
        lookback_hours=24
    )


class TestSnapshotDensityValidation:
    """Test snapshot density validation (bot downtime detection)."""
    
    @pytest.mark.asyncio
    async def test_full_coverage_passes(self, snapshot_repo, mock_session):
        """100% coverage should pass validation."""
        # Arrange: Mock query to return full coverage
        # 10 addresses × 24 hours = 240 expected, 240 found
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 240  # All snapshots present
        mock_session.execute.return_value = mock_result
        
        addresses = [f"0x{i:040x}" for i in range(10)]
        
        # Act
        is_valid, coverage, found, expected = await snapshot_repo.validate_snapshot_density(
            addresses=addresses,
            lookback_hours=24,
            min_coverage_pct=85.0
        )
        
        # Assert
        assert is_valid is True
        assert coverage == 100.0
        assert found == 240
        assert expected == 240
    
    @pytest.mark.asyncio
    async def test_low_coverage_raises_exception(self, snapshot_repo, mock_session):
        """<85% coverage should raise InsufficientSnapshotCoverageError."""
        # Arrange: Bot downtime - only 50% snapshots available
        # 10 addresses × 24 hours = 240 expected, 120 found (50%)
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 120  # Missing 50%
        mock_session.execute.return_value = mock_result
        
        addresses = [f"0x{i:040x}" for i in range(10)]
        
        # Act & Assert
        with pytest.raises(InsufficientSnapshotCoverageError) as exc_info:
            await snapshot_repo.validate_snapshot_density(
                addresses=addresses,
                lookback_hours=24,
                min_coverage_pct=85.0
            )
        
        # Verify exception details
        assert exc_info.value.found_snapshots == 120
        assert exc_info.value.expected_snapshots == 240
        assert exc_info.value.coverage_pct == 50.0
        assert exc_info.value.min_coverage_pct == 85.0
    
    @pytest.mark.asyncio
    async def test_boundary_coverage_85_percent(self, snapshot_repo, mock_session):
        """Exactly 85% coverage should raise exception (boundary inclusive)."""
        # Arrange: Exactly at boundary
        # 100 addresses × 24 hours = 2400 expected, 2040 found (85%)
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 2040  # Exactly 85%
        mock_session.execute.return_value = mock_result
        
        addresses = [f"0x{i:040x}" for i in range(100)]
        
        # Act & Assert: 85% should FAIL (need >85%)
        with pytest.raises(InsufficientSnapshotCoverageError):
            await snapshot_repo.validate_snapshot_density(
                addresses=addresses,
                lookback_hours=24,
                min_coverage_pct=85.0
            )
    
    @pytest.mark.asyncio
    async def test_just_above_threshold_passes(self, snapshot_repo, mock_session):
        """85.5% coverage should pass validation."""
        # Arrange: Slightly above threshold
        # 100 addresses × 24 hours = 2400 expected, 2052 found (85.5%)
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 2052
        mock_session.execute.return_value = mock_result
        
        addresses = [f"0x{i:040x}" for i in range(100)]
        
        # Act
        is_valid, coverage, found, expected = await snapshot_repo.validate_snapshot_density(
            addresses=addresses,
            lookback_hours=24,
            min_coverage_pct=85.0
        )
        
        # Assert
        assert is_valid is True
        assert coverage == pytest.approx(85.5, rel=0.1)


class TestIncompleteDataTagAssignment:
    """Test that [Incomplete Data] tag blocks [High Conviction]."""
    
    def test_incomplete_data_blocks_all_tags(self, calculator):
        """When snapshot_density_valid=False, only [Incomplete Data] tag assigned."""
        # Arrange: Metric that WOULD get High Conviction normally
        metric = AccumulationMetricCreate(
            token_symbol="ETH",
            whale_count=100,
            total_balance_current_wei="100000000000000000000",
            total_balance_historical_wei="90000000000000000000",
            total_balance_change_wei="10000000000000000000",
            total_balance_current_eth=Decimal("100"),
            total_balance_historical_eth=Decimal("90"),
            total_balance_change_eth=Decimal("10"),
            accumulation_score=Decimal("11.11"),
            
            total_weth_balance_eth=Decimal("2"),
            total_steth_balance_eth=Decimal("3"),
            lst_adjusted_score=Decimal("12.5"),
            lst_migration_count=0,
            steth_eth_rate=Decimal("1.0"),
            
            mad_threshold=Decimal("2.0"),  # Would trigger High Conviction
            is_anomaly=False,
            
            concentration_gini=Decimal("0.5"),
            num_signals_used=95,
            num_signals_excluded=5,
            accumulators_count=60,
            distributors_count=30,
            neutral_count=10,
            
            current_block_number=12345,
            historical_block_number=12000,
            lookback_hours=24,
            tags=[]
        )
        
        # Act: snapshot_density_valid=False (bot downtime)
        tags = calculator._assign_tags(
            metric,
            whale_count=100,
            looping_suspect_count=0,
            snapshot_density_valid=False,  # ❌ Incomplete data!
            snapshot_coverage_pct=50.0  # Only 50% coverage
        )
        
        # Assert: ONLY [Incomplete Data], NO other tags
        assert tags == ["Incomplete Data"]
        assert "High Conviction" not in tags
        assert "Organic Accumulation" not in tags
    
    def test_complete_data_allows_normal_tags(self, calculator):
        """When snapshot_density_valid=True, normal tagging proceeds."""
        # Arrange: Same metric
        metric = AccumulationMetricCreate(
            token_symbol="ETH",
            whale_count=100,
            total_balance_current_wei="100000000000000000000",
            total_balance_historical_wei="90000000000000000000",
            total_balance_change_wei="10000000000000000000",
            total_balance_current_eth=Decimal("100"),
            total_balance_historical_eth=Decimal("90"),
            total_balance_change_eth=Decimal("10"),
            accumulation_score=Decimal("11.11"),
            
            total_weth_balance_eth=Decimal("2"),
            total_steth_balance_eth=Decimal("3"),
            lst_adjusted_score=Decimal("12.5"),
            lst_migration_count=0,
            steth_eth_rate=Decimal("1.0"),
            
            mad_threshold=Decimal("2.0"),
            is_anomaly=False,
            
            concentration_gini=Decimal("0.5"),
            num_signals_used=95,
            num_signals_excluded=5,
            accumulators_count=60,
            distributors_count=30,
            neutral_count=10,
            
            current_block_number=12345,
            historical_block_number=12000,
            lookback_hours=24,
            tags=[]
        )
        
        # Act: snapshot_density_valid=True (normal operation)
        tags = calculator._assign_tags(
            metric,
            whale_count=100,
            looping_suspect_count=0,
            snapshot_density_valid=True,  # ✅ Complete data
            snapshot_coverage_pct=95.0  # 95% coverage
        )
        
        # Assert: Normal tags assigned
        assert "Incomplete Data" not in tags
        assert "High Conviction" in tags  # Should get this tag
        assert "Organic Accumulation" in tags  # 60% accumulators


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
