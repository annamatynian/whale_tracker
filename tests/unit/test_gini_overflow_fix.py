"""
Test for Gini Coefficient Decimal Overflow Fix (GEMINI FIX #8)

Validates that Gini calculation handles large Wei values without overflow.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock

from src.analyzers.accumulation_score_calculator import AccumulationScoreCalculator


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


class TestGiniOverflowFix:
    """Test Gini coefficient calculation with extreme values."""
    
    def test_gini_with_extreme_wei_values(self, calculator):
        """
        GEMINI FIX #8: Gini calculation should handle 10^24 Wei without overflow.
        
        Scenario: Top 1000 whales with balances up to 1M ETH (10^24 Wei)
        OLD: cumsum = sum(i * balance_wei) reaches 10^30 → potential overflow
        NEW: Normalize to ETH first → cumsum reaches 10^12 (safe)
        """
        # Arrange: 1000 whales with realistic distribution
        # Top whale: 1,000,000 ETH = 10^24 Wei
        # Median: 100,000 ETH = 10^23 Wei
        # Bottom: 10,000 ETH = 10^22 Wei
        
        # Create addresses
        addresses = [f"0x{i:040x}" for i in range(1000)]
        
        # Create extreme balances (in Wei)
        current_balances = {}
        historical_balances = {}
        
        for i, addr in enumerate(addresses):
            # Power law distribution (realistic for crypto)
            # Top whales: 1M ETH, decreasing to 10k ETH
            balance_eth = 1_000_000 / (i + 1)**0.5
            balance_wei = int(balance_eth * 10**18)
            
            current_balances[addr] = balance_wei
            historical_balances[addr] = balance_wei  # Same (no change)
        
        # Empty LST balances (focus on native ETH)
        weth_balances = {addr: 0 for addr in addresses}
        steth_balances = {addr: 0 for addr in addresses}
        
        # Act: Calculate metrics (should NOT overflow)
        metrics = calculator._calculate_metrics(
            current_balances=current_balances,
            historical_balances=historical_balances,
            weth_balances=weth_balances,
            steth_balances=steth_balances,
            steth_rate=Decimal("1.0"),
            lst_migration_count=0,
            looping_suspect_count=0,
            price_change_48h_pct=None,
            token_symbol="ETH",
            whale_count=1000,
            current_block=12345,
            historical_block=12000
        )
        
        # Assert: Gini coefficient calculated successfully
        assert metrics.concentration_gini >= 0
        assert metrics.concentration_gini <= 1
        assert metrics.num_signals_used == 1000
        
        # Expect moderate Gini (realistic power law distribution)
        # WHY: 1000 whales with sqrt decay gives Gini ≈ 0.32 (empirically verified)
        assert metrics.concentration_gini > Decimal("0.2"), \
            f"Power law distribution should produce Gini > 0.2, got {metrics.concentration_gini}"
        assert metrics.concentration_gini < Decimal("0.5"), \
            f"Realistic distribution should have Gini < 0.5, got {metrics.concentration_gini}"
    
    def test_gini_result_unchanged_by_normalization(self, calculator):
        """
        Verify that normalizing to ETH doesn't change Gini result.
        
        Mathematical proof: Gini is dimensionless (ratio of ratios)
        G = (2 * sum(i * x_i)) / (n * sum(x_i)) - (n+1)/n
        
        If x_i → x_i / k (normalize by constant k):
        G' = (2 * sum(i * x_i/k)) / (n * sum(x_i/k)) - (n+1)/n
           = (2 * sum(i * x_i) / k) / (n * sum(x_i) / k) - (n+1)/n
           = (2 * sum(i * x_i)) / (n * sum(x_i)) - (n+1)/n = G
        """
        # Arrange: Small test set with known Gini
        addresses = [f"0x{i:040x}" for i in range(5)]
        
        # Perfect inequality: [1, 2, 3, 4, 5] ETH
        # Gini ≈ 0.26667 (known value)
        balances_wei = {
            addresses[0]: 1 * 10**18,  # 1 ETH
            addresses[1]: 2 * 10**18,  # 2 ETH
            addresses[2]: 3 * 10**18,  # 3 ETH
            addresses[3]: 4 * 10**18,  # 4 ETH
            addresses[4]: 5 * 10**18   # 5 ETH
        }
        
        # Empty LST
        weth_balances = {addr: 0 for addr in addresses}
        steth_balances = {addr: 0 for addr in addresses}
        
        # Act
        metrics = calculator._calculate_metrics(
            current_balances=balances_wei,
            historical_balances=balances_wei,
            weth_balances=weth_balances,
            steth_balances=steth_balances,
            steth_rate=Decimal("1.0"),
            lst_migration_count=0,
            looping_suspect_count=0,
            price_change_48h_pct=None,
            token_symbol="ETH",
            whale_count=5,
            current_block=12345,
            historical_block=12000
        )
        
        # Assert: Gini matches expected value (±0.01 tolerance)
        expected_gini = Decimal("0.26667")
        assert abs(metrics.concentration_gini - expected_gini) < Decimal("0.01"), \
            f"Expected Gini ≈ {expected_gini}, got {metrics.concentration_gini}"
    
    def test_gini_perfect_equality(self, calculator):
        """Gini = 0 for perfectly equal distribution."""
        # Arrange: All whales have exactly 100 ETH
        addresses = [f"0x{i:040x}" for i in range(100)]
        
        balances_wei = {addr: 100 * 10**18 for addr in addresses}
        weth_balances = {addr: 0 for addr in addresses}
        steth_balances = {addr: 0 for addr in addresses}
        
        # Act
        metrics = calculator._calculate_metrics(
            current_balances=balances_wei,
            historical_balances=balances_wei,
            weth_balances=weth_balances,
            steth_balances=steth_balances,
            steth_rate=Decimal("1.0"),
            lst_migration_count=0,
            looping_suspect_count=0,
            price_change_48h_pct=None,
            token_symbol="ETH",
            whale_count=100,
            current_block=12345,
            historical_block=12000
        )
        
        # Assert: Gini ≈ 0 (perfect equality)
        assert metrics.concentration_gini < Decimal("0.01"), \
            f"Perfect equality should give Gini ≈ 0, got {metrics.concentration_gini}"
    
    def test_gini_perfect_inequality(self, calculator):
        """Gini → 1 for maximum inequality (one whale has everything)."""
        # Arrange: One whale has 1M ETH, others have 1 ETH
        addresses = [f"0x{i:040x}" for i in range(100)]
        
        balances_wei = {}
        for i, addr in enumerate(addresses):
            if i == 0:
                balances_wei[addr] = 1_000_000 * 10**18  # Mega whale
            else:
                balances_wei[addr] = 1 * 10**18  # Tiny whales
        
        weth_balances = {addr: 0 for addr in addresses}
        steth_balances = {addr: 0 for addr in addresses}
        
        # Act
        metrics = calculator._calculate_metrics(
            current_balances=balances_wei,
            historical_balances=balances_wei,
            weth_balances=weth_balances,
            steth_balances=steth_balances,
            steth_rate=Decimal("1.0"),
            lst_migration_count=0,
            looping_suspect_count=0,
            price_change_48h_pct=None,
            token_symbol="ETH",
            whale_count=100,
            current_block=12345,
            historical_block=12000
        )
        
        # Assert: Gini → 1 (extreme inequality)
        assert metrics.concentration_gini > Decimal("0.95"), \
            f"Extreme inequality should give Gini > 0.95, got {metrics.concentration_gini}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
