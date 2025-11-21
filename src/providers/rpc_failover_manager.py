"""
RPC Failover Manager

Manages multiple RPC providers with configurable priority and automatic failover.
"""

import logging
import asyncio
from typing import List, Tuple, Any, Optional

from src.abstractions.rpc_provider import RPCProvider


class RPCFailoverManager:
    """
    RPC failover manager.

    Manages multiple RPC providers with priority-based failover.
    """

    def __init__(self, providers: List[Tuple[int, RPCProvider]]):
        """
        Initialize failover manager.

        Args:
            providers: List of (priority, provider) tuples
                      Lower priority number = higher priority
        """
        self.logger = logging.getLogger(__name__)
        self.providers = sorted(providers, key=lambda x: x[0])
        self._provider_stats = {}

    async def execute_with_failover(
        self,
        method_name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute method with automatic failover.

        Args:
            method_name: Method name to call
            *args, **kwargs: Method arguments

        Returns:
            Any: Method result

        Raises:
            Exception: If all providers fail
        """
        last_error = None

        for priority, provider in self.providers:
            if not provider.is_healthy:
                self.logger.debug(f"Skipping unhealthy provider: {provider.provider_name}")
                continue

            try:
                self.logger.debug(f"Trying provider: {provider.provider_name} (priority {priority})")
                method = getattr(provider, method_name)
                result = await method(*args, **kwargs)

                self.logger.debug(f"Success with provider: {provider.provider_name}")
                self._record_success(provider)
                return result

            except Exception as e:
                self.logger.warning(f"Provider {provider.provider_name} failed: {e}")
                self._record_failure(provider, e)
                last_error = e
                continue

        raise Exception(f"All RPC providers failed. Last error: {last_error}")

    def _record_success(self, provider: RPCProvider):
        """Record successful request."""
        if provider.provider_name not in self._provider_stats:
            self._provider_stats[provider.provider_name] = {'success': 0, 'failure': 0}
        self._provider_stats[provider.provider_name]['success'] += 1

    def _record_failure(self, provider: RPCProvider, error: Exception):
        """Record failed request."""
        if provider.provider_name not in self._provider_stats:
            self._provider_stats[provider.provider_name] = {'success': 0, 'failure': 0}
        self._provider_stats[provider.provider_name]['failure'] += 1

    def get_stats(self) -> dict:
        """Get provider statistics."""
        return {
            'total_providers': len(self.providers),
            'provider_stats': self._provider_stats
        }
