"""
CoinGecko Price Provider

Price data from CoinGecko API.
"""

import os
import logging
import aiohttp
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import time

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
        
        # WHY: stETH rate cache - reduces API calls (rate changes slowly)
        self._steth_rate_cache: Optional[Tuple[Decimal, float]] = None  # (rate, timestamp)
        self._cache_ttl = 300  # 5 minutes
        
        # WHY: Historical price cache - historical data never changes
        # Key: (coin_id, hours_ago_rounded)
        self._historical_cache: Dict[Tuple[str, int], Tuple[Decimal, float]] = {}
        self._historical_cache_ttl = 21600  # 6 hours
        
        # WHY: Address to CoinGecko coin_id mapping
        # CoinGecko API requires coin_id, not contract address
        self._address_to_coin_id = {
            '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': 'ethereum',  # WETH
            '0xae7ab96520de3a18e5e111b5eaab095312d7fe84': 'staked-ether',  # stETH
            '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': 'wrapped-bitcoin',  # WBTC
            '0x514910771af9ca656af840dff83e8264ecf986ca': 'chainlink',  # LINK
            '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984': 'uniswap',  # UNI
        }

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

    async def get_historical_price(
        self,
        token_address: str,
        hours_ago: int,
        vs_currency: str = 'usd'
    ) -> Optional[Decimal]:
        """
        Get historical token price N hours ago.
        
        WHY: Required for Bullish Divergence detection:
        - Compare current whale accumulation vs price 48-72h ago
        - If whales buying but price flat/down = bullish signal
        
        Args:
            token_address: Contract address (e.g., WETH, stETH)
            hours_ago: How many hours back (24, 48, 72)
            vs_currency: Target currency (default: usd)
            
        Returns:
            Decimal: Historical price, or None if not found
            
        Example:
            >>> provider = CoinGeckoProvider()
            >>> # Get ETH price 48 hours ago
            >>> price_48h = await provider.get_historical_price(
            ...     '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
            ...     hours_ago=48
            ... )
            >>> print(f"ETH 48h ago: ${price_48h}")
            ETH 48h ago: $3250.45
        """
        # Normalize address
        token_address = token_address.lower()
        
        # WHY: Round hours for cache efficiency
        # 47.5h and 48.2h both use 48h cache entry
        hours_rounded = round(hours_ago)
        
        # Check cache first
        cache_key = (token_address, hours_rounded)
        if cache_key in self._historical_cache:
            cached_price, cached_time = self._historical_cache[cache_key]
            if time.time() - cached_time < self._historical_cache_ttl:
                self.logger.debug(
                    f"Using cached historical price for {token_address} "
                    f"{hours_rounded}h ago: {cached_price}"
                )
                return cached_price
        
        try:
            # WHY: CoinGecko requires coin_id, not address
            coin_id = self._address_to_coin_id.get(token_address)
            if not coin_id:
                self.logger.warning(
                    f"Unknown token address {token_address}, cannot fetch historical price. "
                    f"Add to _address_to_coin_id mapping."
                )
                return None
            
            # WHY: Convert hours to days for API
            # CoinGecko granularity:
            # - days=1: 5min intervals
            # - days=2-90: 1hour intervals (optimal for 24-72h)
            # - days>90: 1day intervals
            days = max(1, hours_rounded // 24 + 1)
            
            url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': vs_currency,
                'days': days
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    prices = data.get('prices', [])
                    if not prices:
                        self.logger.warning(
                            f"No historical prices returned for {coin_id} ({token_address})"
                        )
                        return None
                    
                    # WHY: Find closest price to target timestamp
                    # prices = [[timestamp_ms, price], ...]
                    target_timestamp = (time.time() - hours_rounded * 3600) * 1000  # Convert to ms
                    
                    closest_price = min(
                        prices,
                        key=lambda p: abs(p[0] - target_timestamp)
                    )
                    
                    price = Decimal(str(closest_price[1]))
                    actual_timestamp = closest_price[0] / 1000  # Convert back to seconds
                    time_diff_hours = abs(actual_timestamp - (target_timestamp / 1000)) / 3600
                    
                    # WHY: Log if actual timestamp differs significantly
                    if time_diff_hours > 2:
                        self.logger.warning(
                            f"Historical price for {coin_id} {hours_rounded}h ago "
                            f"has {time_diff_hours:.1f}h time difference from target"
                        )
                    
                    # Cache the result
                    self._historical_cache[cache_key] = (price, time.time())
                    self.logger.info(
                        f"Fetched historical price for {coin_id} ({token_address}) "
                        f"{hours_rounded}h ago: {price} {vs_currency} "
                        f"(cached for {self._historical_cache_ttl}s)"
                    )
                    
                    return price
                    
        except Exception as e:
            self.logger.error(
                f"Error fetching historical price for {token_address} "
                f"{hours_rounded}h ago: {e}"
            )
            return None
    
    async def get_current_price(
        self,
        token_symbol: str,
        vs_currency: str = 'usd'
    ) -> Optional[Decimal]:
        """
        Get current price by token symbol (convenience method).
        
        Args:
            token_symbol: Token symbol (e.g., "ETH", "BTC")
            vs_currency: Currency to price against
        
        Returns:
            Optional[Decimal]: Current price or None
        """
        try:
            # Map symbol to CoinGecko coin_id
            symbol_to_id = {
                'ETH': 'ethereum',
                'BTC': 'bitcoin',
                'WETH': 'ethereum',  # WETH = ETH price
                'STETH': 'staked-ether',
                'WBTC': 'wrapped-bitcoin',
                'LINK': 'chainlink',
                'UNI': 'uniswap'
            }
            
            coin_id = symbol_to_id.get(token_symbol.upper())
            if not coin_id:
                self.logger.warning(f"Unknown token symbol {token_symbol}")
                return None
            
            url = f"{self.BASE_URL}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': vs_currency
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    price_raw = data.get(coin_id, {}).get(vs_currency)
                    if not price_raw:
                        return None
                    
                    return Decimal(str(price_raw))
                    
        except Exception as e:
            self.logger.error(f"Error fetching current price for {token_symbol}: {e}")
            return None
    
    async def get_historical_price(
        self,
        token_symbol: str,
        timestamp: datetime,
        vs_currency: str = 'usd'
    ) -> Optional[Decimal]:
        """
        Get historical price by token symbol at specific timestamp.
        
        Args:
            token_symbol: Token symbol (e.g., "ETH", "BTC")
            timestamp: Target timestamp
            vs_currency: Currency to price against
        
        Returns:
            Optional[Decimal]: Historical price or None
        """
        try:
            # Map symbol to CoinGecko coin_id
            symbol_to_id = {
                'ETH': 'ethereum',
                'BTC': 'bitcoin',
                'WETH': 'ethereum',
                'STETH': 'staked-ether',
                'WBTC': 'wrapped-bitcoin',
                'LINK': 'chainlink',
                'UNI': 'uniswap'
            }
            
            coin_id = symbol_to_id.get(token_symbol.upper())
            if not coin_id:
                self.logger.warning(f"Unknown token symbol {token_symbol}")
                return None
            
            # Calculate hours ago
            hours_ago = (datetime.now() - timestamp).total_seconds() / 3600
            days = max(1, int(hours_ago // 24 + 1))
            
            url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': vs_currency,
                'days': days
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    prices = data.get('prices', [])
                    if not prices:
                        return None
                    
                    # Find closest price to target timestamp
                    target_timestamp_ms = int(timestamp.timestamp() * 1000)
                    
                    closest_price = min(
                        prices,
                        key=lambda p: abs(p[0] - target_timestamp_ms)
                    )
                    
                    return Decimal(str(closest_price[1]))
                    
        except Exception as e:
            self.logger.error(
                f"Error fetching historical price for {token_symbol} "
                f"at {timestamp}: {e}"
            )
            return None
    
    async def get_steth_eth_rate(self) -> Decimal:
        """
        Fetch stETH/ETH exchange rate from CoinGecko.
        
        WHY: stETH ≠ 1.0 ETH due to:
        - Redemption queue delays
        - Market liquidity conditions
        - Protocol risks (slashing, etc.)
        
        Typical range: 0.99-1.01 ETH
        De-peg warning: < 0.98 or > 1.02
        
        Returns:
            Decimal: stETH price in ETH (e.g., 0.9987)
            Fallback: 1.0 on API error
            
        Example:
            >>> provider = CoinGeckoProvider()
            >>> rate = await provider.get_steth_eth_rate()
            >>> print(f"1 stETH = {rate} ETH")
            1 stETH = 0.9987 ETH
        """
        # Check cache first
        if self._steth_rate_cache:
            cached_rate, cached_time = self._steth_rate_cache
            if time.time() - cached_time < self._cache_ttl:
                self.logger.debug(f"Using cached stETH rate: {cached_rate}")
                return cached_rate
        
        try:
            # CoinGecko endpoint: /simple/price?ids=staked-ether&vs_currencies=eth
            url = f"{self.BASE_URL}/simple/price"
            params = {
                'ids': 'staked-ether',
                'vs_currencies': 'eth'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    rate_raw = data.get('staked-ether', {}).get('eth')
                    if not rate_raw:
                        self.logger.warning("stETH rate not found in response, using fallback 1.0")
                        return Decimal('1.0')
                    
                    rate = Decimal(str(rate_raw))
                    
                    # WHY: De-peg detection - critical for risk management
                    if rate < Decimal('0.98'):
                        self.logger.warning(
                            f"⚠️ stETH DE-PEG DETECTED: {rate} ETH (< 0.98) - High risk!"
                        )
                    elif rate > Decimal('1.02'):
                        self.logger.warning(
                            f"⚠️ stETH PREMIUM DETECTED: {rate} ETH (> 1.02) - Unusual!"
                        )
                    
                    # Cache the result
                    self._steth_rate_cache = (rate, time.time())
                    self.logger.info(f"Fetched stETH rate: {rate} ETH (cached for {self._cache_ttl}s)")
                    
                    return rate
                    
        except Exception as e:
            self.logger.error(f"Error fetching stETH rate from CoinGecko: {e}")
            # WHY: Fallback to 1.0 prevents crashes in dependent modules
            return Decimal('1.0')
    
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
