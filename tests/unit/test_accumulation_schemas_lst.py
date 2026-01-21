"""
Unit Tests for AccumulationMetricCreate - LST Fields

Tests Pydantic validation for new LST correction fields.

Run: pytest tests/unit/test_accumulation_schemas_lst.py -v
"""

import pytest
from decimal import Decimal
from src.schemas.accumulation_schemas import AccumulationMetricCreate


class TestLSTFieldsValidation:
    """Test LST field validation rules."""
    
    def test_create_metric_with_lst_fields(self):
        """Test creating metric with all LST fields populated."""
        metric = AccumulationMetricCreate(
            token_symbol="ETH",
            whale_count=100,
            total_balance_current_wei="1000000000000000000",
            total_balance_historical_wei="900000000000000000",
            total_balance_change_wei="100000000000000000",
            total_balance_current_eth=Decimal('1.0'),
            total_balance_historical_eth=Decimal('0.9'),
            total_balance_change_eth=Decimal('0.1'),
            accumulation_score=Decimal('11.1'),
            accumulators_count=30,
            distributors_count=20,
            neutral_count=50,
            current_block_number=20000000,
            historical_block_number=19993000,
            lookback_hours=24,
            # LST fields
            total_weth_balance_eth=Decimal('5.5'),
            total_steth_balance_eth=Decimal('10.2'),
            lst_adjusted_score=Decimal('12.5'),
            lst_migration_count=3,
            steth_eth_rate=Decimal('0.9985'),
            tags=["Organic Accumulation", "High Conviction"],
            concentration_gini=Decimal('0.65'),
            is_anomaly=False,
            mad_threshold=Decimal('2.5'),
            top_anomaly_driver=None,
            price_change_48h_pct=Decimal('-1.5')
        )
        
        assert metric.total_weth_balance_eth == Decimal('5.5')
        assert metric.total_steth_balance_eth == Decimal('10.2')
        assert metric.lst_adjusted_score == Decimal('12.5')
        assert metric.lst_migration_count == 3
        assert metric.steth_eth_rate == Decimal('0.9985')
        assert len(metric.tags) == 2
        assert "Organic Accumulation" in metric.tags
        assert metric.concentration_gini == Decimal('0.65')
        assert metric.is_anomaly is False
    
    def test_create_metric_without_lst_fields(self):
        """Test backward compatibility - metric without LST fields."""
        metric = AccumulationMetricCreate(
            token_symbol="ETH",
            whale_count=50,
            total_balance_current_wei="500000000000000000",
            total_balance_historical_wei="450000000000000000",
            total_balance_change_wei="50000000000000000",
            total_balance_current_eth=Decimal('0.5'),
            total_balance_historical_eth=Decimal('0.45'),
            total_balance_change_eth=Decimal('0.05'),
            accumulation_score=Decimal('11.1'),
            accumulators_count=15,
            distributors_count=10,
            neutral_count=25,
            current_block_number=20000000,
            historical_block_number=19993000,
            lookback_hours=24
            # NO LST fields - should use defaults
        )
        
        # Check defaults
        assert metric.total_weth_balance_eth is None
        assert metric.total_steth_balance_eth is None
        assert metric.lst_adjusted_score is None
        assert metric.lst_migration_count == 0
        assert metric.steth_eth_rate is None
        assert metric.tags == []
        assert metric.concentration_gini is None
        assert metric.is_anomaly is False
    
    def test_steth_rate_crisis_scenario(self):
        """Test stETH rate accepts crisis values (0.90-1.10 range)."""
        # Crisis: stETH depeg to 0.92
        metric = AccumulationMetricCreate(
            token_symbol="ETH",
            whale_count=10,
            total_balance_current_wei="100000000000000000",
            total_balance_historical_wei="100000000000000000",
            total_balance_change_wei="0",
            total_balance_current_eth=Decimal('0.1'),
            total_balance_historical_eth=Decimal('0.1'),
            total_balance_change_eth=Decimal('0'),
            accumulation_score=Decimal('0'),
            accumulators_count=0,
            distributors_count=0,
            neutral_count=10,
            current_block_number=20000000,
            historical_block_number=19993000,
            lookback_hours=24,
            steth_eth_rate=Decimal('0.92')  # Crisis scenario
        )
        
        assert metric.steth_eth_rate == Decimal('0.92')
    
    def test_steth_rate_rejects_invalid(self):
        """Test stETH rate rejects values outside 0.90-1.10 range."""
        with pytest.raises(ValueError):
            AccumulationMetricCreate(
                token_symbol="ETH",
                whale_count=10,
                total_balance_current_wei="100000000000000000",
                total_balance_historical_wei="100000000000000000",
                total_balance_change_wei="0",
                total_balance_current_eth=Decimal('0.1'),
                total_balance_historical_eth=Decimal('0.1'),
                total_balance_change_eth=Decimal('0'),
                accumulation_score=Decimal('0'),
                accumulators_count=0,
                distributors_count=0,
                neutral_count=10,
                current_block_number=20000000,
                historical_block_number=19993000,
                lookback_hours=24,
                steth_eth_rate=Decimal('0.85')  # Too low
            )
    
    def test_gini_coefficient_bounds(self):
        """Test Gini coefficient accepts only 0.0-1.0 range."""
        # Valid: 0.0 (perfect equality)
        metric1 = AccumulationMetricCreate(
            token_symbol="ETH",
            whale_count=10,
            total_balance_current_wei="100000000000000000",
            total_balance_historical_wei="100000000000000000",
            total_balance_change_wei="0",
            total_balance_current_eth=Decimal('0.1'),
            total_balance_historical_eth=Decimal('0.1'),
            total_balance_change_eth=Decimal('0'),
            accumulation_score=Decimal('0'),
            accumulators_count=0,
            distributors_count=0,
            neutral_count=10,
            current_block_number=20000000,
            historical_block_number=19993000,
            lookback_hours=24,
            concentration_gini=Decimal('0.0')
        )
        assert metric1.concentration_gini == Decimal('0.0')
        
        # Valid: 1.0 (perfect inequality)
        metric2 = AccumulationMetricCreate(
            token_symbol="ETH",
            whale_count=10,
            total_balance_current_wei="100000000000000000",
            total_balance_historical_wei="100000000000000000",
            total_balance_change_wei="0",
            total_balance_current_eth=Decimal('0.1'),
            total_balance_historical_eth=Decimal('0.1'),
            total_balance_change_eth=Decimal('0'),
            accumulation_score=Decimal('0'),
            accumulators_count=0,
            distributors_count=0,
            neutral_count=10,
            current_block_number=20000000,
            historical_block_number=19993000,
            lookback_hours=24,
            concentration_gini=Decimal('1.0')
        )
        assert metric2.concentration_gini == Decimal('1.0')
        
        # Invalid: > 1.0
        with pytest.raises(ValueError):
            AccumulationMetricCreate(
                token_symbol="ETH",
                whale_count=10,
                total_balance_current_wei="100000000000000000",
                total_balance_historical_wei="100000000000000000",
                total_balance_change_wei="0",
                total_balance_current_eth=Decimal('0.1'),
                total_balance_historical_eth=Decimal('0.1'),
                total_balance_change_eth=Decimal('0'),
                accumulation_score=Decimal('0'),
                accumulators_count=0,
                distributors_count=0,
                neutral_count=10,
                current_block_number=20000000,
                historical_block_number=19993000,
                lookback_hours=24,
                concentration_gini=Decimal('1.5')  # Invalid
            )
    
    def test_tags_list_functionality(self):
        """Test tags field accepts list of strings."""
        metric = AccumulationMetricCreate(
            token_symbol="ETH",
            whale_count=10,
            total_balance_current_wei="100000000000000000",
            total_balance_historical_wei="100000000000000000",
            total_balance_change_wei="0",
            total_balance_current_eth=Decimal('0.1'),
            total_balance_historical_eth=Decimal('0.1'),
            total_balance_change_eth=Decimal('0'),
            accumulation_score=Decimal('0'),
            accumulators_count=0,
            distributors_count=0,
            neutral_count=10,
            current_block_number=20000000,
            historical_block_number=19993000,
            lookback_hours=24,
            tags=["Organic Accumulation", "Bullish Divergence", "LST Migration"]
        )
        
        assert len(metric.tags) == 3
        assert "Bullish Divergence" in metric.tags
        assert isinstance(metric.tags, list)
