"""
DateTime Helpers for LP Health Tracker
====================================

Utilities for handling timezone-aware datetime operations.
Fixes comparison issues between naive and timezone-aware datetimes.
"""

from datetime import datetime, timezone
from typing import Union


def ensure_timezone_aware(dt: Union[datetime, str, None]) -> datetime:
    """Ensure datetime object is timezone-aware.
    
    Args:
        dt: datetime object, ISO string, or None
        
    Returns:
        timezone-aware datetime object
    """
    if dt is None:
        return datetime.now(timezone.utc)
    
    if isinstance(dt, str):
        try:
            # Handle various ISO formats
            if dt.endswith('Z'):
                dt = dt[:-1] + '+00:00'
            dt = datetime.fromisoformat(dt)
        except ValueError:
            # Fallback to current time
            return datetime.now(timezone.utc)
    
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            # Assume UTC for naive datetimes
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    
    return datetime.now(timezone.utc)


def safe_datetime_diff_days(start_dt: Union[datetime, str], end_dt: Union[datetime, str] = None) -> int:
    """Safely calculate difference in days between two datetimes.
    
    Args:
        start_dt: Start datetime (entry date)
        end_dt: End datetime (defaults to now)
        
    Returns:
        int: Number of days difference
    """
    start = ensure_timezone_aware(start_dt)
    end = ensure_timezone_aware(end_dt) if end_dt else datetime.now(timezone.utc)
    
    return max(0, (end - start).days)
