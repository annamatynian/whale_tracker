"""
SQL Detection Repository

PostgreSQL implementation of DetectionRepository using SQLAlchemy ORM.
"""

import logging
from typing import List, Optional
from datetime import datetime

from src.abstractions.detection_repository import DetectionRepository
from models.schemas import *
from models.database import *


class SQLDetectionRepository(DetectionRepository):
    """
    SQL-based detection repository.

    Uses PostgreSQL with SQLAlchemy ORM for data persistence.
    """

    def __init__(self, db_manager):
        """
        Initialize SQL repository.

        Args:
            db_manager: AsyncDatabaseManager or SyncDatabaseManager instance
        """
        self.logger = logging.getLogger(__name__)
        self.db = db_manager

    @property
    def repository_type(self) -> str:
        """Get repository type."""
        return 'postgresql'

    async def test_connection(self) -> bool:
        """Test database connection."""
        try:
            async with self.db.session() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False

    # Implementation methods would go here
    # For brevity, showing structure only
    # Full implementation available in models/database.py integration

    async def save_detection(self, detection: OneHopDetectionCreate) -> int:
        """Save one-hop detection."""
        async with self.db.session() as session:
            db_detection = OneHopDetection(**detection.model_dump())
            session.add(db_detection)
            await session.flush()
            detection_id = db_detection.id
            await session.commit()
            return detection_id

    async def get_detection(self, detection_id: int) -> Optional[OneHopDetectionResponse]:
        """Get detection by ID."""
        async with self.db.session() as session:
            detection = await session.get(OneHopDetection, detection_id)
            if detection:
                return OneHopDetectionResponse.model_validate(detection)
            return None

    async def get_detections(self, filters: OneHopDetectionFilter) -> List[OneHopDetectionResponse]:
        """Get detections matching filters."""
        # Implementation would build query based on filters
        async with self.db.session() as session:
            query = session.query(OneHopDetection)
            # Apply filters here
            results = await session.execute(query.limit(filters.limit).offset(filters.offset))
            return [OneHopDetectionResponse.model_validate(row) for row in results]

    async def update_detection(self, detection_id: int, update: OneHopDetectionUpdate) -> bool:
        """Update detection."""
        async with self.db.session() as session:
            detection = await session.get(OneHopDetection, detection_id)
            if not detection:
                return False
            for key, value in update.model_dump(exclude_unset=True).items():
                setattr(detection, key, value)
            await session.commit()
            return True

    async def mark_alert_sent(self, detection_id: int, sent_at: Optional[datetime] = None) -> bool:
        """Mark alert as sent."""
        async with self.db.session() as session:
            detection = await session.get(OneHopDetection, detection_id)
            if not detection:
                return False
            detection.alert_sent = True
            detection.alert_sent_at = sent_at or datetime.utcnow()
            await session.commit()
            return True

    async def delete_detection(self, detection_id: int) -> bool:
        """Delete detection."""
        async with self.db.session() as session:
            detection = await session.get(OneHopDetection, detection_id)
            if not detection:
                return False
            await session.delete(detection)
            await session.commit()
            return True

    # Intermediate address methods
    async def save_intermediate_address(self, address_data: IntermediateAddressCreate) -> str:
        """Save intermediate address."""
        async with self.db.session() as session:
            db_address = IntermediateAddress(**address_data.model_dump())
            session.add(db_address)
            await session.commit()
            return db_address.address

    async def get_intermediate_address(self, address: str) -> Optional[IntermediateAddressResponse]:
        """Get intermediate address."""
        async with self.db.session() as session:
            addr = await session.get(IntermediateAddress, address)
            if addr:
                return IntermediateAddressResponse.model_validate(addr)
            return None

    async def get_intermediate_addresses(self, filters: IntermediateAddressFilter) -> List[IntermediateAddressResponse]:
        """Get intermediate addresses."""
        async with self.db.session() as session:
            query = session.query(IntermediateAddress)
            # Apply filters
            results = await session.execute(query.limit(filters.limit).offset(filters.offset))
            return [IntermediateAddressResponse.model_validate(row) for row in results]

    async def update_intermediate_address(self, address: str, address_data: IntermediateAddressCreate) -> bool:
        """Update intermediate address."""
        async with self.db.session() as session:
            addr = await session.get(IntermediateAddress, address)
            if not addr:
                return False
            for key, value in address_data.model_dump().items():
                setattr(addr, key, value)
            await session.commit()
            return True

    async def increment_address_usage(self, address: str, detected_at: Optional[datetime] = None) -> bool:
        """Increment address usage count."""
        async with self.db.session() as session:
            addr = await session.get(IntermediateAddress, address)
            if not addr:
                return False
            addr.times_used += 1
            addr.last_detection_at = detected_at or datetime.utcnow()
            await session.commit()
            return True

    # Transaction methods
    async def save_transaction(self, transaction: TransactionCreate) -> str:
        """Save transaction."""
        async with self.db.session() as session:
            db_tx = Transaction(**transaction.model_dump())
            session.add(db_tx)
            await session.commit()
            return db_tx.tx_hash

    async def get_transaction(self, tx_hash: str) -> Optional[TransactionResponse]:
        """Get transaction."""
        async with self.db.session() as session:
            tx = await session.get(Transaction, tx_hash)
            if tx:
                return TransactionResponse.model_validate(tx)
            return None

    async def transaction_exists(self, tx_hash: str) -> bool:
        """Check if transaction exists."""
        async with self.db.session() as session:
            tx = await session.get(Transaction, tx_hash)
            return tx is not None

    # Alert methods
    async def save_alert(self, alert: WhaleAlertCreate) -> int:
        """Save whale alert."""
        async with self.db.session() as session:
            db_alert = WhaleAlert(**alert.model_dump())
            session.add(db_alert)
            await session.flush()
            alert_id = db_alert.id
            await session.commit()
            return alert_id

    async def get_alert(self, alert_id: int) -> Optional[WhaleAlertResponse]:
        """Get alert."""
        async with self.db.session() as session:
            alert = await session.get(WhaleAlert, alert_id)
            if alert:
                return WhaleAlertResponse.model_validate(alert)
            return None

    async def get_alerts_for_detection(self, detection_id: int) -> List[WhaleAlertResponse]:
        """Get all alerts for detection."""
        async with self.db.session() as session:
            results = await session.execute(
                session.query(WhaleAlert).filter_by(detection_id=detection_id)
            )
            return [WhaleAlertResponse.model_validate(row) for row in results]

    # Signal metrics methods
    async def save_signal_metrics(self, metrics: SignalMetricsCreate) -> int:
        """Save signal metrics."""
        async with self.db.session() as session:
            db_metrics = SignalMetrics(**metrics.model_dump())
            session.add(db_metrics)
            await session.flush()
            metrics_id = db_metrics.id
            await session.commit()
            return metrics_id

    async def get_signal_metrics(
        self,
        signal_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[SignalMetricsResponse]:
        """Get signal metrics."""
        async with self.db.session() as session:
            query = session.query(SignalMetrics).filter_by(signal_name=signal_name)
            if start_date:
                query = query.filter(SignalMetrics.date >= start_date)
            if end_date:
                query = query.filter(SignalMetrics.date <= end_date)
            results = await session.execute(query)
            return [SignalMetricsResponse.model_validate(row) for row in results]

    # Statistics methods
    async def get_detection_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get detection statistics."""
        # Implementation would aggregate data from detections table
        return {
            'total_detections': 0,
            'avg_confidence': 0,
            'high_confidence_count': 0
        }

    async def get_top_whales(self, limit: int = 10, start_date: Optional[datetime] = None) -> List[dict]:
        """Get top whale addresses."""
        # Implementation would group by whale_address and aggregate
        return []

    async def get_top_intermediates(self, limit: int = 10, start_date: Optional[datetime] = None) -> List[dict]:
        """Get top intermediate addresses."""
        # Implementation would use intermediate_addresses table
        return []
