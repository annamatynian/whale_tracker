"""
Unit Tests for Whale Analyzer
===============================

Tests for statistical analysis and anomaly detection.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from src.analyzers.whale_analyzer import (
    WhaleAnalyzer,
    TransactionStats,
    AnomalyResult,
    get_analyzer
)


class TestWhaleAnalyzerInitialization:
    """Test WhaleAnalyzer initialization."""

    def test_default_initialization(self):
        """Test WhaleAnalyzer with default parameters."""
        analyzer = WhaleAnalyzer()

        assert analyzer.anomaly_multiplier == 1.3
        assert analyzer.rolling_window_size == 10
        assert analyzer.min_history_required == 5
        assert len(analyzer.transaction_history) == 0

    def test_custom_initialization(self):
        """Test WhaleAnalyzer with custom parameters."""
        analyzer = WhaleAnalyzer(
            anomaly_multiplier=1.5,
            rolling_window_size=20,
            min_history_required=10
        )

        assert analyzer.anomaly_multiplier == 1.5
        assert analyzer.rolling_window_size == 20
        assert analyzer.min_history_required == 10


class TestTransactionTracking:
    """Test transaction history tracking."""

    def test_add_single_transaction(self):
        """Test adding a single transaction."""
        analyzer = WhaleAnalyzer()
        whale_address = "0x123"

        analyzer.add_transaction(whale_address, 100000.0)

        assert whale_address in analyzer.transaction_history
        assert len(analyzer.transaction_history[whale_address]) == 1
        assert analyzer.transaction_history[whale_address][0] == 100000.0

    def test_add_multiple_transactions(self):
        """Test adding multiple transactions."""
        analyzer = WhaleAnalyzer()
        whale_address = "0x123"

        amounts = [100000.0, 150000.0, 200000.0]
        for amount in amounts:
            analyzer.add_transaction(whale_address, amount)

        assert len(analyzer.transaction_history[whale_address]) == 3
        assert list(analyzer.transaction_history[whale_address]) == amounts

    def test_transaction_with_timestamp(self):
        """Test adding transaction with custom timestamp."""
        analyzer = WhaleAnalyzer()
        whale_address = "0x123"
        timestamp = datetime(2024, 1, 1, 12, 0, 0)

        analyzer.add_transaction(whale_address, 100000.0, timestamp)

        assert whale_address in analyzer.timestamp_history
        assert analyzer.timestamp_history[whale_address][0] == timestamp

    def test_max_history_limit(self):
        """Test that history respects max length."""
        analyzer = WhaleAnalyzer(rolling_window_size=5)
        whale_address = "0x123"

        # Add more transactions than max length (window_size * 3 = 15)
        for i in range(20):
            analyzer.add_transaction(whale_address, float(i * 1000))

        # Should keep only last 15 transactions
        assert len(analyzer.transaction_history[whale_address]) == 15


class TestWhaleStats:
    """Test whale statistics calculation."""

    def test_get_stats_no_history(self):
        """Test getting stats for whale with no history."""
        analyzer = WhaleAnalyzer()

        stats = analyzer.get_whale_stats("0x123")

        assert stats is None

    def test_get_stats_basic(self):
        """Test basic statistics calculation."""
        analyzer = WhaleAnalyzer()
        whale_address = "0x123"

        amounts = [100000.0, 150000.0, 200000.0, 250000.0]
        for amount in amounts:
            analyzer.add_transaction(whale_address, amount)

        stats = analyzer.get_whale_stats(whale_address)

        assert stats is not None
        assert stats.whale_address == whale_address
        assert stats.transaction_count == 4
        assert stats.avg_amount_usd == 175000.0
        assert stats.median_amount_usd == 175000.0
        assert stats.max_amount_usd == 250000.0
        assert stats.min_amount_usd == 100000.0

    def test_get_stats_frequency(self):
        """Test frequency calculation."""
        analyzer = WhaleAnalyzer()
        whale_address = "0x123"

        # Add transactions 1 hour apart
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        for i in range(5):
            timestamp = base_time + timedelta(hours=i)
            analyzer.add_transaction(whale_address, 100000.0, timestamp)

        stats = analyzer.get_whale_stats(whale_address)

        # Average should be 1 hour between transactions
        assert abs(stats.avg_frequency_hours - 1.0) < 0.01


class TestAnomalyDetection:
    """Test anomaly detection logic."""

    def test_anomaly_no_history(self):
        """Test anomaly detection with no history."""
        analyzer = WhaleAnalyzer()

        result = analyzer.detect_anomaly("0x123", 100000.0)

        assert result.is_anomaly == False
        assert result.confidence == 0.0
        assert "No historical data" in result.reason

    def test_anomaly_insufficient_history(self):
        """Test anomaly detection with insufficient history."""
        analyzer = WhaleAnalyzer(min_history_required=5)
        whale_address = "0x123"

        # Add only 3 transactions (less than min required)
        for i in range(3):
            analyzer.add_transaction(whale_address, 100000.0)

        result = analyzer.detect_anomaly(whale_address, 200000.0)

        assert result.is_anomaly == False
        assert "Insufficient history" in result.reason

    def test_anomaly_detected(self):
        """Test anomaly detection when amount exceeds threshold."""
        analyzer = WhaleAnalyzer(anomaly_multiplier=1.3, min_history_required=5)
        whale_address = "0x123"

        # Add consistent history of $100k transactions
        for i in range(10):
            analyzer.add_transaction(whale_address, 100000.0)

        # Test with amount that exceeds threshold (100k * 1.3 = 130k)
        result = analyzer.detect_anomaly(whale_address, 150000.0)

        assert result.is_anomaly == True
        assert result.current_amount == 150000.0
        assert result.average_amount == 100000.0
        assert result.threshold == 130000.0
        assert result.multiplier == 1.3
        assert result.confidence > 50.0

    def test_anomaly_not_detected(self):
        """Test anomaly not detected when amount is within threshold."""
        analyzer = WhaleAnalyzer(anomaly_multiplier=1.3, min_history_required=5)
        whale_address = "0x123"

        # Add consistent history
        for i in range(10):
            analyzer.add_transaction(whale_address, 100000.0)

        # Test with amount below threshold
        result = analyzer.detect_anomaly(whale_address, 120000.0)

        assert result.is_anomaly == False
        assert result.confidence < 50.0

    def test_anomaly_rolling_average(self):
        """Test that anomaly detection uses rolling average."""
        analyzer = WhaleAnalyzer(
            anomaly_multiplier=1.3,
            rolling_window_size=5,
            min_history_required=3
        )
        whale_address = "0x123"

        # Add varying amounts
        amounts = [50000, 100000, 150000, 200000, 250000]
        for amount in amounts:
            analyzer.add_transaction(whale_address, float(amount))

        result = analyzer.detect_anomaly(whale_address, 300000.0)

        # Average of [50k, 100k, 150k, 200k, 250k] = 150k
        # Threshold = 150k * 1.3 = 195k
        # 300k > 195k = anomaly
        assert result.is_anomaly == True


class TestDumpPatternDetection:
    """Test dump pattern detection."""

    def test_dump_pattern_no_transactions(self):
        """Test dump pattern with no transactions."""
        analyzer = WhaleAnalyzer()

        result = analyzer.detect_dump_pattern("0x123", [])

        assert result['is_dump_pattern'] == False
        assert result['confidence'] == 0.0

    def test_dump_pattern_multiple_recent_transactions(self):
        """Test dump pattern detection for frequent transactions."""
        analyzer = WhaleAnalyzer()
        whale_address = "0x123"

        # Create 5 recent transactions within 24 hours
        now = datetime.now()
        recent_transactions = [
            {'timestamp': now - timedelta(hours=i), 'amount_usd': 100000}
            for i in range(5)
        ]

        result = analyzer.detect_dump_pattern(whale_address, recent_transactions)

        # Should detect dump pattern due to frequency
        assert len(result['signals']) > 0
        assert result['score'] > 0

    def test_dump_pattern_exchange_destinations(self):
        """Test dump pattern detection for exchange-bound transactions."""
        analyzer = WhaleAnalyzer()
        whale_address = "0x123"

        # Create transactions, most going to exchanges
        recent_transactions = [
            {'timestamp': datetime.now(), 'amount_usd': 100000, 'is_exchange_destination': True},
            {'timestamp': datetime.now(), 'amount_usd': 100000, 'is_exchange_destination': True},
            {'timestamp': datetime.now(), 'amount_usd': 100000, 'is_exchange_destination': True},
            {'timestamp': datetime.now(), 'amount_usd': 100000, 'is_exchange_destination': False},
        ]

        result = analyzer.detect_dump_pattern(whale_address, recent_transactions)

        # Should detect dump pattern due to exchange ratio (75%)
        assert result['is_dump_pattern'] == True or result['score'] >= 30
        assert any('exchange' in signal.lower() for signal in result['signals'])

    def test_dump_pattern_increasing_amounts(self):
        """Test dump pattern detection for increasing transaction sizes."""
        analyzer = WhaleAnalyzer()
        whale_address = "0x123"

        # Create transactions with increasing amounts
        recent_transactions = [
            {'timestamp': datetime.now(), 'amount_usd': 50000},
            {'timestamp': datetime.now(), 'amount_usd': 100000},
            {'timestamp': datetime.now(), 'amount_usd': 150000},
            {'timestamp': datetime.now(), 'amount_usd': 200000},
        ]

        result = analyzer.detect_dump_pattern(whale_address, recent_transactions)

        # Should detect increasing pattern
        assert result['score'] > 0

    def test_dump_pattern_high_confidence(self):
        """Test dump pattern with multiple signals."""
        analyzer = WhaleAnalyzer()
        whale_address = "0x123"

        # Create scenario with multiple dump signals
        now = datetime.now()
        recent_transactions = [
            {
                'timestamp': now - timedelta(hours=1),
                'amount_usd': 100000,
                'is_exchange_destination': True
            },
            {
                'timestamp': now - timedelta(hours=2),
                'amount_usd': 150000,
                'is_exchange_destination': True
            },
            {
                'timestamp': now - timedelta(hours=3),
                'amount_usd': 200000,
                'is_exchange_destination': True
            },
        ]

        result = analyzer.detect_dump_pattern(whale_address, recent_transactions)

        # Multiple signals should give high score
        assert result['is_dump_pattern'] == True
        assert result['confidence'] >= 50.0


class TestUtilityMethods:
    """Test utility methods."""

    def test_clear_history(self):
        """Test clearing whale history."""
        analyzer = WhaleAnalyzer()
        whale_address = "0x123"

        analyzer.add_transaction(whale_address, 100000.0)
        assert whale_address in analyzer.transaction_history

        analyzer.clear_history(whale_address)
        assert whale_address not in analyzer.transaction_history

    def test_get_all_whale_addresses(self):
        """Test getting all tracked whales."""
        analyzer = WhaleAnalyzer()

        analyzer.add_transaction("0x123", 100000.0)
        analyzer.add_transaction("0x456", 200000.0)

        addresses = analyzer.get_all_whale_addresses()

        assert len(addresses) == 2
        assert "0x123" in addresses
        assert "0x456" in addresses

    def test_export_stats(self):
        """Test exporting statistics for all whales."""
        analyzer = WhaleAnalyzer()

        analyzer.add_transaction("0x123", 100000.0)
        analyzer.add_transaction("0x123", 150000.0)

        stats = analyzer.export_stats()

        assert "0x123" in stats
        assert stats["0x123"] is not None


class TestSingleton:
    """Test singleton pattern."""

    def test_get_analyzer_singleton(self):
        """Test that get_analyzer returns singleton."""
        analyzer1 = get_analyzer()
        analyzer2 = get_analyzer()

        assert analyzer1 is analyzer2

    def test_get_analyzer_custom_params(self):
        """Test get_analyzer maintains singleton (ignores new params)."""
        # First call creates singleton
        analyzer1 = get_analyzer()
        initial_multiplier = analyzer1.anomaly_multiplier

        # Second call with different params returns same singleton
        analyzer2 = get_analyzer(anomaly_multiplier=1.5, rolling_window_size=20)

        # Should be same instance, params unchanged
        assert analyzer1 is analyzer2
        assert analyzer2.anomaly_multiplier == initial_multiplier


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_zero_amount_transaction(self):
        """Test handling zero amount transaction."""
        analyzer = WhaleAnalyzer()

        analyzer.add_transaction("0x123", 0.0)

        stats = analyzer.get_whale_stats("0x123")
        assert stats.avg_amount_usd == 0.0

    def test_negative_amount_not_recommended(self):
        """Test that negative amounts are handled (though not recommended)."""
        analyzer = WhaleAnalyzer()

        # While not recommended, system should handle it gracefully
        analyzer.add_transaction("0x123", -100000.0)

        stats = analyzer.get_whale_stats("0x123")
        assert stats is not None

    def test_very_large_amounts(self):
        """Test handling very large transaction amounts."""
        analyzer = WhaleAnalyzer()

        # $1 billion transaction
        large_amount = 1_000_000_000.0
        analyzer.add_transaction("0x123", large_amount)

        stats = analyzer.get_whale_stats("0x123")
        assert stats.max_amount_usd == large_amount
