"""
Detection Repository Abstraction

Abstract base class for detection data persistence.
Separates business logic from data access layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

# Import schemas from models
from models.schemas import (
    OneHopDetectionCreate,
    OneHopDetectionResponse,
    OneHopDetectionUpdate,
    OneHopDetectionFilter,
    IntermediateAddressCreate,
    IntermediateAddressResponse,
    IntermediateAddressFilter,
    TransactionCreate,
    TransactionResponse,
    WhaleAlertCreate,
    WhaleAlertResponse,
    SignalMetricsCreate,
    SignalMetricsResponse
)


class DetectionRepository(ABC):
    """
    Abstract repository for detection data.

    Implementations can use PostgreSQL (SQLDetectionRepository) or
    in-memory storage (InMemoryDetectionRepository for testing).
    """

    # ==================== One-Hop Detections ====================

    @abstractmethod
    async def save_detection(self, detection: OneHopDetectionCreate) -> int:
        """
        Save one-hop detection to storage.

        Args:
            detection: Detection data to save

        Returns:
            int: Detection ID

        Raises:
            Exception: If save fails
        """
        pass

    @abstractmethod
    async def get_detection(self, detection_id: int) -> Optional[OneHopDetectionResponse]:
        """
        Get detection by ID.

        Args:
            detection_id: Detection ID

        Returns:
            Optional[OneHopDetectionResponse]: Detection or None if not found
        """
        pass

    @abstractmethod
    async def get_detections(
        self,
        filters: OneHopDetectionFilter
    ) -> List[OneHopDetectionResponse]:
        """
        Get detections matching filters.

        Args:
            filters: Filter criteria

        Returns:
            List[OneHopDetectionResponse]: List of matching detections
        """
        pass

    @abstractmethod
    async def update_detection(
        self,
        detection_id: int,
        update: OneHopDetectionUpdate
    ) -> bool:
        """
        Update detection.

        Args:
            detection_id: Detection ID
            update: Update data

        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    async def mark_alert_sent(
        self,
        detection_id: int,
        sent_at: Optional[datetime] = None
    ) -> bool:
        """
        Mark detection alert as sent.

        Args:
            detection_id: Detection ID
            sent_at: Timestamp when alert was sent (None for current time)

        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    async def delete_detection(self, detection_id: int) -> bool:
        """
        Delete detection.

        Args:
            detection_id: Detection ID

        Returns:
            bool: True if deleted successfully
        """
        pass

    # ==================== Intermediate Addresses ====================

    @abstractmethod
    async def save_intermediate_address(
        self,
        address_data: IntermediateAddressCreate
    ) -> str:
        """
        Save intermediate address profile.

        Args:
            address_data: Address profile data

        Returns:
            str: Address (primary key)
        """
        pass

    @abstractmethod
    async def get_intermediate_address(
        self,
        address: str
    ) -> Optional[IntermediateAddressResponse]:
        """
        Get intermediate address profile.

        Args:
            address: Ethereum address

        Returns:
            Optional[IntermediateAddressResponse]: Address profile or None
        """
        pass

    @abstractmethod
    async def get_intermediate_addresses(
        self,
        filters: IntermediateAddressFilter
    ) -> List[IntermediateAddressResponse]:
        """
        Get intermediate addresses matching filters.

        Args:
            filters: Filter criteria

        Returns:
            List[IntermediateAddressResponse]: List of matching addresses
        """
        pass

    @abstractmethod
    async def update_intermediate_address(
        self,
        address: str,
        address_data: IntermediateAddressCreate
    ) -> bool:
        """
        Update intermediate address profile.

        Args:
            address: Ethereum address
            address_data: Updated profile data

        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    async def increment_address_usage(
        self,
        address: str,
        detected_at: Optional[datetime] = None
    ) -> bool:
        """
        Increment usage count for intermediate address.

        Args:
            address: Ethereum address
            detected_at: Detection timestamp (None for current time)

        Returns:
            bool: True if updated successfully
        """
        pass

    # ==================== Transactions ====================

    @abstractmethod
    async def save_transaction(self, transaction: TransactionCreate) -> str:
        """
        Save transaction to storage.

        Args:
            transaction: Transaction data

        Returns:
            str: Transaction hash

        Raises:
            Exception: If save fails
        """
        pass

    @abstractmethod
    async def get_transaction(self, tx_hash: str) -> Optional[TransactionResponse]:
        """
        Get transaction by hash.

        Args:
            tx_hash: Transaction hash

        Returns:
            Optional[TransactionResponse]: Transaction or None
        """
        pass

    @abstractmethod
    async def transaction_exists(self, tx_hash: str) -> bool:
        """
        Check if transaction exists in storage.

        Args:
            tx_hash: Transaction hash

        Returns:
            bool: True if transaction exists
        """
        pass

    # ==================== Whale Alerts ====================

    @abstractmethod
    async def save_alert(self, alert: WhaleAlertCreate) -> int:
        """
        Save whale alert.

        Args:
            alert: Alert data

        Returns:
            int: Alert ID
        """
        pass

    @abstractmethod
    async def get_alert(self, alert_id: int) -> Optional[WhaleAlertResponse]:
        """
        Get alert by ID.

        Args:
            alert_id: Alert ID

        Returns:
            Optional[WhaleAlertResponse]: Alert or None
        """
        pass

    @abstractmethod
    async def get_alerts_for_detection(
        self,
        detection_id: int
    ) -> List[WhaleAlertResponse]:
        """
        Get all alerts for a detection.

        Args:
            detection_id: Detection ID

        Returns:
            List[WhaleAlertResponse]: List of alerts
        """
        pass

    # ==================== Signal Metrics ====================

    @abstractmethod
    async def save_signal_metrics(
        self,
        metrics: SignalMetricsCreate
    ) -> int:
        """
        Save signal performance metrics.

        Args:
            metrics: Metrics data

        Returns:
            int: Metrics ID
        """
        pass

    @abstractmethod
    async def get_signal_metrics(
        self,
        signal_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[SignalMetricsResponse]:
        """
        Get signal metrics for time period.

        Args:
            signal_name: Signal name
            start_date: Start date (None for all)
            end_date: End date (None for all)

        Returns:
            List[SignalMetricsResponse]: List of metrics
        """
        pass

    # ==================== Statistics ====================

    @abstractmethod
    async def get_detection_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """
        Get detection statistics.

        Args:
            start_date: Start date (None for all time)
            end_date: End date (None for now)

        Returns:
            dict: Statistics dictionary with counts, averages, etc.
        """
        pass

    @abstractmethod
    async def get_top_whales(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None
    ) -> List[dict]:
        """
        Get top whale addresses by activity.

        Args:
            limit: Number of results
            start_date: Start date (None for all time)

        Returns:
            List[dict]: List of {address, detection_count, total_volume_eth}
        """
        pass

    @abstractmethod
    async def get_top_intermediates(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None
    ) -> List[dict]:
        """
        Get top intermediate addresses by usage.

        Args:
            limit: Number of results
            start_date: Start date (None for all time)

        Returns:
            List[dict]: List of {address, times_used, profile_type}
        """
        pass

    # ==================== Utility ====================

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            bool: True if connection successful
        """
        pass

    @property
    @abstractmethod
    def repository_type(self) -> str:
        """
        Get repository type.

        Returns:
            str: Repository type (e.g., 'postgresql', 'memory')
        """
        pass
