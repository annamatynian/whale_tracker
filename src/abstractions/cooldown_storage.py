"""
Cooldown Storage Abstraction

Abstract base class for alert cooldown tracking.
Enables persistent cooldowns and distributed deployments.
"""

from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime


class CooldownStorage(ABC):
    """
    Abstract cooldown storage interface.

    Implementations can use in-memory storage (for testing/single instance),
    Redis (for distributed), or database (for persistence).
    """

    @abstractmethod
    async def was_sent_recently(
        self,
        alert_key: str,
        cooldown_seconds: int
    ) -> bool:
        """
        Check if alert was sent recently (within cooldown period).

        Args:
            alert_key: Unique identifier for the alert
            cooldown_seconds: Cooldown period in seconds

        Returns:
            bool: True if alert was sent within cooldown period
        """
        pass

    @abstractmethod
    async def mark_sent(
        self,
        alert_key: str,
        sent_at: Optional[datetime] = None
    ) -> None:
        """
        Mark alert as sent at given time.

        Args:
            alert_key: Unique identifier for the alert
            sent_at: Timestamp when alert was sent (None for current time)
        """
        pass

    @abstractmethod
    async def get_last_sent_time(self, alert_key: str) -> Optional[datetime]:
        """
        Get timestamp when alert was last sent.

        Args:
            alert_key: Unique identifier for the alert

        Returns:
            Optional[datetime]: Last sent timestamp or None if never sent
        """
        pass

    @abstractmethod
    async def clear_alert(self, alert_key: str) -> None:
        """
        Clear cooldown for specific alert.

        Args:
            alert_key: Unique identifier for the alert
        """
        pass

    @abstractmethod
    async def clear_all(self) -> None:
        """
        Clear all cooldown data.
        """
        pass

    @abstractmethod
    async def get_all_alerts(self) -> dict[str, datetime]:
        """
        Get all alert keys with their last sent times.

        Returns:
            dict: Dictionary mapping alert_key to last_sent_time
        """
        pass

    @abstractmethod
    async def cleanup_expired(self, max_age_seconds: int) -> int:
        """
        Clean up expired entries older than max_age_seconds.

        Args:
            max_age_seconds: Maximum age in seconds

        Returns:
            int: Number of entries cleaned up
        """
        pass

    @property
    @abstractmethod
    def storage_type(self) -> str:
        """
        Get storage type name.

        Returns:
            str: Storage type (e.g., 'memory', 'redis', 'database')
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test storage connection (for Redis/Database implementations).

        Returns:
            bool: True if connection successful
        """
        pass

    @property
    @abstractmethod
    def is_distributed(self) -> bool:
        """
        Check if storage supports distributed deployments.

        Returns:
            bool: True if storage is shared across instances (Redis, Database)
        """
        pass

    @abstractmethod
    async def get_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            dict: Statistics dictionary with keys like 'total_alerts', 'active_cooldowns', etc.
        """
        pass
