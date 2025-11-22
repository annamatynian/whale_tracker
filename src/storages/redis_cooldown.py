"""
Redis Cooldown Storage

Redis-based implementation of CooldownStorage.
Suitable for production and distributed deployments.
"""

import logging
from typing import Optional
from datetime import datetime
import time

from src.abstractions.cooldown_storage import CooldownStorage


class RedisCooldownStorage(CooldownStorage):
    """
    Redis cooldown storage implementation.

    Stores cooldown data in Redis for persistence and distributed support.
    Requires redis package: pip install redis aioredis
    """

    def __init__(self, redis_client):
        """
        Initialize Redis storage.

        Args:
            redis_client: Redis async client instance (aioredis or redis.asyncio)
        """
        self.logger = logging.getLogger(__name__)
        self.redis = redis_client
        self.key_prefix = "whale_tracker:alert:"

    @property
    def storage_type(self) -> str:
        """Get storage type."""
        return 'redis'

    @property
    def is_distributed(self) -> bool:
        """Check if storage supports distributed deployments."""
        return True

    async def was_sent_recently(
        self,
        alert_key: str,
        cooldown_seconds: int
    ) -> bool:
        """Check if alert was sent recently."""
        try:
            key = f"{self.key_prefix}{alert_key}"
            last_sent_str = await self.redis.get(key)

            if not last_sent_str:
                return False

            last_sent = float(last_sent_str)
            elapsed = time.time() - last_sent

            return elapsed < cooldown_seconds

        except Exception as e:
            self.logger.error(f"Error checking cooldown in Redis: {e}")
            return False

    async def mark_sent(
        self,
        alert_key: str,
        sent_at: Optional[datetime] = None
    ) -> None:
        """Mark alert as sent."""
        try:
            timestamp = sent_at.timestamp() if sent_at else time.time()
            key = f"{self.key_prefix}{alert_key}"

            # Store with 24 hour expiration
            await self.redis.set(key, str(timestamp), ex=86400)

        except Exception as e:
            self.logger.error(f"Error marking alert in Redis: {e}")

    async def get_last_sent_time(self, alert_key: str) -> Optional[datetime]:
        """Get last sent time for alert."""
        try:
            key = f"{self.key_prefix}{alert_key}"
            last_sent_str = await self.redis.get(key)

            if last_sent_str:
                timestamp = float(last_sent_str)
                return datetime.fromtimestamp(timestamp)

            return None

        except Exception as e:
            self.logger.error(f"Error getting last sent time from Redis: {e}")
            return None

    async def clear_alert(self, alert_key: str) -> None:
        """Clear cooldown for alert."""
        try:
            key = f"{self.key_prefix}{alert_key}"
            await self.redis.delete(key)

        except Exception as e:
            self.logger.error(f"Error clearing alert in Redis: {e}")

    async def clear_all(self) -> None:
        """Clear all cooldown data."""
        try:
            pattern = f"{self.key_prefix}*"
            keys = await self.redis.keys(pattern)

            if keys:
                await self.redis.delete(*keys)
                self.logger.info(f"Cleared {len(keys)} cooldown entries from Redis")

        except Exception as e:
            self.logger.error(f"Error clearing all alerts in Redis: {e}")

    async def get_all_alerts(self) -> dict[str, datetime]:
        """Get all alerts with timestamps."""
        try:
            pattern = f"{self.key_prefix}*"
            keys = await self.redis.keys(pattern)

            result = {}
            for key in keys:
                alert_key = key.decode() if isinstance(key, bytes) else key
                alert_key = alert_key.replace(self.key_prefix, '')

                value = await self.redis.get(key)
                if value:
                    timestamp = float(value)
                    result[alert_key] = datetime.fromtimestamp(timestamp)

            return result

        except Exception as e:
            self.logger.error(f"Error getting all alerts from Redis: {e}")
            return {}

    async def cleanup_expired(self, max_age_seconds: int) -> int:
        """
        Clean up expired entries.

        Note: Redis automatically expires keys, so this is mostly a no-op.
        """
        # Redis handles expiration automatically
        return 0

    async def test_connection(self) -> bool:
        """Test Redis connection."""
        try:
            await self.redis.ping()
            self.logger.info("Redis connection successful")
            return True

        except Exception as e:
            self.logger.error(f"Redis connection test failed: {e}")
            return False

    async def get_stats(self) -> dict:
        """Get storage statistics."""
        try:
            pattern = f"{self.key_prefix}*"
            keys = await self.redis.keys(pattern)
            total_alerts = len(keys)

            # Count active cooldowns (entries exist = still in cooldown)
            active_cooldowns = total_alerts

            return {
                'storage_type': self.storage_type,
                'total_alerts': total_alerts,
                'active_cooldowns': active_cooldowns,
                'is_distributed': self.is_distributed
            }

        except Exception as e:
            self.logger.error(f"Error getting Redis stats: {e}")
            return {
                'storage_type': self.storage_type,
                'error': str(e)
            }
