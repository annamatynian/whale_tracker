"""
Whale Analyzer - Statistical Analysis for Whale Transactions
=============================================================

This module implements statistical analysis for detecting anomalous whale behavior:
- Rolling averages of transaction sizes
- Statistical anomaly detection (threshold multiplier approach)
- Pattern recognition for whale dumping signals

Inspired by: whale_agent/whale_agent.py (open interest analysis)
Adapted for: On-chain wallet transaction analysis

Author: Whale Tracker Project
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque


@dataclass
class TransactionStats:
    """Statistics for a whale's transaction history."""
    whale_address: str
    avg_amount_usd: float
    median_amount_usd: float
    std_dev_usd: float
    max_amount_usd: float
    min_amount_usd: float
    transaction_count: int
    avg_frequency_hours: float
    last_seen: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'whale_address': self.whale_address,
            'avg_amount_usd': self.avg_amount_usd,
            'median_amount_usd': self.median_amount_usd,
            'std_dev_usd': self.std_dev_usd,
            'max_amount_usd': self.max_amount_usd,
            'min_amount_usd': self.min_amount_usd,
            'transaction_count': self.transaction_count,
            'avg_frequency_hours': self.avg_frequency_hours,
            'last_seen': self.last_seen.isoformat() if isinstance(self.last_seen, datetime) else str(self.last_seen)
        }


@dataclass
class AnomalyResult:
    """Result of anomaly detection analysis."""
    is_anomaly: bool
    current_amount: float
    average_amount: float
    threshold: float
    multiplier: float
    confidence: float  # 0-100
    reason: str


class WhaleAnalyzer:
    """
    Statistical analyzer for whale transaction patterns.

    Uses rolling averages and threshold multipliers to detect anomalous behavior.
    Based on the approach from whale_agent (_detect_whale_activity).
    """

    def __init__(
        self,
        anomaly_multiplier: float = 1.3,
        rolling_window_size: int = 10,
        min_history_required: int = 5
    ):
        """
        Initialize WhaleAnalyzer.

        Args:
            anomaly_multiplier: Multiplier above average to trigger anomaly (default 1.3 = 30% above avg)
            rolling_window_size: Number of transactions to use for rolling average (default 10)
            min_history_required: Minimum number of transactions needed for analysis (default 5)
        """
        self.anomaly_multiplier = anomaly_multiplier
        self.rolling_window_size = rolling_window_size
        self.min_history_required = min_history_required

        # Transaction history storage
        # Format: {whale_address: deque of transaction amounts}
        self.transaction_history: Dict[str, deque] = {}

        # Timestamp history for frequency analysis
        # Format: {whale_address: deque of timestamps}
        self.timestamp_history: Dict[str, deque] = {}

    def add_transaction(
        self,
        whale_address: str,
        amount_usd: float,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Add a transaction to whale's history for future analysis.

        Args:
            whale_address: Ethereum address of the whale
            amount_usd: Transaction amount in USD
            timestamp: When the transaction occurred (default: now)
        """
        if whale_address not in self.transaction_history:
            self.transaction_history[whale_address] = deque(maxlen=self.rolling_window_size * 3)
            self.timestamp_history[whale_address] = deque(maxlen=self.rolling_window_size * 3)

        self.transaction_history[whale_address].append(amount_usd)

        if timestamp is None:
            timestamp = datetime.now()
        self.timestamp_history[whale_address].append(timestamp)

    def get_whale_stats(self, whale_address: str) -> Optional[TransactionStats]:
        """
        Calculate statistics for a whale's transaction history.

        Args:
            whale_address: Ethereum address of the whale

        Returns:
            TransactionStats object or None if no history
        """
        if whale_address not in self.transaction_history:
            return None

        amounts = list(self.transaction_history[whale_address])
        timestamps = list(self.timestamp_history[whale_address])

        if not amounts:
            return None

        # Calculate basic statistics
        avg_amount = np.mean(amounts)
        median_amount = np.median(amounts)
        std_dev = np.std(amounts) if len(amounts) > 1 else 0.0
        max_amount = max(amounts)
        min_amount = min(amounts)

        # Calculate frequency (average hours between transactions)
        avg_frequency_hours = 0.0
        if len(timestamps) > 1:
            time_diffs = [(timestamps[i] - timestamps[i-1]).total_seconds() / 3600
                          for i in range(1, len(timestamps))]
            avg_frequency_hours = np.mean(time_diffs)

        return TransactionStats(
            whale_address=whale_address,
            avg_amount_usd=float(avg_amount),
            median_amount_usd=float(median_amount),
            std_dev_usd=float(std_dev),
            max_amount_usd=float(max_amount),
            min_amount_usd=float(min_amount),
            transaction_count=len(amounts),
            avg_frequency_hours=avg_frequency_hours,
            last_seen=timestamps[-1] if timestamps else datetime.now()
        )

    def detect_anomaly(
        self,
        whale_address: str,
        current_amount: float
    ) -> AnomalyResult:
        """
        Detect if current transaction amount is anomalous based on historical pattern.

        Implementation based on whale_agent._detect_whale_activity():
        - Uses rolling average of transaction amounts
        - Applies threshold multiplier (default 1.3x)
        - Current > (average * multiplier) = anomaly

        Args:
            whale_address: Ethereum address of the whale
            current_amount: Current transaction amount in USD

        Returns:
            AnomalyResult with detection details
        """
        if whale_address not in self.transaction_history:
            return AnomalyResult(
                is_anomaly=False,
                current_amount=current_amount,
                average_amount=0.0,
                threshold=0.0,
                multiplier=self.anomaly_multiplier,
                confidence=0.0,
                reason="No historical data available"
            )

        history = list(self.transaction_history[whale_address])

        # Check if we have enough history
        if len(history) < self.min_history_required:
            return AnomalyResult(
                is_anomaly=False,
                current_amount=current_amount,
                average_amount=0.0,
                threshold=0.0,
                multiplier=self.anomaly_multiplier,
                confidence=0.0,
                reason=f"Insufficient history (need {self.min_history_required}, have {len(history)})"
            )

        # Calculate rolling average
        if len(history) <= self.rolling_window_size:
            # Use all history if we don't have enough for full window
            avg_amount = np.mean(history)
        else:
            # Use rolling window
            df = pd.DataFrame({'amount': history})
            rolling_avg = df['amount'].rolling(window=self.rolling_window_size).mean()
            avg_amount = rolling_avg.iloc[-1]

        # Calculate threshold
        threshold = avg_amount * self.anomaly_multiplier

        # Detect anomaly
        is_anomaly = current_amount > threshold

        # Calculate confidence (how far above threshold)
        if is_anomaly:
            excess_ratio = (current_amount - threshold) / threshold
            confidence = min(100.0, 50.0 + (excess_ratio * 100))
        else:
            ratio = current_amount / threshold if threshold > 0 else 0
            confidence = max(0.0, 50.0 - ((1 - ratio) * 50))

        # Generate reason
        if is_anomaly:
            percentage_above = ((current_amount - avg_amount) / avg_amount * 100)
            reason = f"Amount ${current_amount:,.0f} is {percentage_above:.1f}% above avg ${avg_amount:,.0f}"
        else:
            reason = f"Amount ${current_amount:,.0f} is within normal range (avg: ${avg_amount:,.0f})"

        return AnomalyResult(
            is_anomaly=is_anomaly,
            current_amount=current_amount,
            average_amount=float(avg_amount),
            threshold=float(threshold),
            multiplier=self.anomaly_multiplier,
            confidence=float(confidence),
            reason=reason
        )

    def detect_dump_pattern(
        self,
        whale_address: str,
        recent_transactions: List[Dict]
    ) -> Dict:
        """
        Detect if whale is showing dump pattern behavior.

        Dump patterns:
        1. Increasing frequency of transactions
        2. Transactions going to exchanges
        3. Multiple large transactions in short time window

        Args:
            whale_address: Ethereum address of the whale
            recent_transactions: List of recent transactions with metadata

        Returns:
            Dict with dump pattern analysis
        """
        if not recent_transactions:
            return {
                'is_dump_pattern': False,
                'confidence': 0.0,
                'signals': [],
                'recommendation': 'No recent transactions to analyze'
            }

        signals = []
        dump_score = 0.0

        # Signal 1: Multiple large transactions in short period
        if len(recent_transactions) >= 3:
            time_window_hours = 24
            time_threshold = datetime.now() - timedelta(hours=time_window_hours)

            recent_count = sum(
                1 for tx in recent_transactions
                if tx.get('timestamp', datetime.now()) > time_threshold
            )

            if recent_count >= 3:
                signals.append(f"{recent_count} transactions in {time_window_hours} hours")
                dump_score += 30.0

        # Signal 2: Transactions going to exchanges
        exchange_count = sum(
            1 for tx in recent_transactions
            if tx.get('is_exchange_destination', False)
        )

        if exchange_count > 0:
            exchange_ratio = exchange_count / len(recent_transactions)
            if exchange_ratio > 0.5:
                signals.append(f"{exchange_ratio*100:.0f}% of transactions to exchanges")
                dump_score += 40.0
            elif exchange_ratio > 0.3:
                signals.append(f"{exchange_ratio*100:.0f}% of transactions to exchanges")
                dump_score += 20.0

        # Signal 3: Increasing transaction amounts
        amounts = [tx.get('amount_usd', 0) for tx in recent_transactions[-5:]]
        if len(amounts) >= 3:
            # Check if amounts are trending upward
            if amounts[-1] > amounts[0] * 1.5:
                signals.append(f"Transaction sizes increasing (latest {amounts[-1]/amounts[0]:.1f}x first)")
                dump_score += 20.0

        # Signal 4: Faster than normal frequency
        stats = self.get_whale_stats(whale_address)
        if stats and stats.avg_frequency_hours > 0:
            recent_timestamps = [tx.get('timestamp', datetime.now()) for tx in recent_transactions[-3:]]
            if len(recent_timestamps) >= 2:
                recent_avg_hours = np.mean([
                    (recent_timestamps[i] - recent_timestamps[i-1]).total_seconds() / 3600
                    for i in range(1, len(recent_timestamps))
                ])

                if recent_avg_hours < stats.avg_frequency_hours * 0.5:
                    signals.append(f"Transaction frequency 2x faster than normal")
                    dump_score += 10.0

        # Determine if dump pattern
        is_dump_pattern = dump_score >= 50.0

        # Generate recommendation
        if is_dump_pattern:
            recommendation = "⚠️ POTENTIAL DUMP - Whale showing multiple sell signals"
        elif dump_score >= 30.0:
            recommendation = "⚡ CAUTION - Some concerning patterns detected"
        else:
            recommendation = "✅ Normal activity - No immediate dump risk"

        return {
            'is_dump_pattern': is_dump_pattern,
            'confidence': min(100.0, dump_score),
            'signals': signals,
            'recommendation': recommendation,
            'score': dump_score
        }

    def clear_history(self, whale_address: str) -> None:
        """Clear transaction history for a whale."""
        if whale_address in self.transaction_history:
            del self.transaction_history[whale_address]
        if whale_address in self.timestamp_history:
            del self.timestamp_history[whale_address]

    def get_all_whale_addresses(self) -> List[str]:
        """Get list of all whales being tracked."""
        return list(self.transaction_history.keys())

    def export_stats(self) -> Dict:
        """Export statistics for all tracked whales."""
        return {
            address: self.get_whale_stats(address).to_dict()
            if self.get_whale_stats(address) else None
            for address in self.get_all_whale_addresses()
        }


# Global instance
_analyzer_instance = None


def get_analyzer(
    anomaly_multiplier: float = 1.3,
    rolling_window_size: int = 10
) -> WhaleAnalyzer:
    """Get singleton whale analyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = WhaleAnalyzer(
            anomaly_multiplier=anomaly_multiplier,
            rolling_window_size=rolling_window_size
        )
    return _analyzer_instance
