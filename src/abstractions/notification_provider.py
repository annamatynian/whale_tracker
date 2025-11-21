"""
Notification Provider Abstraction

Abstract base class for all notification providers (Telegram, Discord, Email, etc.).
Enables multi-channel notifications and easy testing.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class NotificationProvider(ABC):
    """
    Abstract notification provider interface.

    All notification implementations (Telegram, Discord, Email, Slack, etc.)
    must implement this interface.
    """

    @abstractmethod
    async def send_message(self, message: str, parse_mode: Optional[str] = None) -> bool:
        """
        Send a simple text message.

        Args:
            message: Message text to send
            parse_mode: Optional formatting mode ('HTML', 'Markdown', etc.)

        Returns:
            bool: True if message sent successfully
        """
        pass

    @abstractmethod
    async def send_whale_direct_transfer_alert(
        self,
        from_address: str,
        to_address: str,
        amount_eth: float,
        tx_hash: str,
        block_number: int,
        timestamp: datetime,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send whale direct transfer alert.

        Args:
            from_address: Sender address
            to_address: Recipient address
            amount_eth: Amount in ETH
            tx_hash: Transaction hash
            block_number: Block number
            timestamp: Transaction timestamp
            additional_data: Optional additional data

        Returns:
            bool: True if alert sent successfully
        """
        pass

    @abstractmethod
    async def send_whale_onehop_alert(
        self,
        whale_address: str,
        intermediate_address: str,
        exchange_address: Optional[str],
        whale_amount_eth: float,
        exchange_amount_eth: Optional[float],
        whale_tx_hash: str,
        exchange_tx_hash: Optional[str],
        confidence: int,
        signal_scores: Dict[str, int],
        intermediate_profile: Optional[Dict[str, Any]] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send whale one-hop detection alert.

        Args:
            whale_address: Whale address
            intermediate_address: Intermediate address
            exchange_address: Exchange address (if detected)
            whale_amount_eth: Amount sent by whale
            exchange_amount_eth: Amount sent to exchange (if detected)
            whale_tx_hash: Whale transaction hash
            exchange_tx_hash: Exchange transaction hash (if detected)
            confidence: Overall confidence score (0-100)
            signal_scores: Individual signal scores
            intermediate_profile: Intermediate address profile data
            additional_data: Optional additional data

        Returns:
            bool: True if alert sent successfully
        """
        pass

    @abstractmethod
    async def send_statistical_alert(
        self,
        alert_type: str,
        title: str,
        details: Dict[str, Any],
        severity: str = 'medium'
    ) -> bool:
        """
        Send statistical anomaly alert.

        Args:
            alert_type: Type of alert ('accumulation', 'unusual_activity', etc.)
            title: Alert title
            details: Alert details dictionary
            severity: Alert severity ('low', 'medium', 'high', 'critical')

        Returns:
            bool: True if alert sent successfully
        """
        pass

    @abstractmethod
    async def send_daily_report(
        self,
        date: datetime,
        stats: Dict[str, Any]
    ) -> bool:
        """
        Send daily report with statistics.

        Args:
            date: Report date
            stats: Statistics dictionary

        Returns:
            bool: True if report sent successfully
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to notification service.

        Returns:
            bool: True if connection successful
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Get provider name.

        Returns:
            str: Provider name (e.g., 'telegram', 'discord', 'email')
        """
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if provider is properly configured.

        Returns:
            bool: True if provider is configured and ready to use
        """
        pass
