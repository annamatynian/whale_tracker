"""
CoinGecko Price Provider

Price data from CoinGecko API.
"""

import os
import logging
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal

from src.abstractions.price_provider import PriceProvider


class CoinGeckoProvider(PriceProvider):
    """CoinGecko price provider."""

    BASE_URL = 'https://api.coingecko.com/api/v3'

    def __init__(
        self,
        api_key: Optional[str] = None,
        network: str = 'ethereum'
    ):
        """Initialize CoinGecko provider."""
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self._network = network
        self._platform_id = self._get_platform_id(network)

    def _get_platform_id(self, network: str) -> str:
        """Get CoinGecko platform ID."""
        platform_map = {
            'ethereum': 'ethereum',
            'base': 'base',
            'arbitrum': 'arbitrum-one',
            'optimism': 'optimistic-ethereum',
            'polygon': 'polygon-pos'
        }
        return platform_map.get(network, 'ethereum')

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return 'coingecko'

    @property
    def network(self) -> str:
        """Get network."""
        return self._network

    @property
    def is_available(self) -> bool:
        """Check availability."""
        return True  # CoinGecko has free tier

    async def get_price(
        self,
        token_address: str,
        vs_currency: str = 'usd'
    ) -> Optional[Decimal]:
        """Get token price."""
        try:
            url = f"{self.BASE_URL}/simple/token_price/{self._platform_id}"
            params = {
                'contract_addresses': token_address,
                'vs_currencies': vs_currency
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()

                    price = data.get(token_address.lower(), {}).get(vs_currency)
                    if price:
                        return Decimal(str(price))
                    return None

        except Exception as e:
            self.logger.error(f"Error fetching price from CoinGecko: {e}")
            return None

    async def get_prices_batch(
        self,
        token_addresses: List[str],
        vs_currency: str = 'usd'
    ) -> Dict[str, Optional[Decimal]]:
        """Get multiple prices."""
        # Placeholder - would batch addresses
        result = {}
        for address in token_addresses:
            result[address] = await self.get_price(address, vs_currency)
        return result

    # Stub methods for brevity
    async def get_price_at_timestamp(self, token_address: str, timestamp: datetime, vs_currency: str = 'usd') -> Optional[Decimal]:
        """Historical price (requires Pro API)."""
        raise NotImplementedError("Historical prices require CoinGecko Pro")

    async def get_price_history(self, token_address: str, start_time: datetime, end_time: datetime, vs_currency: str = 'usd', interval: str = '1h') -> List[Dict[str, any]]:
        """Price history."""
        raise NotImplementedError("Price history requires CoinGecko Pro")

    async def get_market_data(self, token_address: str) -> Dict[str, any]:
        """Market data."""
        return {}

    async def get_token_info(self, token_address: str) -> Optional[Dict[str, any]]:
        """Token info."""
        return None

    async def search_token(self, query: str) -> List[Dict[str, any]]:
        """Search tokens."""
        return []

    async def get_eth_price(self, vs_currency: str = 'usd') -> Decimal:
        """Get ETH price."""
        eth_address = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'  # WETH
        price = await self.get_price(eth_address, vs_currency)
        return price or Decimal('0')

    async def convert_value(self, amount: Decimal, from_token: str, to_currency: str = 'usd', timestamp: Optional[datetime] = None) -> Decimal:
        """Convert value."""
        price = await self.get_price(from_token, to_currency)
        if price:
            return amount * price
        return Decimal('0')

    async def test_connection(self) -> bool:
        """Test connection."""
        try:
            url = f"{self.BASE_URL}/ping"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    return True
        except Exception as e:
            self.logger.error(f"CoinGecko connection test failed: {e}")
            return False
