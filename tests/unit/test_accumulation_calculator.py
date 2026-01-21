"""Unit Tests for AccumulationScoreCalculator - MVP Version

Run: pytest tests/unit/test_accumulation_calculator.py -v
"""

import pytest
from unittest.mock import Mock, AsyncMock
from decimal import Decimal

from src.analyzers.accumulation_score_calculator import AccumulationScoreCalculator
from src.schemas.accumulation_schemas import AccumulationMetricCreate, AccumulationMetric


@pytest.fixture
def mock_dependencies():
    """Create mocked dependencies."""
    whale_provider = Mock()
    whale_provider.health_check = AsyncMock(return_value={"status": "healthy"})
    
    multicall_client = Mock()
    multicall_client.get_latest_block = AsyncMock(return_value=24000000)
    multicall_client.get_balances_batch = AsyncMock()  # NEW: batch balances instead of historical
    multicall_client.health_check = AsyncMock(return_value={"status": "healthy"})
    
    repository = Mock()
    repository.create = AsyncMock()
    repository.get_recent_metrics = AsyncMock(return_value=[])
    
    snapshot_repo = Mock()  # NEW: snapshot repository
    snapshot_repo.get_addresses_in_top_at_time = AsyncMock(return_value=set())
    snapshot_repo.get_snapshots_batch_at_time = AsyncMock(return_value={})
    
    return whale_provider, multicall_client, repository, snapshot_repo


@pytest.fixture
def calculator(mock_dependencies):
    """Create calculator with mocked dependencies."""
    whale_provider, multicall_client, repository, snapshot_repo = mock_dependencies
    return AccumulationScoreCalculator(
        whale_provider=whale_provider,
        multicall_client=multicall_client,
        repository=repository,
        snapshot_repo=snapshot_repo,
        lookback_hours=24
    )


class TestCalculatorInit:
    def test_init(self, mock_dependencies):
        """Test initialization."""
        whale_provider, multicall_client, repository, snapshot_repo = mock_dependencies
        calc = AccumulationScoreCalculator(
            whale_provider=whale_provider,
            multicall_client=multicall_client,
            repository=repository,
            snapshot_repo=snapshot_repo,
            lookback_hours=12
        )
        
        assert calc.whale_provider == whale_provider
        assert calc.multicall_client == multicall_client
        assert calc.repository == repository
        assert calc.snapshot_repo == snapshot_repo
        assert calc.lookback_hours == 12


class TestCalculateAccumulationScore:
    @pytest.mark.asyncio
    async def test_basic_calculation(self, calculator, mock_dependencies):
        """Test basic accumulation score calculation with Survival Bias fix."""
        whale_provider, multicall_client, repository, snapshot_repo = mock_dependencies
        
        # Mock current whales
        whale_provider.get_top_whales = AsyncMock(return_value=[
            {'address': '0xAddr1', 'balance_wei': int(2000 * 1e18)},
            {'address': '0xAddr2', 'balance_wei': int(1500 * 1e18)},
        ])
        
        # Mock historical top whales (UNION approach)
        snapshot_repo.get_addresses_in_top_at_time = AsyncMock(return_value={
            '0xAddr1',  # Was whale, still whale
            '0xAddr3',  # Was whale, NOT whale anymore (survival bias!)
        })
        
        # Mock current balances for ALL addresses (current ∪ historical)
        multicall_client.get_balances_batch = AsyncMock(return_value={
            '0xAddr1': int(2000 * 1e18),
            '0xAddr2': int(1500 * 1e18),
            '0xAddr3': int(500 * 1e18),  # Dropped out of top (was whale)
        })
        
        # Mock historical snapshots
        mock_snapshot = Mock()
        snapshot_repo.get_snapshots_batch_at_time = AsyncMock(return_value={
            '0xAddr1': Mock(balance_wei=str(int(1800 * 1e18))),  # +200 ETH
            '0xAddr2': Mock(balance_wei=str(int(0))),  # New whale (+1500 ETH)
            '0xAddr3': Mock(balance_wei=str(int(1000 * 1e18))),  # -500 ETH (exited)
        })
        
        # Mock repository create
        mock_metric = Mock(spec=AccumulationMetric)
        mock_metric.accumulation_score = Decimal('8.57')
        mock_metric.whale_count = 3  # Now 3 (UNION)
        mock_metric.total_balance_change_eth = Decimal('1200')  # +200 +1500 -500
        repository.create = AsyncMock(return_value=mock_metric)
        
        result = await calculator.calculate_accumulation_score()
        
        assert result == mock_metric
        assert repository.create.called
        
        # VERIFY: We analyzed ALL addresses (UNION)
        multicall_client.get_balances_batch.assert_called_once()
        call_args = multicall_client.get_balances_batch.call_args
        analyzed_addresses = set(call_args.kwargs['addresses'])
        assert analyzed_addresses == {'0xAddr1', '0xAddr2', '0xAddr3'}
    
    @pytest.mark.asyncio
    async def test_no_whales_raises_error(self, calculator, mock_dependencies):
        """Test error when no whales found."""
        whale_provider, _, _, _ = mock_dependencies
        whale_provider.get_top_whales = AsyncMock(return_value=[])
        
        with pytest.raises(ValueError, match="No whales found"):
            await calculator.calculate_accumulation_score()


class TestCalculateMetrics:
    def test_accumulation_scenario(self, calculator):
        """Test metrics calculation for accumulation scenario."""
        current = {
            '0xAddr1': int(2000 * 1e18),
            '0xAddr2': int(1500 * 1e18),
        }
        historical = {
            '0xAddr1': int(1800 * 1e18),
            '0xAddr2': int(1400 * 1e18),
        }
        
        metrics = calculator._calculate_metrics(
            current_balances=current,
            historical_balances=historical,
            token_symbol='ETH',
            whale_count=2,
            current_block=24000000,
            historical_block=23992800
        )
        
        assert metrics.whale_count == 2
        assert metrics.accumulation_score > 0  # Positive = accumulation
        assert metrics.accumulators_count == 2
        assert metrics.distributors_count == 0


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_success(self, calculator):
        """Test successful health check."""
        health = await calculator.health_check()
        
        assert health["status"] == "healthy"
        assert health["whale_provider"] == "ok"
        assert health["multicall_client"] == "ok"


# Run: pytest tests/unit/test_accumulation_calculator.py -v
