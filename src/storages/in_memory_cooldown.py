"""
In-Memory Cooldown Storage

Simple in-memory implementation of CooldownStorage.
Suitable for testing and single-instance deployments.
"""

import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict

from src.abstractions.cooldown_storage import CooldownStorage


class InMemoryCooldownStorage(CooldownStorage):
    """
    In-memory cooldown storage implementation.

    Stores cooldown data in memory. Data is lost on restart.
    Not suitable for distributed deployments.
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self.logger = logging.getLogger(__name__)
        self._alerts: Dict[str, datetime] = {}
        self._access_count: Dict[str, int] = defaultdict(int)

    @property
    def storage_type(self) -> str:
        """Get storage type."""
        return 'memory'

    @property
    def is_distributed(self) -> bool:
        """Check if storage supports distributed deployments."""
        return False

    async def was_sent_recently(
        self,
        alert_key: str,
        cooldown_seconds: int
    ) -> bool:
        """
        Check if alert was sent recently.

        Args:
            alert_key: Alert identifier
            cooldown_seconds: Cooldown period

        Returns:
            bool: True if within cooldown period
        """
        self._access_count[alert_key] += 1

        last_sent = self._alerts.get(alert_key)
        if not last_sent:
            return False

        elapsed = (datetime.utcnow() - last_sent).total_seconds()
        is_recent = elapsed < cooldown_seconds

        if is_recent:
            self.logger.debug(
                f"Alert {alert_key} in cooldown: {elapsed:.0f}s / {cooldown_seconds}s"
            )

        return is_recent

    async def mark_sent(
        self,
        alert_key: str,
        sent_at: Optional[datetime] = None
    ) -> None:
        """
        Mark alert as sent.

        Args:
            alert_key: Alert identifier
            sent_at: Timestamp (defaults to now)
        """
        timestamp = sent_at or datetime.utcnow()
        self._alerts[alert_key] = timestamp
        self.logger.debug(f"Marked alert {alert_key} as sent at {timestamp}")

    async def get_last_sent_time(self, alert_key: str) -> Optional[datetime]:
        """
        Get last sent time for alert.

        Args:
            alert_key: Alert identifier

        Returns:
            Optional[datetime]: Last sent time or None
        """
        return self._alerts.get(alert_key)

    async def clear_alert(self, alert_key: str) -> None:
        """
        Clear cooldown for alert.

        Args:
            alert_key: Alert identifier
        """
        if alert_key in self._alerts:
            del self._alerts[alert_key]
            self.logger.debug(f"Cleared cooldown for alert {alert_key}")

    async def clear_all(self) -> None:
        """Clear all cooldown data."""
        count = len(self._alerts)
        self._alerts.clear()
        self._access_count.clear()
        self.logger.info(f"Cleared all cooldown data ({count} entries)")

    async def get_all_alerts(self) -> dict[str, datetime]:
        """
        Get all alerts with timestamps.

        Returns:
            dict: Alert key to timestamp mapping
        """
        return self._alerts.copy()

    async def cleanup_expired(self, max_age_seconds: int) -> int:
        """
        Clean up expired entries.

        Args:
            max_age_seconds: Maximum age

        Returns:
            int: Number of entries removed
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=max_age_seconds)

        expired_keys = [
            key for key, timestamp in self._alerts.items()
            if timestamp < cutoff
        ]

        for key in expired_keys:
            del self._alerts[key]
            if key in self._access_count:
                del self._access_count[key]

        if expired_keys:
            self.logger.info(
                f"Cleaned up {len(expired_keys)} expired cooldown entries"
            )

        return len(expired_keys)

    async def test_connection(self) -> bool:
        """
        Test storage connection.

        Returns:
            bool: Always True for in-memory storage
        """
        return True

    async def get_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            dict: Statistics
        """
        now = datetime.utcnow()

        # Count active cooldowns (< 1 hour old)
        active_cooldowns = sum(
            1 for timestamp in self._alerts.values()
            if (now - timestamp).total_seconds() < 3600
        )

        return {
            'storage_type': self.storage_type,
            'total_alerts': len(self._alerts),
            'active_cooldowns': active_cooldowns,
            'total_accesses': sum(self._access_count.values()),
            'unique_alerts': len(self._access_count),
            'is_distributed': self.is_distributed
        }
