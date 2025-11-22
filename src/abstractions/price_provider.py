"""
Price Provider Abstraction

Abstract base class for token price data sources.
Enables multi-source price fetching and reliability.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal


class PriceProvider(ABC):
    """
    Abstract price provider interface.

    Implementations can use CoinGecko, CoinMarketCap, Uniswap pools,
    DEX aggregators, or any other price source.
    """

    @abstractmethod
    async def get_price(
        self,
        token_address: str,
        vs_currency: str = 'usd'
    ) -> Optional[Decimal]:
        """
        Get current token price.

        Args:
            token_address: Token contract address
            vs_currency: Currency to price against (default: 'usd')

        Returns:
            Optional[Decimal]: Current price or None if not available

        Raises:
            Exception: If API call fails
        """
        pass

    @abstractmethod
    async def get_prices_batch(
        self,
        token_addresses: List[str],
        vs_currency: str = 'usd'
    ) -> Dict[str, Optional[Decimal]]:
        """
        Get prices for multiple tokens.

        Args:
            token_addresses: List of token contract addresses
            vs_currency: Currency to price against

        Returns:
            Dict[str, Optional[Decimal]]: Map of address to price

        Raises:
            Exception: If API call fails
        """
        pass

    @abstractmethod
    async def get_price_at_timestamp(
        self,
        token_address: str,
        timestamp: datetime,
        vs_currency: str = 'usd'
    ) -> Optional[Decimal]:
        """
        Get historical token price at specific timestamp.

        Args:
            token_address: Token contract address
            timestamp: Target timestamp
            vs_currency: Currency to price against

        Returns:
            Optional[Decimal]: Historical price or None if not available

        Raises:
            Exception: If API call fails or historical data not available
        """
        pass

    @abstractmethod
    async def get_price_history(
        self,
        token_address: str,
        start_time: datetime,
        end_time: datetime,
        vs_currency: str = 'usd',
        interval: str = '1h'
    ) -> List[Dict[str, any]]:
        """
        Get price history over time range.

        Args:
            token_address: Token contract address
            start_time: Start timestamp
            end_time: End timestamp
            vs_currency: Currency to price against
            interval: Data interval ('1m', '5m', '1h', '1d', etc.)

        Returns:
            List[Dict]: List of {timestamp, price, volume} entries

        Raises:
            Exception: If API call fails or historical data not available
        """
        pass

    @abstractmethod
    async def get_market_data(
        self,
        token_address: str
    ) -> Dict[str, any]:
        """
        Get comprehensive market data for token.

        Args:
            token_address: Token contract address

        Returns:
            Dict: Market data including:
                - price_usd
                - market_cap
                - volume_24h
                - price_change_24h
                - total_supply
                - circulating_supply

        Raises:
            Exception: If API call fails
        """
        pass

    @abstractmethod
    async def get_token_info(
        self,
        token_address: str
    ) -> Optional[Dict[str, any]]:
        """
        Get basic token information.

        Args:
            token_address: Token contract address

        Returns:
            Optional[Dict]: Token info including name, symbol, decimals, etc.

        Raises:
            Exception: If API call fails
        """
        pass

    @abstractmethod
    async def search_token(
        self,
        query: str
    ) -> List[Dict[str, any]]:
        """
        Search for tokens by name or symbol.

        Args:
            query: Search query

        Returns:
            List[Dict]: List of matching tokens

        Raises:
            Exception: If API call fails
        """
        pass

    @abstractmethod
    async def get_eth_price(self, vs_currency: str = 'usd') -> Decimal:
        """
        Get current ETH price.

        Args:
            vs_currency: Currency to price against

        Returns:
            Decimal: ETH price

        Raises:
            Exception: If API call fails
        """
        pass

    @abstractmethod
    async def convert_value(
        self,
        amount: Decimal,
        from_token: str,
        to_currency: str = 'usd',
        timestamp: Optional[datetime] = None
    ) -> Decimal:
        """
        Convert token amount to fiat value.

        Args:
            amount: Token amount
            from_token: Token contract address
            to_currency: Target currency
            timestamp: Optional timestamp for historical conversion

        Returns:
            Decimal: Converted value

        Raises:
            Exception: If conversion fails
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Get provider name.

        Returns:
            str: Provider name (e.g., 'coingecko', 'uniswap_v3')
        """
        pass

    @property
    @abstractmethod
    def network(self) -> str:
        """
        Get network name.

        Returns:
            str: Network name (e.g., 'ethereum', 'base')
        """
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is available and configured.

        Returns:
            bool: True if provider can be used
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to price provider.

        Returns:
            bool: True if connection successful
        """
        pass

    @property
    def supports_historical_data(self) -> bool:
        """
        Check if provider supports historical price data.

        Returns:
            bool: True if historical data is available
        """
        return False

    @property
    def rate_limit_per_minute(self) -> Optional[int]:
        """
        Get rate limit in requests per minute.

        Returns:
            Optional[int]: Rate limit or None if unlimited
        """
        return None

    @property
    def cache_duration_seconds(self) -> int:
        """
        Get recommended cache duration for prices.

        Returns:
            int: Cache duration in seconds
        """
        return 60  # Default: 1 minute
