"""
Tests for Gemini Looping Defense Fixes (Phase 2)

Validates 3 critical anti-looping measures:
1. MAD Filter: stETH-dominated signals → [Technical Activity]
2. Depeg Risk: stETH < 0.98 → downgrade High Conviction
3. Looping Detection: >10% whales with >100 ETH LSTs → flag
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from src.analyzers.accumulation_score_calculator import AccumulationScoreCalculator
from src.schemas.accumulation_schemas import AccumulationMetricCreate


@pytest.fixture
def mock_dependencies():
    """Create mocked dependencies for AccumulationScoreCalculator."""
    whale_provider = AsyncMock()
    multicall_client = AsyncMock()
    repository = AsyncMock()
    snapshot_repo = AsyncMock()
    price_provider = AsyncMock()
    
    return {
        'whale_provider': whale_provider,
        'multicall_client': multicall_client,
        'repository': repository,
        'snapshot_repo': snapshot_repo,
        'price_provider': price_provider
    }


@pytest.fixture
def calculator(mock_dependencies):
    """Create AccumulationScoreCalculator instance."""
    return AccumulationScoreCalculator(
        whale_provider=mock_dependencies['whale_provider'],
        multicall_client=mock_dependencies['multicall_client'],
        repository=mock_dependencies['repository'],
        snapshot_repo=mock_dependencies['snapshot_repo'],
        price_provider=mock_dependencies['price_provider'],
        lookback_hours=24
    )


class TestMADFilterForStETH:
    """Test MAD Filter - stETH-dominated signals should be tagged as Technical Activity."""
    
    def test_high_steth_dominance_triggers_technical_activity_tag(self, calculator):
        """GEMINI FIX 1: When stETH dominates (>70%), tag as [Technical Activity] not [High Conviction]."""
        # Arrange: Create metric with stETH-dominated change
        metric = AccumulationMetricCreate(
            token_symbol="ETH",
            whale_count=100,
            total_balance_current_wei="100000000000000000000",
            total_balance_historical_wei="90000000000000000000",
            total_balance_change_wei="10000000000000000000",
            total_balance_current_eth=Decimal("100"),
            total_balance_historical_eth=Decimal("90"),
            total_balance_change_eth=Decimal("10"),  # Total change: 10 ETH
            accumulation_score=Decimal("11.11"),
            
            # LST-adjusted metrics (stETH dominates!)
            total_weth_balance_eth=Decimal("5"),
            total_steth_balance_eth=Decimal("8"),  # 8 ETH in stETH (80% of 10 ETH change!)
            lst_adjusted_score=Decimal("12.5"),
            lst_migration_count=0,
            steth_eth_rate=Decimal("1.0"),
            
            # MAD threshold (score exceeds 3×MAD)
            mad_threshold=Decimal("2.0"),  # 3×MAD = 6.0, score 12.5 > 6.0 ✓
            is_anomaly=False,
            
            # Quality metrics
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
        
        # Act: Assign tags
        tags = calculator._assign_tags(metric, whale_count=100, looping_suspect_count=0)
        
        # Assert: Should have [Technical Activity] NOT [High Conviction]
        assert "Technical Activity" in tags, "Should flag stETH-dominated signal as technical"
        assert "High Conviction" not in tags, "Should NOT give High Conviction to stETH looping"
    
    def test_low_steth_dominance_allows_high_conviction(self, calculator):
        """When stETH is <70% of change, normal [High Conviction] tag applies."""
        # Arrange: stETH is only 30% of total change
        metric = AccumulationMetricCreate(
            token_symbol="ETH",
            whale_count=100,
            total_balance_current_wei="100000000000000000000",
            total_balance_historical_wei="90000000000000000000",
            total_balance_change_wei="10000000000000000000",
            total_balance_current_eth=Decimal("100"),
            total_balance_historical_eth=Decimal("90"),
            total_balance_change_eth=Decimal("10"),  # Total change: 10 ETH
            accumulation_score=Decimal("11.11"),
            
            # LST-adjusted (stETH only 3 ETH = 30%)
            total_weth_balance_eth=Decimal("2"),
            total_steth_balance_eth=Decimal("3"),  # Only 30% of 10 ETH
            lst_adjusted_score=Decimal("12.5"),
            lst_migration_count=0,
            steth_eth_rate=Decimal("1.0"),
            
            # MAD threshold
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
        
        # Act
        tags = calculator._assign_tags(metric, whale_count=100, looping_suspect_count=0)
        
        # Assert: Normal High Conviction applies
        assert "High Conviction" in tags, "Should allow High Conviction when stETH <70%"
        assert "Technical Activity" not in tags, "No technical tag for normal accumulation"


class TestDepegRiskDowngrade:
    """Test Depeg Risk - stETH < 0.98 should downgrade High Conviction."""
    
    def test_depeg_removes_high_conviction_tag(self, calculator):
        """GEMINI FIX 2: Depeg (stETH < 0.98) removes High Conviction to avoid margin call false signals."""
        # Arrange: Metric that WOULD get High Conviction, but depeg active
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
            
            # LST metrics
            total_weth_balance_eth=Decimal("2"),
            total_steth_balance_eth=Decimal("3"),  # Low stETH dominance
            lst_adjusted_score=Decimal("12.5"),
            lst_migration_count=0,
            steth_eth_rate=Decimal("0.97"),  # ❌ DEPEG! < 0.98
            
            # MAD threshold (would trigger High Conviction normally)
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
        
        # Act
        tags = calculator._assign_tags(metric, whale_count=100, looping_suspect_count=0)
        
        # Assert: Depeg prevents High Conviction
        assert "Depeg Risk" in tags, "Should detect depeg"
        assert "High Conviction" not in tags, "Depeg should remove High Conviction"
    
    def test_healthy_steth_rate_allows_high_conviction(self, calculator):
        """When stETH rate is healthy (≥0.98), High Conviction can be assigned."""
        # Arrange: Same as above but healthy rate
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
            steth_eth_rate=Decimal("0.999"),  # ✅ Healthy rate
            
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
        
        # Act
        tags = calculator._assign_tags(metric, whale_count=100, looping_suspect_count=0)
        
        # Assert: No depeg, High Conviction allowed
        assert "High Conviction" in tags, "Healthy rate allows High Conviction"
        assert "Depeg Risk" not in tags, "No depeg risk at 0.999 rate"


class TestLoopingPatternDetection:
    """Test Looping Detection - high LST concentration should trigger Technical Activity tag."""
    
    @pytest.mark.asyncio
    async def test_detect_high_lst_concentration(self, calculator):
        """GEMINI FIX 3: Detect addresses with >100 ETH in LSTs as looping suspects."""
        # Arrange: 15 out of 100 whales have >100 ETH in LSTs
        addresses = [f"0x{i:040x}" for i in range(100)]
        
        weth_balances = {}
        steth_balances = {}
        
        # First 15 addresses: 60 ETH WETH + 50 ETH stETH = 110 ETH total (>100 threshold)
        for i in range(15):
            addr = addresses[i]
            weth_balances[addr] = int(Decimal("60") * Decimal("1e18"))  # 60 WETH
            steth_balances[addr] = int(Decimal("50") * Decimal("1e18"))  # 50 stETH
        
        # Rest: Small LST holdings
        for i in range(15, 100):
            addr = addresses[i]
            weth_balances[addr] = int(Decimal("5") * Decimal("1e18"))
            steth_balances[addr] = int(Decimal("3") * Decimal("1e18"))
        
        # Act
        looping_count = await calculator._detect_looping_pattern(
            addresses=addresses,
            weth_balances=weth_balances,
            steth_balances=steth_balances
        )
        
        # Assert
        assert looping_count == 15, "Should detect 15 looping suspects"
    
    def test_high_looping_suspect_count_triggers_tag(self, calculator):
        """When >10% of whales are looping suspects, add [Technical Activity] tag."""
        # Arrange
        metric = AccumulationMetricCreate(
            token_symbol="ETH",
            whale_count=100,
            total_balance_current_wei="100000000000000000000",
            total_balance_historical_wei="90000000000000000000",
            total_balance_change_wei="10000000000000000000",
            total_balance_current_eth=Decimal("100"),
            total_balance_historical_eth=Decimal("90"),
            total_balance_change_eth=Decimal("10"),
            accumulation_score=Decimal("5.0"),
            
            total_weth_balance_eth=Decimal("2"),
            total_steth_balance_eth=Decimal("3"),
            lst_adjusted_score=Decimal("6.0"),
            lst_migration_count=0,
            steth_eth_rate=Decimal("1.0"),
            
            mad_threshold=Decimal("10.0"),  # No MAD anomaly
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
        
        # Act: 15 looping suspects (15% > 10% threshold)
        tags = calculator._assign_tags(metric, whale_count=100, looping_suspect_count=15)
        
        # Assert
        assert "Technical Activity" in tags, "Should flag high looping concentration"
    
    def test_low_looping_suspect_count_no_tag(self, calculator):
        """When ≤10% of whales are suspects, no automatic Technical Activity tag."""
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
            accumulation_score=Decimal("5.0"),
            
            total_weth_balance_eth=Decimal("2"),
            total_steth_balance_eth=Decimal("3"),
            lst_adjusted_score=Decimal("6.0"),
            lst_migration_count=0,
            steth_eth_rate=Decimal("1.0"),
            
            mad_threshold=Decimal("10.0"),
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
        
        # Act: Only 8 suspects (8% ≤ 10%)
        tags = calculator._assign_tags(metric, whale_count=100, looping_suspect_count=8)
        
        # Assert
        assert "Technical Activity" not in tags, "Low concentration shouldn't trigger tag"


class TestCombinedScenarios:
    """Test combined fixes working together."""
    
    def test_all_three_fixes_together(self, calculator):
        """Comprehensive test: stETH dominance + depeg + high LST concentration."""
        # Arrange: The worst case - all 3 conditions active
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
            
            # ❌ Condition 1: stETH dominance (80%)
            total_weth_balance_eth=Decimal("2"),
            total_steth_balance_eth=Decimal("8"),  # 80% of change!
            lst_adjusted_score=Decimal("12.5"),
            lst_migration_count=0,
            
            # ❌ Condition 2: Depeg
            steth_eth_rate=Decimal("0.96"),  # Severe depeg
            
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
        
        # Act: ❌ Condition 3: High looping (20% of whales)
        tags = calculator._assign_tags(metric, whale_count=100, looping_suspect_count=20)
        
        # Assert: All defensive tags applied
        assert "Technical Activity" in tags, "stETH dominance + high LST → Technical Activity"
        assert "Depeg Risk" in tags, "Depeg detected"
        assert "High Conviction" not in tags, "ALL 3 conditions prevent High Conviction"
        
        # Count total defensive tags
        defensive_tags = [t for t in tags if t in ["Technical Activity", "Depeg Risk"]]
        assert len(defensive_tags) == 2, "Both defensive tags should be present"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
