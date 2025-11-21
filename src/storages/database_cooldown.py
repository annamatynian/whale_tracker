"""
Database Cooldown Storage

PostgreSQL-based implementation of CooldownStorage using existing database.
Suitable for production with full persistence.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from src.abstractions.cooldown_storage import CooldownStorage


class DatabaseCooldownStorage(CooldownStorage):
    """
    Database cooldown storage implementation.

    Stores cooldown data in PostgreSQL for full persistence.
    Can reuse existing whale_tracker database.

    Note: Requires a 'alert_cooldowns' table:
        CREATE TABLE alert_cooldowns (
            alert_key VARCHAR(255) PRIMARY KEY,
            last_sent_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX idx_last_sent_at ON alert_cooldowns(last_sent_at);
    """

    def __init__(self, db_manager):
        """
        Initialize database storage.

        Args:
            db_manager: AsyncDatabaseManager instance from models.db_connection
        """
        self.logger = logging.getLogger(__name__)
        self.db = db_manager

    @property
    def storage_type(self) -> str:
        """Get storage type."""
        return 'database'

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
            async with self.db.session() as session:
                result = await session.execute(
                    """
                    SELECT last_sent_at FROM alert_cooldowns
                    WHERE alert_key = :key
                    """,
                    {'key': alert_key}
                )
                row = result.fetchone()

                if not row:
                    return False

                last_sent = row[0]
                elapsed = (datetime.utcnow() - last_sent).total_seconds()

                return elapsed < cooldown_seconds

        except Exception as e:
            self.logger.error(f"Error checking cooldown in database: {e}")
            return False

    async def mark_sent(
        self,
        alert_key: str,
        sent_at: Optional[datetime] = None
    ) -> None:
        """Mark alert as sent."""
        try:
            timestamp = sent_at or datetime.utcnow()

            async with self.db.session() as session:
                await session.execute(
                    """
                    INSERT INTO alert_cooldowns (alert_key, last_sent_at)
                    VALUES (:key, :timestamp)
                    ON CONFLICT (alert_key)
                    DO UPDATE SET last_sent_at = :timestamp
                    """,
                    {'key': alert_key, 'timestamp': timestamp}
                )
                await session.commit()

        except Exception as e:
            self.logger.error(f"Error marking alert in database: {e}")

    async def get_last_sent_time(self, alert_key: str) -> Optional[datetime]:
        """Get last sent time for alert."""
        try:
            async with self.db.session() as session:
                result = await session.execute(
                    """
                    SELECT last_sent_at FROM alert_cooldowns
                    WHERE alert_key = :key
                    """,
                    {'key': alert_key}
                )
                row = result.fetchone()

                return row[0] if row else None

        except Exception as e:
            self.logger.error(f"Error getting last sent time from database: {e}")
            return None

    async def clear_alert(self, alert_key: str) -> None:
        """Clear cooldown for alert."""
        try:
            async with self.db.session() as session:
                await session.execute(
                    "DELETE FROM alert_cooldowns WHERE alert_key = :key",
                    {'key': alert_key}
                )
                await session.commit()

        except Exception as e:
            self.logger.error(f"Error clearing alert in database: {e}")

    async def clear_all(self) -> None:
        """Clear all cooldown data."""
        try:
            async with self.db.session() as session:
                result = await session.execute("DELETE FROM alert_cooldowns")
                await session.commit()
                self.logger.info(f"Cleared all cooldown data from database")

        except Exception as e:
            self.logger.error(f"Error clearing all alerts in database: {e}")

    async def get_all_alerts(self) -> dict[str, datetime]:
        """Get all alerts with timestamps."""
        try:
            async with self.db.session() as session:
                result = await session.execute(
                    "SELECT alert_key, last_sent_at FROM alert_cooldowns"
                )
                rows = result.fetchall()

                return {row[0]: row[1] for row in rows}

        except Exception as e:
            self.logger.error(f"Error getting all alerts from database: {e}")
            return {}

    async def cleanup_expired(self, max_age_seconds: int) -> int:
        """Clean up expired entries."""
        try:
            cutoff = datetime.utcnow() - timedelta(seconds=max_age_seconds)

            async with self.db.session() as session:
                result = await session.execute(
                    """
                    DELETE FROM alert_cooldowns
                    WHERE last_sent_at < :cutoff
                    """,
                    {'cutoff': cutoff}
                )
                await session.commit()

                deleted = result.rowcount
                if deleted > 0:
                    self.logger.info(f"Cleaned up {deleted} expired cooldown entries")

                return deleted

        except Exception as e:
            self.logger.error(f"Error cleaning up database: {e}")
            return 0

    async def test_connection(self) -> bool:
        """Test database connection."""
        try:
            async with self.db.session() as session:
                await session.execute("SELECT 1")
                self.logger.info("Database connection successful")
                return True

        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False

    async def get_stats(self) -> dict:
        """Get storage statistics."""
        try:
            async with self.db.session() as session:
                # Get total count
                result = await session.execute(
                    "SELECT COUNT(*) FROM alert_cooldowns"
                )
                total = result.fetchone()[0]

                # Get active count (< 1 hour old)
                one_hour_ago = datetime.utcnow() - timedelta(hours=1)
                result = await session.execute(
                    """
                    SELECT COUNT(*) FROM alert_cooldowns
                    WHERE last_sent_at > :cutoff
                    """,
                    {'cutoff': one_hour_ago}
                )
                active = result.fetchone()[0]

                return {
                    'storage_type': self.storage_type,
                    'total_alerts': total,
                    'active_cooldowns': active,
                    'is_distributed': self.is_distributed
                }

        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {
                'storage_type': self.storage_type,
                'error': str(e)
            }
