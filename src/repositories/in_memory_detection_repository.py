"""
In-Memory Detection Repository

In-memory implementation for testing purposes.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict

from src.abstractions.detection_repository import DetectionRepository
from models.schemas import *


class InMemoryDetectionRepository(DetectionRepository):
    """
    In-memory detection repository for testing.

    All data is stored in memory and lost on restart.
    """

    def __init__(self):
        """Initialize in-memory repository."""
        self.logger = logging.getLogger(__name__)
        self._detections: Dict[int, dict] = {}
        self._intermediate_addresses: Dict[str, dict] = {}
        self._transactions: Dict[str, dict] = {}
        self._alerts: Dict[int, dict] = {}
        self._signal_metrics: Dict[int, dict] = {}
        self._next_detection_id = 1
        self._next_alert_id = 1
        self._next_metrics_id = 1

    @property
    def repository_type(self) -> str:
        """Get repository type."""
        return 'memory'

    async def test_connection(self) -> bool:
        """Test connection (always succeeds for in-memory)."""
        return True

    async def save_detection(self, detection: OneHopDetectionCreate) -> int:
        """Save detection."""
        detection_id = self._next_detection_id
        self._next_detection_id += 1

        data = detection.model_dump()
        data.update({
            'id': detection_id,
            'status': 'pending',
            'notes': None,
            'alert_sent': False,
            'alert_sent_at': None,
            'detected_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })

        self._detections[detection_id] = data
        return detection_id

    async def get_detection(self, detection_id: int) -> Optional[OneHopDetectionResponse]:
        """Get detection by ID."""
        data = self._detections.get(detection_id)
        if data:
            return OneHopDetectionResponse(**data)
        return None

    async def get_detections(self, filters: OneHopDetectionFilter) -> List[OneHopDetectionResponse]:
        """Get detections matching filters."""
        results = []
        for data in self._detections.values():
            # Apply filters
            if filters.whale_address and data['whale_address'] != filters.whale_address:
                continue
            if filters.min_confidence and data['total_confidence'] < filters.min_confidence:
                continue
            results.append(OneHopDetectionResponse(**data))

        # Apply pagination
        start = filters.offset
        end = start + filters.limit
        return results[start:end]

    async def update_detection(self, detection_id: int, update: OneHopDetectionUpdate) -> bool:
        """Update detection."""
        if detection_id not in self._detections:
            return False

        data = update.model_dump(exclude_unset=True)
        self._detections[detection_id].update(data)
        self._detections[detection_id]['updated_at'] = datetime.utcnow()
        return True

    async def mark_alert_sent(self, detection_id: int, sent_at: Optional[datetime] = None) -> bool:
        """Mark alert as sent."""
        if detection_id not in self._detections:
            return False

        self._detections[detection_id]['alert_sent'] = True
        self._detections[detection_id]['alert_sent_at'] = sent_at or datetime.utcnow()
        return True

    async def delete_detection(self, detection_id: int) -> bool:
        """Delete detection."""
        if detection_id in self._detections:
            del self._detections[detection_id]
            return True
        return False

    # Intermediate address methods
    async def save_intermediate_address(self, address_data: IntermediateAddressCreate) -> str:
        """Save intermediate address."""
        data = address_data.model_dump()
        data.update({
            'times_used': 1,
            'first_detection_at': datetime.utcnow(),
            'last_detection_at': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        self._intermediate_addresses[data['address']] = data
        return data['address']

    async def get_intermediate_address(self, address: str) -> Optional[IntermediateAddressResponse]:
        """Get intermediate address."""
        data = self._intermediate_addresses.get(address)
        if data:
            return IntermediateAddressResponse(**data)
        return None

    async def get_intermediate_addresses(self, filters: IntermediateAddressFilter) -> List[IntermediateAddressResponse]:
        """Get intermediate addresses."""
        results = []
        for data in self._intermediate_addresses.values():
            # Apply filters
            if filters.profile_type and data['profile_type'] != filters.profile_type:
                continue
            if filters.min_confidence and data['overall_confidence'] < filters.min_confidence:
                continue
            results.append(IntermediateAddressResponse(**data))

        start = filters.offset
        end = start + filters.limit
        return results[start:end]

    async def update_intermediate_address(self, address: str, address_data: IntermediateAddressCreate) -> bool:
        """Update intermediate address."""
        if address not in self._intermediate_addresses:
            return False

        data = address_data.model_dump()
        data['updated_at'] = datetime.utcnow()
        self._intermediate_addresses[address].update(data)
        return True

    async def increment_address_usage(self, address: str, detected_at: Optional[datetime] = None) -> bool:
        """Increment address usage."""
        if address not in self._intermediate_addresses:
            return False

        self._intermediate_addresses[address]['times_used'] += 1
        self._intermediate_addresses[address]['last_detection_at'] = detected_at or datetime.utcnow()
        return True

    # Transaction methods
    async def save_transaction(self, transaction: TransactionCreate) -> str:
        """Save transaction."""
        data = transaction.model_dump()
        data['created_at'] = datetime.utcnow()
        self._transactions[data['tx_hash']] = data
        return data['tx_hash']

    async def get_transaction(self, tx_hash: str) -> Optional[TransactionResponse]:
        """Get transaction."""
        data = self._transactions.get(tx_hash)
        if data:
            return TransactionResponse(**data)
        return None

    async def transaction_exists(self, tx_hash: str) -> bool:
        """Check if transaction exists."""
        return tx_hash in self._transactions

    # Alert methods
    async def save_alert(self, alert: WhaleAlertCreate) -> int:
        """Save alert."""
        alert_id = self._next_alert_id
        self._next_alert_id += 1

        data = alert.model_dump()
        data.update({
            'id': alert_id,
            'sent_at': datetime.utcnow(),
            'delivery_status': 'sent',
            'delivery_error': None,
            'created_at': datetime.utcnow()
        })
        self._alerts[alert_id] = data
        return alert_id

    async def get_alert(self, alert_id: int) -> Optional[WhaleAlertResponse]:
        """Get alert."""
        data = self._alerts.get(alert_id)
        if data:
            return WhaleAlertResponse(**data)
        return None

    async def get_alerts_for_detection(self, detection_id: int) -> List[WhaleAlertResponse]:
        """Get alerts for detection."""
        results = []
        for data in self._alerts.values():
            if data['detection_id'] == detection_id:
                results.append(WhaleAlertResponse(**data))
        return results

    # Signal metrics methods
    async def save_signal_metrics(self, metrics: SignalMetricsCreate) -> int:
        """Save signal metrics."""
        metrics_id = self._next_metrics_id
        self._next_metrics_id += 1

        data = metrics.model_dump()
        data.update({
            'id': metrics_id,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        self._signal_metrics[metrics_id] = data
        return metrics_id

    async def get_signal_metrics(
        self,
        signal_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[SignalMetricsResponse]:
        """Get signal metrics."""
        results = []
        for data in self._signal_metrics.values():
            if data['signal_name'] != signal_name:
                continue
            if start_date and data['date'] < start_date:
                continue
            if end_date and data['date'] > end_date:
                continue
            results.append(SignalMetricsResponse(**data))
        return results

    # Statistics methods
    async def get_detection_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get detection statistics."""
        detections = self._detections.values()

        if start_date:
            detections = [d for d in detections if d['detected_at'] >= start_date]
        if end_date:
            detections = [d for d in detections if d['detected_at'] <= end_date]

        total = len(detections)
        if total == 0:
            return {'total_detections': 0}

        avg_confidence = sum(d['total_confidence'] for d in detections) / total
        high_confidence = sum(1 for d in detections if d['total_confidence'] >= 85)

        return {
            'total_detections': total,
            'avg_confidence': avg_confidence,
            'high_confidence_count': high_confidence
        }

    async def get_top_whales(self, limit: int = 10, start_date: Optional[datetime] = None) -> List[dict]:
        """Get top whales."""
        whale_stats = defaultdict(lambda: {'count': 0, 'volume_eth': 0})

        for detection in self._detections.values():
            if start_date and detection['detected_at'] < start_date:
                continue

            address = detection['whale_address']
            whale_stats[address]['count'] += 1
            whale_stats[address]['volume_eth'] += float(detection['whale_amount_eth'])

        results = [
            {'address': addr, **stats}
            for addr, stats in whale_stats.items()
        ]
        results.sort(key=lambda x: x['volume_eth'], reverse=True)

        return results[:limit]

    async def get_top_intermediates(self, limit: int = 10, start_date: Optional[datetime] = None) -> List[dict]:
        """Get top intermediates."""
        results = []
        for data in self._intermediate_addresses.values():
            if start_date and data['first_detection_at'] < start_date:
                continue
            results.append({
                'address': data['address'],
                'times_used': data['times_used'],
                'profile_type': data['profile_type']
            })

        results.sort(key=lambda x: x['times_used'], reverse=True)
        return results[:limit]

    async def get_whale_statistics(self, whale_address: str, days: int = 30) -> dict:
        """
        Get activity statistics for a specific whale address.

        In-memory implementation for testing. Handles cold start gracefully.

        Args:
            whale_address: Ethereum address of the whale
            days: Number of days to look back (default: 30)

        Returns:
            dict: Whale statistics or empty dict if no historical data
        """
        try:
            # Calculate date threshold
            date_threshold = datetime.utcnow() - timedelta(days=days)

            # Filter detections for this whale within time period
            whale_detections = [
                d for d in self._detections.values()
                if d['whale_address'] == whale_address
                and d['detected_at'] >= date_threshold
            ]

            # Cold start - no data
            if not whale_detections:
                self.logger.debug(
                    f"No historical data for whale {whale_address[:10]}... (cold start)"
                )
                return {}

            # Calculate statistics
            amounts = [float(d['whale_amount_eth']) for d in whale_detections]
            dates = [d['detected_at'] for d in whale_detections]

            first_seen = min(dates)
            last_seen = max(dates)
            days_since_last = (datetime.utcnow() - last_seen).days

            stats = {
                'total_transactions': len(whale_detections),
                'avg_amount_eth': sum(amounts) / len(amounts),
                'max_amount_eth': max(amounts),
                'min_amount_eth': min(amounts),
                'total_volume_eth': sum(amounts),
                'first_seen': first_seen,
                'last_seen': last_seen,
                'days_since_last': days_since_last
            }

            self.logger.debug(
                f"Whale {whale_address[:10]}... stats: "
                f"{stats['total_transactions']} txns, "
                f"avg {stats['avg_amount_eth']:.2f} ETH"
            )

            return stats

        except Exception as e:
            self.logger.error(f"Error calculating whale statistics: {str(e)}")
            return {}  # Graceful degradation
