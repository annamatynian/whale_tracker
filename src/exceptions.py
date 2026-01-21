"""
Custom exceptions for Whale Tracker system.

Includes specialized exceptions for snapshot data staleness detection.
"""

from datetime import datetime


class WhaleTrackerException(Exception):
    """Base exception for all whale tracker errors."""
    pass


class StaleSnapshotError(WhaleTrackerException):
    """
    Raised when snapshot data is too old for accurate analysis.
    
    WHY: Prevents accumulation score from being calculated over wrong time period.
    
    Example:
        Requested: 24h lookback
        Found: Snapshot from 48h ago
        → Raises StaleSnapshotError to prevent false [High Conviction] tags
    """
    
    def __init__(
        self,
        requested_timestamp: datetime,
        found_timestamp: datetime,
        max_drift_pct: float,
        actual_drift_pct: float
    ):
        self.requested_timestamp = requested_timestamp
        self.found_timestamp = found_timestamp
        self.max_drift_pct = max_drift_pct
        self.actual_drift_pct = actual_drift_pct
        
        message = (
            f"Stale snapshot detected! "
            f"Requested: {requested_timestamp}, "
            f"Found: {found_timestamp} "
            f"(drift: {actual_drift_pct:.1f}%, max: {max_drift_pct:.1f}%)"
        )
        super().__init__(message)


class InsufficientSnapshotCoverageError(WhaleTrackerException):
    """
    Raised when snapshot density is too low for accurate analysis (GEMINI FIX #7).
    
    WHY: Prevents [High Conviction] on incomplete data after bot downtime.
    
    Example:
        Bot crashed for 12h → missing 50% of hourly snapshots
        → Coverage: 50% < 85% required
        → Raises InsufficientSnapshotCoverageError
        → Tag: [Incomplete Data] instead of [High Conviction]
    """
    
    def __init__(
        self,
        found_snapshots: int,
        expected_snapshots: int,
        coverage_pct: float,
        min_coverage_pct: float,
        lookback_hours: int
    ):
        self.found_snapshots = found_snapshots
        self.expected_snapshots = expected_snapshots
        self.coverage_pct = coverage_pct
        self.min_coverage_pct = min_coverage_pct
        self.lookback_hours = lookback_hours
        
        message = (
            f"Insufficient snapshot coverage! "
            f"Found: {found_snapshots}/{expected_snapshots} snapshots "
            f"({coverage_pct:.1f}% coverage, required: {min_coverage_pct}%) "
            f"over {lookback_hours}h lookback. "
            f"Likely bot downtime detected."
        )
        super().__init__(message)


class NetworkError(WhaleTrackerException):
    """Raised when blockchain network is unreachable."""
    pass


class InvalidConfigurationError(WhaleTrackerException):
    """Raised when configuration is invalid."""
    pass
