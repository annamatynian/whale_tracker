"""
Unit Tests for AccumulationScoreCalculator - LST Correction

Tests LST aggregation, MAD detection, Gini index, and smart tags.

Run: pytest tests/unit/test_accumulation_calculator_lst.py -v
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, AsyncMock
from datetime import datetime, UTC

from src.analyzers.accumulation_score_calculator import AccumulationScoreCalculator


@pytest.fixture
def mock_dependencies():
    """Create mocked dependencies."""
    whale_provider = Mock()
    multicall_client = Mock()
    repository = Mock()
    snapshot_repo = Mock()
    price_provider = Mock()
    
    return {
        'whale_provider': whale_provider,
        'multicall_client': multicall_client,
        'repository': repository,
        'snapshot_repo': snapshot_repo,
        'price_provider': price_provider
    }


@pytest.fixture
def calculator(mock_dependencies):
    """Create calculator instance with mocked dependencies."""
    return AccumulationScoreCalculator(**mock_dependencies)


class TestSmartTags:
    """Test smart tags assignment."""
    
    def test_tag_organic_accumulation(self, calculator):
        """Test [Organic Accumulation] tag when 25%+ whales accumulating."""
        from src.schemas.accumulation_schemas import AccumulationMetricCreate
        
        metric = AccumulationMetricCreate(
            token_symbol="ETH",
            whale_count=100,
            accumulators_count=30,  # 30% accumulating
            distributors_count=20,
            neutral_count=50,
            total_balance_current_wei="1000000000000000000",
            total_balance_historical_wei="900000000000000000",
            total_balance_change_wei="100000000000000000",
            total_balance_current_eth=Decimal('1.0'),
            total_balance_historical_eth=Decimal('0.9'),
            total_balance_change_eth=Decimal('0.1'),
            accumulation_score=Decimal('11.1'),
            concentration_gini=Decimal('0.5'),
            is_anomaly=False,
            current_block_number=20000000,
            historical_block_number=19993000,
            lookback_hours=24
        )
        
        tags = calculator._assign_tags(metric, whale_count=100)
        
        assert "Organic Accumulation" in tags
    
    def test_tag_concentrated_signal(self, calculator):
        """Test [Concentrated Signal] tag when Gini > 0.85."""
        from src.schemas.accumulation_schemas import AccumulationMetricCreate
        
        metric = AccumulationMetricCreate(
            token_symbol="ETH",
            whale_count=100,
            accumulators_count=10,
            distributors_count=5,
            neutral_count=85,
            total_balance_current_wei="1000000000000000000",
            total_balance_historical_wei="900000000000000000",
            total_balance_change_wei="100000000000000000",
            total_balance_current_eth=Decimal('1.0'),
            total_balance_historical_eth=Decimal('0.9'),
            total_balance_change_eth=Decimal('0.1'),
            accumulation_score=Decimal('11.1'),
            concentration_gini=Decimal('0.87'),  # High concentration
            is_anomaly=False,
            current_block_number=20000000,
            historical_block_number=19993000,
            lookback_hours=24
        )
        
        tags = calculator._assign_tags(metric, whale_count=100)
        
        assert "Concentrated Signal" in tags
    
    def test_tag_bullish_divergence(self, calculator):
        """Test [Bullish Divergence] tag: +score during -price."""
        from src.schemas.accumulation_schemas import AccumulationMetricCreate
        
        metric = AccumulationMetricCreate(
            token_symbol="ETH",
            whale_count=100,
            accumulators_count=40,
            distributors_count=10,
            neutral_count=50,
            total_balance_current_wei="1000000000000000000",
            total_balance_historical_wei="900000000000000000",
            total_balance_change_wei="100000000000000000",
            total_balance_current_eth=Decimal('1.0'),
            total_balance_historical_eth=Decimal('0.9'),
            total_balance_change_eth=Decimal('0.1'),
            accumulation_score=Decimal('11.1'),
            lst_adjusted_score=Decimal('0.5'),  # +0.5% accumulation
            price_change_48h_pct=Decimal('-3.2'),  # -3.2% price drop
            concentration_gini=Decimal('0.5'),
            is_anomaly=False,
            current_block_number=20000000,
            historical_block_number=19993000,
            lookback_hours=24
        )
        
        tags = calculator._assign_tags(metric, whale_count=100)
        
        assert "Bullish Divergence" in tags
    
    def test_tag_anomaly_alert(self, calculator):
        """Test [Anomaly Alert] tag when is_anomaly=True."""
        from src.schemas.accumulation_schemas import AccumulationMetricCreate
        
        metric = AccumulationMetricCreate(
            token_symbol="ETH",
            whale_count=100,
            accumulators_count=1,
            distributors_count=0,
            neutral_count=99,
            total_balance_current_wei="1000000000000000000",
            total_balance_historical_wei="900000000000000000",
            total_balance_change_wei="100000000000000000",
            total_balance_current_eth=Decimal('1.0'),
            total_balance_historical_eth=Decimal('0.9'),
            total_balance_change_eth=Decimal('0.1'),
            accumulation_score=Decimal('50.0'),  # Huge score
            concentration_gini=Decimal('0.95'),
            is_anomaly=True,  # Outlier detected
            top_anomaly_driver="0xWhaleOutlier...",
            current_block_number=20000000,
            historical_block_number=19993000,
            lookback_hours=24
        )
        
        tags = calculator._assign_tags(metric, whale_count=100)
        
        assert "Anomaly Alert" in tags


class TestLSTMigrationDetection:
    """Test LST migration detection logic."""
    
    @pytest.mark.asyncio
    async def test_detect_migration_eth_to_steth(self, calculator):
        """Test detection when whale moves ETH → stETH."""
        addresses = ["0xWhale1"]
        
        # Historical: 100 ETH, 0 stETH
        # Current: 95 ETH, 5 stETH (gas cost: 0.01 ETH)
        # Net change ≈ 0 → Migration detected
        
        eth_current = {"0xWhale1": 95 * 10**18}
        eth_historical = {"0xWhale1": 100 * 10**18}
        weth_current = {"0xWhale1": 0}
        steth_current = {"0xWhale1": int(5.01 * 10**18)}  # 5.01 stETH (covers gas)
        steth_rate = Decimal('0.998')
        
        count = await calculator._detect_lst_migration(
            addresses=addresses,
            eth_current=eth_current,
            eth_historical=eth_historical,
            weth_current=weth_current,
            steth_current=steth_current,
            steth_rate=steth_rate
        )
        
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_no_migration_real_dump(self, calculator):
        """Test NO detection when whale actually dumps (not migrating)."""
        addresses = ["0xWhale1"]
        
        # Historical: 100 ETH, 0 stETH
        # Current: 50 ETH, 0 stETH
        # Net change = -50 ETH → Real dump, not migration
        
        eth_current = {"0xWhale1": 50 * 10**18}
        eth_historical = {"0xWhale1": 100 * 10**18}
        weth_current = {"0xWhale1": 0}
        steth_current = {"0xWhale1": 0}
        steth_rate = Decimal('0.998')
        
        count = await calculator._detect_lst_migration(
            addresses=addresses,
            eth_current=eth_current,
            eth_historical=eth_historical,
            weth_current=weth_current,
            steth_current=steth_current,
            steth_rate=steth_rate
        )
        
        assert count == 0  # Not a migration
