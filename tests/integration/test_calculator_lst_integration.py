"""
Integration Test for AccumulationScoreCalculator - LST Phase 2 (Partial)

Tests that current LST integration works end-to-end:
- price_provider injection
- _fetch_lst_balances() execution
- _calculate_metrics() with LST aggregation, MAD, Gini
- Database storage with new fields

Run: pytest tests/integration/test_calculator_lst_integration.py -v -s
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from datetime import datetime, UTC

from src.analyzers.accumulation_score_calculator import AccumulationScoreCalculator
from src.schemas.accumulation_schemas import AccumulationMetric


class MockPriceProvider:
    """Mock PriceProvider for testing."""
    
    async def get_steth_eth_rate(self):
        """Return mock stETH rate."""
        return Decimal('0.9985')


class MockMulticallClient:
    """Mock MulticallClient with LST support."""
    
    async def get_balances_batch(self, addresses, network):
        """Return mock ETH balances."""
        return {
            addr: 100_000_000_000_000_000_000 for addr in addresses  # 100 ETH each
        }
    
    async def get_erc20_balances_batch(self, addresses, token_address, network):
        """Return mock WETH/stETH balances."""
        # Simulate: 50% of whales have 10 WETH, 30% have 20 stETH
        from src.data.multicall_client import WETH_ADDRESS, STETH_ADDRESS
        
        if token_address == WETH_ADDRESS:
            return {
                addr: 10_000_000_000_000_000_000 if i % 2 == 0 else 0  # 10 WETH for even indices
                for i, addr in enumerate(addresses)
            }
        elif token_address == STETH_ADDRESS:
            return {
                addr: 20_000_000_000_000_000_000 if i % 3 == 0 else 0  # 20 stETH for every 3rd
                for i, addr in enumerate(addresses)
            }
        return {}
    
    async def get_latest_block(self, network):
        """Return mock block number."""
        return 20000000
    
    async def health_check(self):
        return {"status": "healthy"}


class MockWhaleProvider:
    """Mock WhaleListProvider."""
    
    async def get_top_whales(self, limit, network):
        """Return mock whale addresses - FIXED: proper 42-char addresses."""
        return [
            {"address": f"0x{str(i).zfill(40)}"}
            for i in range(min(limit, 10))  # Return 10 whales max
        ]
    
    async def health_check(self):
        return {"status": "healthy"}


class MockSnapshotRepository:
    """Mock SnapshotRepository."""
    
    async def get_addresses_in_top_at_time(self, timestamp, limit, tolerance_hours, network):
        """Return same addresses (no churn) - FIXED: proper 42-char addresses."""
        return {
            f"0x{str(i).zfill(40)}"  # Proper 42-char address: 0x + 40 hex chars
            for i in range(min(limit, 10))
        }
    
    async def get_snapshots_batch_at_time(self, addresses, timestamp, tolerance_hours, network):
        """Return mock historical snapshots (90 ETH each = 10% less)."""
        from src.schemas.snapshot_schemas import WhaleBalanceSnapshot
        
        return {
            addr: WhaleBalanceSnapshot(
                id=1,
                address=addr,  # Use the provided address (already 42 chars)
                balance_wei="90000000000000000000",  # 90 ETH
                balance_eth=Decimal('90.0'),
                block_number=19993000,
                snapshot_timestamp=timestamp,
                network=network,
                created_at=datetime.now(UTC)
            )
            for addr in addresses
        }


class MockAccumulationRepository:
    """Mock AccumulationRepository."""
    
    def __init__(self):
        self.stored_metrics = []
    
    async def create(self, metric_create):
        """Store metric and return with ID."""
        metric = AccumulationMetric(
            id=len(self.stored_metrics) + 1,
            **metric_create.model_dump(),
            created_at=datetime.now(UTC)
        )
        self.stored_metrics.append(metric)
        return metric
    
    async def get_recent_metrics(self, token_symbol=None, limit=10):
        """Return stored metrics."""
        return self.stored_metrics[:limit]


@pytest.fixture
def mock_dependencies():
    """Create all mocked dependencies."""
    return {
        'whale_provider': MockWhaleProvider(),
        'multicall_client': MockMulticallClient(),
        'repository': MockAccumulationRepository(),
        'snapshot_repo': MockSnapshotRepository(),
        'price_provider': MockPriceProvider()
    }


@pytest.fixture
def calculator(mock_dependencies):
    """Create calculator with mocked dependencies."""
    return AccumulationScoreCalculator(**mock_dependencies)


class TestLSTIntegrationPhase2:
    """Integration tests for LST Phase 2 (partial implementation)."""
    
    @pytest.mark.asyncio
    async def test_calculator_initialization(self, calculator):
        """Test calculator initializes with price_provider."""
        assert calculator.price_provider is not None
        assert calculator.lookback_hours == 24
    
    @pytest.mark.asyncio
    async def test_fetch_lst_balances(self, calculator, mock_dependencies):
        """Test _fetch_lst_balances method execution."""
        addresses = [f"0x{'1234567890abcdef' * 2}{i:04x}" for i in range(5)]
        
        weth_balances, steth_balances, steth_rate = await calculator._fetch_lst_balances(
            addresses=addresses,
            network="ethereum"
        )
        
        # Check results
        assert len(weth_balances) == 5
        assert len(steth_balances) == 5
        assert steth_rate == Decimal('0.9985')
        
        # Check some whales have LST balances
        assert any(balance > 0 for balance in weth_balances.values())
        assert any(balance > 0 for balance in steth_balances.values())
    
    @pytest.mark.asyncio
    async def test_calculate_metrics_with_lst(self, calculator, mock_dependencies):
        """Test _calculate_metrics with LST aggregation."""
        # Mock data
        current_balances = {
            "0xWhale1": 100_000_000_000_000_000_000,  # 100 ETH
            "0xWhale2": 100_000_000_000_000_000_000,
        }
        historical_balances = {
            "0xWhale1": 90_000_000_000_000_000_000,  # 90 ETH
            "0xWhale2": 90_000_000_000_000_000_000,
        }
        weth_balances = {
            "0xWhale1": 10_000_000_000_000_000_000,  # 10 WETH
            "0xWhale2": 0,
        }
        steth_balances = {
            "0xWhale1": 0,
            "0xWhale2": 20_000_000_000_000_000_000,  # 20 stETH
        }
        steth_rate = Decimal('0.9985')
        
        # Calculate metrics
        metrics = calculator._calculate_metrics(
            current_balances=current_balances,
            historical_balances=historical_balances,
            weth_balances=weth_balances,
            steth_balances=steth_balances,
            steth_rate=steth_rate,
            token_symbol="ETH",
            whale_count=2,
            current_block=20000000,
            historical_block=19993000
        )
        
        # Check native ETH metrics
        assert metrics.accumulation_score > Decimal('0')  # Positive (accumulating)
        assert metrics.accumulators_count == 2
        assert metrics.distributors_count == 0
        
        # Check LST fields populated
        assert metrics.total_weth_balance_eth == Decimal('10.0')
        assert metrics.total_steth_balance_eth > Decimal('19.9')  # ~20 * 0.9985
        assert metrics.lst_adjusted_score is not None
        assert metrics.steth_eth_rate == Decimal('0.9985')
        
        # Check statistical fields
        assert metrics.concentration_gini is not None
        assert 0 <= metrics.concentration_gini <= 1
        assert metrics.is_anomaly is False  # No outliers with only 2 whales
        assert metrics.mad_threshold is not None
        
        # Check tags initialized
        assert metrics.tags == []
        
        # Check TODOs are None
        assert metrics.lst_migration_count == 0  # TODO
        assert metrics.price_change_48h_pct is None  # TODO
    
    @pytest.mark.asyncio
    async def test_end_to_end_calculation(self, calculator, mock_dependencies):
        """Test full end-to-end accumulation score calculation."""
        # Run full calculation
        result = await calculator.calculate_accumulation_score(
            token_symbol="ETH",
            whale_limit=10,
            network="ethereum"
        )
        
        # Check result is AccumulationMetric (from DB)
        assert result.id is not None
        assert result.token_symbol == "ETH"
        assert result.whale_count == 10
        
        # Check native ETH metrics
        assert result.total_balance_current_eth > Decimal('0')
        assert result.total_balance_historical_eth > Decimal('0')
        assert result.accumulation_score is not None
        
        # Check LST metrics populated
        assert result.total_weth_balance_eth is not None
        assert result.total_steth_balance_eth is not None
        assert result.lst_adjusted_score is not None
        assert result.steth_eth_rate == Decimal('0.9985')
        
        # Check Gini and MAD
        assert result.concentration_gini is not None
        assert result.mad_threshold is not None
        
        # Check stored in repository
        repo = mock_dependencies['repository']
        assert len(repo.stored_metrics) == 1
        assert repo.stored_metrics[0].id == result.id
    
    @pytest.mark.asyncio
    async def test_gini_coefficient_calculation(self, calculator):
        """Test Gini coefficient with known distribution."""
        # Perfect equality: all whales have same balance
        current_equal = {f"0xWhale{i}": 100_000_000_000_000_000_000 for i in range(10)}
        historical_equal = {f"0xWhale{i}": 90_000_000_000_000_000_000 for i in range(10)}
        weth = {addr: 0 for addr in current_equal}
        steth = {addr: 0 for addr in current_equal}
        
        metrics_equal = calculator._calculate_metrics(
            current_balances=current_equal,
            historical_balances=historical_equal,
            weth_balances=weth,
            steth_balances=steth,
            steth_rate=Decimal('1.0'),
            token_symbol="ETH",
            whale_count=10,
            current_block=20000000,
            historical_block=19993000
        )
        
        # Gini should be ~0 for perfect equality
        assert metrics_equal.concentration_gini < Decimal('0.05')
        
        # High inequality: one whale has most
        current_unequal = {f"0xWhale{i}": 1_000_000_000_000_000_000 for i in range(9)}  # 1 ETH each
        current_unequal["0xWhaleRich"] = 1000_000_000_000_000_000_000  # 1000 ETH
        historical_unequal = {addr: bal for addr, bal in current_unequal.items()}
        
        metrics_unequal = calculator._calculate_metrics(
            current_balances=current_unequal,
            historical_balances=historical_unequal,
            weth_balances={addr: 0 for addr in current_unequal},
            steth_balances={addr: 0 for addr in current_unequal},
            steth_rate=Decimal('1.0'),
            token_symbol="ETH",
            whale_count=10,
            current_block=20000000,
            historical_block=19993000
        )
        
        # Gini should be high for inequality
        assert metrics_unequal.concentration_gini > Decimal('0.8')
    
    @pytest.mark.asyncio
    async def test_mad_anomaly_detection(self, calculator):
        """Test MAD detects outlier whale."""
        # 9 whales with varying small changes (+5% to +15%), 1 whale with +500% (extreme outlier)
        current = {
            "0xWhale0": 105_000_000_000_000_000_000,  # +5%
            "0xWhale1": 108_000_000_000_000_000_000,  # +8%
            "0xWhale2": 110_000_000_000_000_000_000,  # +10%
            "0xWhale3": 112_000_000_000_000_000_000,  # +12%
            "0xWhale4": 115_000_000_000_000_000_000,  # +15%
            "0xWhale5": 107_000_000_000_000_000_000,  # +7%
            "0xWhale6": 109_000_000_000_000_000_000,  # +9%
            "0xWhale7": 111_000_000_000_000_000_000,  # +11%
            "0xWhale8": 113_000_000_000_000_000_000,  # +13%
        }
        current["0xWhaleOutlier"] = 600_000_000_000_000_000_000  # 600 ETH (was 100 = +500%)
        
        historical = {f"0xWhale{i}": 100_000_000_000_000_000_000 for i in range(9)}  # All 100 ETH
        historical["0xWhaleOutlier"] = 100_000_000_000_000_000_000
        
        metrics = calculator._calculate_metrics(
            current_balances=current,
            historical_balances=historical,
            weth_balances={addr: 0 for addr in current},
            steth_balances={addr: 0 for addr in current},
            steth_rate=Decimal('1.0'),
            token_symbol="ETH",
            whale_count=10,
            current_block=20000000,
            historical_block=19993000
        )
        
        # Should detect anomaly
        assert metrics.is_anomaly is True
        assert metrics.top_anomaly_driver == "0xWhaleOutlier"
        assert metrics.mad_threshold > Decimal('0')


class TestLSTIntegrationEdgeCases:
    """Test edge cases for LST integration."""
    
    @pytest.mark.asyncio
    async def test_zero_historical_balances(self, calculator):
        """Test handling of whales with zero historical balance (new whales)."""
        current = {"0xNewWhale": 100_000_000_000_000_000_000}
        historical = {"0xNewWhale": 0}  # New whale
        
        metrics = calculator._calculate_metrics(
            current_balances=current,
            historical_balances=historical,
            weth_balances={"0xNewWhale": 0},
            steth_balances={"0xNewWhale": 0},
            steth_rate=Decimal('1.0'),
            token_symbol="ETH",
            whale_count=1,
            current_block=20000000,
            historical_block=19993000
        )
        
        # Should handle gracefully (score = 0 when dividing by 0)
        assert metrics.accumulation_score == Decimal('0')
        assert metrics.accumulators_count == 1
        
        # CRITICAL: Verify no DivisionByZeroError occurred
        # If we got here without exception, the protection works!
        assert metrics.lst_adjusted_score == Decimal('0')  # LST score also protected
    
    @pytest.mark.asyncio
    async def test_steth_depeg_scenario(self, calculator):
        """Test LST aggregation during stETH depeg (rate < 1.0)."""
        current = {"0xWhale1": 100_000_000_000_000_000_000}  # 100 ETH
        historical = {"0xWhale1": 100_000_000_000_000_000_000}
        weth = {"0xWhale1": 0}
        steth = {"0xWhale1": 50_000_000_000_000_000_000}  # 50 stETH
        
        # Crisis: stETH trading at 0.92 (8% depeg)
        steth_rate_depeg = Decimal('0.92')
        
        metrics = calculator._calculate_metrics(
            current_balances=current,
            historical_balances=historical,
            weth_balances=weth,
            steth_balances=steth,
            steth_rate=steth_rate_depeg,
            token_symbol="ETH",
            whale_count=1,
            current_block=20000000,
            historical_block=19993000
        )
        
        # Check stETH value is discounted
        assert metrics.steth_eth_rate == Decimal('0.92')
        # 50 stETH * 0.92 = 46 ETH equivalent
        assert metrics.total_steth_balance_eth == Decimal('50.0') * Decimal('0.92')
    
    @pytest.mark.asyncio
    async def test_different_lookback_windows(self, mock_dependencies):
        """Test calculator with different lookback windows (24h, 48h, 72h)."""
        # Test 24h lookback
        calc_24h = AccumulationScoreCalculator(**mock_dependencies, lookback_hours=24)
        assert calc_24h.lookback_hours == 24
        
        # Test 48h lookback (for Bullish Divergence detection)
        calc_48h = AccumulationScoreCalculator(**mock_dependencies, lookback_hours=48)
        assert calc_48h.lookback_hours == 48
        
        # Test 72h lookback (extended window)
        calc_72h = AccumulationScoreCalculator(**mock_dependencies, lookback_hours=72)
        assert calc_72h.lookback_hours == 72
        
        # Run calculation with 48h window
        result_48h = await calc_48h.calculate_accumulation_score(
            token_symbol="ETH",
            whale_limit=10,
            network="ethereum"
        )
        
        # Check lookback_hours is stored correctly
        assert result_48h.lookback_hours == 48
