"""
Market Data Service

Background service for fetching and caching market data.
Updates data periodically to avoid API rate limits and reduce latency.

Uses FREE APIs:
- DefiLlama (price data, unlimited)
- CoinGecko Free (market data, 10-30 req/min with caching)
- Alternative.me (Fear & Greed Index, unlimited)
"""

import asyncio
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Optional
from pydantic import BaseModel, Field, validator


logger = logging.getLogger(__name__)


# ==================== Pydantic Models ====================


class MarketData(BaseModel):
    """
    Market data model with validation.

    All market data is validated and typed for safety.
    """
    current_eth_price: float = Field(0.0, ge=0, description="Current ETH price in USD")
    price_change_24h: float = Field(0.0, description="24h price change percentage")
    price_change_7d: float = Field(0.0, description="7d price change percentage")
    volume_24h: float = Field(0.0, ge=0, description="24h trading volume in USD")
    market_cap: float = Field(0.0, ge=0, description="Market capitalization in USD")
    high_24h: float = Field(0.0, ge=0, description="24h high price")
    low_24h: float = Field(0.0, ge=0, description="24h low price")
    volatility_24h: float = Field(0.0, ge=0, description="24h volatility percentage")

    # Sentiment indicators
    sentiment: str = Field("neutral", description="Market sentiment classification")
    fear_greed_index: int = Field(50, ge=0, le=100, description="Fear & Greed Index (0-100)")
    trend: str = Field("unknown", description="Market trend classification")

    # Metadata
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    @validator('sentiment')
    def validate_sentiment(cls, v):
        """Validate sentiment is one of expected values."""
        valid_sentiments = {'extreme_fear', 'fear', 'neutral', 'greed', 'extreme_greed', 'unknown'}
        if v not in valid_sentiments:
            return 'neutral'
        return v

    @validator('trend')
    def validate_trend(cls, v):
        """Validate trend is one of expected values."""
        valid_trends = {'strong_downtrend', 'downtrend', 'sideways', 'uptrend', 'strong_uptrend', 'unknown'}
        if v not in valid_trends:
            return 'unknown'
        return v

    def is_stale(self, max_age_seconds: int = 600) -> bool:
        """
        Check if market data is stale.

        Args:
            max_age_seconds: Maximum age in seconds (default: 600 = 10 min)

        Returns:
            bool: True if data is stale
        """
        if not self.updated_at:
            return True
        age = (datetime.utcnow() - self.updated_at).total_seconds()
        return age > max_age_seconds

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class MarketDataServiceConfig(BaseModel):
    """Configuration for MarketDataService."""
    update_interval: int = Field(300, ge=60, description="Update interval in seconds (min: 60)")
    enable_defillama: bool = Field(True, description="Enable DefiLlama price source")
    enable_coingecko: bool = Field(True, description="Enable CoinGecko market data")
    enable_fear_greed: bool = Field(True, description="Enable Fear & Greed Index")
    request_timeout: int = Field(10, ge=5, le=30, description="API request timeout in seconds")
    max_retries: int = Field(3, ge=1, le=5, description="Maximum retry attempts")


# ==================== Service Implementation ====================


class MarketDataService:
    """
    Background market data service with in-memory caching.

    Features:
    - Fetches data from multiple FREE sources
    - Updates periodically in background (avoids latency on each query)
    - Handles API errors gracefully (uses cached data)
    - Retry logic with exponential backoff
    - Pydantic validation for all data

    Usage:
        >>> service = MarketDataService(update_interval=300)
        >>> await service.start()
        >>> market_data = service.get_market_data()  # Instant, from cache
        >>> await service.stop()
    """

    def __init__(self, config: Optional[MarketDataServiceConfig] = None):
        """
        Initialize Market Data Service.

        Args:
            config: Service configuration (uses defaults if None)
        """
        self.config = config or MarketDataServiceConfig()
        self.market_data: Optional[MarketData] = None
        self.last_update: Optional[datetime] = None
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

        logger.info(
            f"MarketDataService initialized: "
            f"update_interval={self.config.update_interval}s, "
            f"sources: DefiLlama={self.config.enable_defillama}, "
            f"CoinGecko={self.config.enable_coingecko}, "
            f"FearGreed={self.config.enable_fear_greed}"
        )

    async def start(self):
        """Start background market data updates."""
        if self.is_running:
            logger.warning("MarketDataService already running")
            return

        self.is_running = True
        logger.info(f"Starting MarketDataService (update every {self.config.update_interval}s)")

        # Update immediately on start
        await self._update_market_data()

        # Start background loop
        self._task = asyncio.create_task(self._update_loop())

    async def stop(self):
        """Stop background updates."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MarketDataService stopped")

    def get_market_data(self) -> MarketData:
        """
        Get current market data from cache (INSTANT).

        Returns:
            MarketData: Cached market data (Pydantic model)
        """
        if not self.market_data:
            logger.warning("Market data not available, returning defaults")
            return self._get_default_market_data()

        # Check if data is stale
        if self.market_data.is_stale(max_age_seconds=self.config.update_interval * 2):
            logger.warning(
                f"Market data is stale "
                f"(last update: {self.market_data.updated_at})"
            )

        return self.market_data

    # ==================== Background Update Loop ====================

    async def _update_loop(self):
        """Background loop for periodic updates."""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.update_interval)
                await self._update_market_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in market data update loop: {e}")
                # Continue running despite errors

    async def _update_market_data(self):
        """
        Update market data from all sources.

        Uses graceful degradation - if update fails, keeps old cached data.
        """
        try:
            logger.debug("Updating market data from sources...")

            # Fetch from all sources in parallel
            defillama_task = self._get_defillama_price() if self.config.enable_defillama else None
            coingecko_task = self._get_coingecko_data() if self.config.enable_coingecko else None
            fear_greed_task = self._get_fear_greed() if self.config.enable_fear_greed else None

            # Await all with timeout
            results = await asyncio.gather(
                defillama_task or asyncio.sleep(0),
                coingecko_task or asyncio.sleep(0),
                fear_greed_task or asyncio.sleep(0),
                return_exceptions=True
            )

            defillama_price = results[0] if defillama_task and not isinstance(results[0], Exception) else None
            coingecko_data = results[1] if coingecko_task and not isinstance(results[1], Exception) else {}
            fear_greed = results[2] if fear_greed_task and not isinstance(results[2], Exception) else {}

            # Build market data from sources
            current_price = defillama_price or coingecko_data.get('current_price', 0)
            high_24h = coingecko_data.get('high_24h', current_price)
            low_24h = coingecko_data.get('low_24h', current_price)

            # Create validated Pydantic model
            self.market_data = MarketData(
                current_eth_price=current_price,
                price_change_24h=coingecko_data.get('price_change_24h', 0),
                price_change_7d=coingecko_data.get('price_change_7d', 0),
                volume_24h=coingecko_data.get('volume_24h', 0),
                market_cap=coingecko_data.get('market_cap', 0),
                high_24h=high_24h,
                low_24h=low_24h,
                volatility_24h=self._calculate_volatility(high_24h, low_24h, current_price),
                sentiment=fear_greed.get('classification', 'neutral'),
                fear_greed_index=fear_greed.get('value', 50),
                trend=self._detect_trend(
                    coingecko_data.get('price_change_7d', 0),
                    coingecko_data.get('price_change_24h', 0)
                ),
                updated_at=datetime.utcnow()
            )

            self.last_update = datetime.utcnow()

            logger.info(
                f"Market data updated: "
                f"ETH=${self.market_data.current_eth_price:.2f}, "
                f"24h={self.market_data.price_change_24h:+.1f}%, "
                f"sentiment={self.market_data.sentiment}"
            )

        except Exception as e:
            logger.error(f"Failed to update market data: {e}")
            # Keep old cached data - graceful degradation
            if not self.market_data:
                self.market_data = self._get_default_market_data()

    # ==================== Data Source Methods ====================

    async def _get_defillama_price(self) -> Optional[float]:
        """
        Fetch ETH price from DefiLlama (FREE, unlimited).

        Returns:
            Optional[float]: ETH price in USD or None if failed
        """
        try:
            # Native ETH address in DefiLlama
            url = "https://coins.llama.fi/prices/current/ethereum:0x0000000000000000000000000000000000000000"

            data = await self._fetch_with_retry(url)
            if not data:
                return None

            price = data.get('coins', {}).get(
                'ethereum:0x0000000000000000000000000000000000000000',
                {}
            ).get('price')

            if price:
                logger.debug(f"DefiLlama price: ${price:.2f}")

            return price

        except Exception as e:
            logger.error(f"DefiLlama price fetch failed: {e}")
            return None

    async def _get_coingecko_data(self) -> Dict:
        """
        Fetch market data from CoinGecko (FREE, 10-30 req/min).

        Returns:
            Dict: Market data or empty dict if failed
        """
        try:
            url = "https://api.coingecko.com/api/v3/coins/ethereum"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false',
            }

            data = await self._fetch_with_retry(url, params=params)
            if not data:
                return {}

            market_data = data.get('market_data', {})

            result = {
                'current_price': market_data.get('current_price', {}).get('usd', 0),
                'price_change_24h': market_data.get('price_change_percentage_24h', 0),
                'price_change_7d': market_data.get('price_change_percentage_7d', 0),
                'volume_24h': market_data.get('total_volume', {}).get('usd', 0),
                'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                'high_24h': market_data.get('high_24h', {}).get('usd', 0),
                'low_24h': market_data.get('low_24h', {}).get('usd', 0),
            }

            logger.debug(f"CoinGecko data: price=${result['current_price']:.2f}")
            return result

        except Exception as e:
            logger.error(f"CoinGecko fetch failed: {e}")
            return {}

    async def _get_fear_greed(self) -> Dict:
        """
        Fetch Fear & Greed Index from Alternative.me (FREE, unlimited).

        Returns:
            Dict: {'value': int, 'classification': str} or empty dict
        """
        try:
            url = "https://api.alternative.me/fng/"

            data = await self._fetch_with_retry(url)
            if not data:
                return {}

            fng_data = data.get('data', [{}])[0]
            result = {
                'value': int(fng_data.get('value', 50)),
                'classification': fng_data.get('value_classification', 'neutral').lower()
            }

            logger.debug(f"Fear & Greed: {result['value']} ({result['classification']})")
            return result

        except Exception as e:
            logger.error(f"Fear & Greed fetch failed: {e}")
            return {}

    async def _fetch_with_retry(
        self,
        url: str,
        params: Optional[Dict] = None,
        max_retries: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Fetch URL with retry logic and exponential backoff.

        Args:
            url: URL to fetch
            params: Query parameters
            max_retries: Maximum retries (uses config if None)

        Returns:
            Optional[Dict]: JSON response or None if all retries failed
        """
        max_retries = max_retries or self.config.max_retries
        timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, params=params) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        elif resp.status == 429:  # Rate limited
                            wait_time = 2 ** attempt  # Exponential backoff
                            logger.warning(
                                f"Rate limited (429), retrying in {wait_time}s "
                                f"(attempt {attempt+1}/{max_retries})"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        elif resp.status >= 500:  # Server error
                            wait_time = 2 ** attempt
                            logger.warning(
                                f"Server error ({resp.status}), retrying in {wait_time}s "
                                f"(attempt {attempt+1}/{max_retries})"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"API error {resp.status}: {await resp.text()}")
                            return None

            except asyncio.TimeoutError:
                logger.warning(f"Timeout (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
            except Exception as e:
                logger.error(f"Request failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue

        logger.error(f"All {max_retries} attempts failed for {url}")
        return None

    # ==================== Helper Methods ====================

    def _calculate_volatility(self, high: float, low: float, current: float) -> float:
        """
        Calculate 24h volatility percentage.

        Formula: ((High - Low) / Current) * 100
        """
        if current == 0:
            return 0
        return ((high - low) / current) * 100

    def _detect_trend(self, change_7d: float, change_24h: float) -> str:
        """
        Detect market trend from price changes.

        Returns:
            str: 'strong_uptrend', 'uptrend', 'sideways', 'downtrend', 'strong_downtrend'
        """
        if change_7d > 15:
            return 'strong_uptrend'
        elif change_7d > 5:
            return 'uptrend'
        elif change_7d < -15:
            return 'strong_downtrend'
        elif change_7d < -5:
            return 'downtrend'
        else:
            return 'sideways'

    def _get_default_market_data(self) -> MarketData:
        """
        Get default market data (fallback when no data available).

        Returns:
            MarketData: Default/empty market data
        """
        return MarketData(
            current_eth_price=0,
            price_change_24h=0,
            price_change_7d=0,
            volume_24h=0,
            market_cap=0,
            high_24h=0,
            low_24h=0,
            volatility_24h=0,
            sentiment='unknown',
            fear_greed_index=50,
            trend='unknown',
            updated_at=None
        )
