"""
Multi-Channel Notifier

Sends notifications to multiple channels simultaneously.
Implements the Composite pattern for notification providers.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.abstractions.notification_provider import NotificationProvider


class MultiChannelNotifier(NotificationProvider):
    """
    Multi-channel notification provider.

    Sends notifications to multiple providers (Telegram, Discord, Email, etc.)
    simultaneously. Useful for redundancy and reaching multiple audiences.
    """

    def __init__(self, providers: List[NotificationProvider]):
        """
        Initialize multi-channel notifier.

        Args:
            providers: List of notification providers to use
        """
        self.logger = logging.getLogger(__name__)
        self.providers = providers
        self._active_providers = []
        self._failed_providers = []

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        provider_names = [p.provider_name for p in self.providers]
        return f"multi_channel[{','.join(provider_names)}]"

    @property
    def is_configured(self) -> bool:
        """Check if at least one provider is configured."""
        return any(p.is_configured for p in self.providers)

    async def test_connection(self) -> bool:
        """
        Test all provider connections.

        Returns:
            bool: True if at least one provider is connected
        """
        results = await asyncio.gather(
            *[p.test_connection() for p in self.providers],
            return_exceptions=True
        )

        self._active_providers = []
        self._failed_providers = []

        for provider, result in zip(self.providers, results):
            if isinstance(result, Exception):
                self.logger.error(
                    f"Provider {provider.provider_name} test failed: {result}"
                )
                self._failed_providers.append(provider)
            elif result:
                self._active_providers.append(provider)
                self.logger.info(
                    f"Provider {provider.provider_name} connected successfully"
                )
            else:
                self._failed_providers.append(provider)

        success = len(self._active_providers) > 0
        if success:
            self.logger.info(
                f"Multi-channel notifier: {len(self._active_providers)}/{len(self.providers)} providers active"
            )
        else:
            self.logger.error("Multi-channel notifier: no active providers!")

        return success

    async def _send_to_all(
        self,
        method_name: str,
        *args,
        **kwargs
    ) -> bool:
        """
        Send notification using all active providers.

        Args:
            method_name: Method name to call on each provider
            *args, **kwargs: Arguments to pass to the method

        Returns:
            bool: True if at least one provider succeeded
        """
        if not self._active_providers:
            self.logger.warning("No active providers, attempting to use all configured providers")
            active = [p for p in self.providers if p.is_configured]
        else:
            active = self._active_providers

        if not active:
            self.logger.error("No configured providers available")
            return False

        # Send to all providers concurrently
        tasks = []
        for provider in active:
            method = getattr(provider, method_name)
            tasks.append(method(*args, **kwargs))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Track success/failure
        success_count = 0
        for provider, result in zip(active, results):
            if isinstance(result, Exception):
                self.logger.error(
                    f"Provider {provider.provider_name} {method_name} failed: {result}"
                )
            elif result:
                success_count += 1
                self.logger.debug(
                    f"Provider {provider.provider_name} {method_name} succeeded"
                )
            else:
                self.logger.warning(
                    f"Provider {provider.provider_name} {method_name} returned False"
                )

        success = success_count > 0
        self.logger.info(
            f"Multi-channel {method_name}: {success_count}/{len(active)} providers succeeded"
        )

        return success

    async def send_message(
        self,
        message: str,
        parse_mode: Optional[str] = None
    ) -> bool:
        """Send message to all providers."""
        return await self._send_to_all('send_message', message, parse_mode)

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
        """Send whale direct transfer alert to all providers."""
        return await self._send_to_all(
            'send_whale_direct_transfer_alert',
            from_address,
            to_address,
            amount_eth,
            tx_hash,
            block_number,
            timestamp,
            additional_data
        )

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
        """Send whale one-hop alert to all providers."""
        return await self._send_to_all(
            'send_whale_onehop_alert',
            whale_address,
            intermediate_address,
            exchange_address,
            whale_amount_eth,
            exchange_amount_eth,
            whale_tx_hash,
            exchange_tx_hash,
            confidence,
            signal_scores,
            intermediate_profile,
            additional_data
        )

    async def send_statistical_alert(
        self,
        alert_type: str,
        title: str,
        details: Dict[str, Any],
        severity: str = 'medium'
    ) -> bool:
        """Send statistical alert to all providers."""
        return await self._send_to_all(
            'send_statistical_alert',
            alert_type,
            title,
            details,
            severity
        )

    async def send_daily_report(
        self,
        date: datetime,
        stats: Dict[str, Any]
    ) -> bool:
        """Send daily report to all providers."""
        return await self._send_to_all(
            'send_daily_report',
            date,
            stats
        )

    def get_provider_status(self) -> Dict[str, Any]:
        """
        Get status of all providers.

        Returns:
            Dict: Status information
        """
        return {
            'total_providers': len(self.providers),
            'active_providers': len(self._active_providers),
            'failed_providers': len(self._failed_providers),
            'providers': [
                {
                    'name': p.provider_name,
                    'configured': p.is_configured,
                    'active': p in self._active_providers
                }
                for p in self.providers
            ]
        }
