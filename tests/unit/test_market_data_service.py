"""
Unit tests for MarketDataService.

Tests Pydantic models, background updates, caching, and error handling.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

from src.services.market_data_service import (
    MarketDataService,
    MarketData,
    MarketDataServiceConfig
)


class TestMarketDataModel:
    """Test Pydantic MarketData model."""

    def test_market_data_defaults(self):
        """MarketData has correct default values."""
        data = MarketData()

        assert data.current_eth_price == 0.0
        assert data.price_change_24h == 0.0
        assert data.sentiment == 'neutral'
        assert data.fear_greed_index == 50
        assert data.trend == 'unknown'

    def test_market_data_validation(self):
        """MarketData validates field values."""
        # Valid data
        data = MarketData(
            current_eth_price=2500.0,
            price_change_24h=-5.2,
            sentiment='fear',
            fear_greed_index=25
        )

        assert data.current_eth_price == 2500.0
        assert data.sentiment == 'fear'

    def test_market_data_sentiment_validation(self):
        """MarketData validates sentiment values."""
        # Invalid sentiment falls back to 'neutral'
        data = MarketData(sentiment='invalid_sentiment')
        assert data.sentiment == 'neutral'

        # Valid sentiments
        for sentiment in ['extreme_fear', 'fear', 'neutral', 'greed', 'extreme_greed']:
            data = MarketData(sentiment=sentiment)
            assert data.sentiment == sentiment

    def test_market_data_trend_validation(self):
        """MarketData validates trend values."""
        # Invalid trend falls back to 'unknown'
        data = MarketData(trend='invalid_trend')
        assert data.trend == 'unknown'

        # Valid trends
        for trend in ['strong_downtrend', 'downtrend', 'sideways', 'uptrend', 'strong_uptrend']:
            data = MarketData(trend=trend)
            assert data.trend == trend

    def test_market_data_fear_greed_index_bounds(self):
        """MarketData validates fear_greed_index is 0-100."""
        # Valid values
        data1 = MarketData(fear_greed_index=0)
        assert data1.fear_greed_index == 0

        data2 = MarketData(fear_greed_index=100)
        assert data2.fear_greed_index == 100

        data3 = MarketData(fear_greed_index=50)
        assert data3.fear_greed_index == 50

    def test_market_data_is_stale(self):
        """MarketData.is_stale() detects stale data."""
        # No timestamp = stale
        data = MarketData()
        assert data.is_stale() is True

        # Recent timestamp = not stale
        data_fresh = MarketData(updated_at=datetime.utcnow())
        assert data_fresh.is_stale(max_age_seconds=600) is False


class TestMarketDataServiceConfig:
    """Test MarketDataServiceConfig Pydantic model."""

    def test_config_defaults(self):
        """Config has correct default values."""
        config = MarketDataServiceConfig()

        assert config.update_interval == 300  # 5 minutes
        assert config.enable_defillama is True
        assert config.enable_coingecko is True
        assert config.enable_fear_greed is True
        assert config.request_timeout == 10
        assert config.max_retries == 3

    def test_config_validation(self):
        """Config validates field constraints."""
        # Valid config
        config = MarketDataServiceConfig(
            update_interval=120,
            request_timeout=15,
            max_retries=5
        )

        assert config.update_interval == 120
        assert config.request_timeout == 15
        assert config.max_retries == 5


class TestMarketDataService:
    """Test MarketDataService functionality."""

    def test_service_initialization(self):
        """Service initializes with default config."""
        service = MarketDataService()

        assert service.config is not None
        assert service.market_data is None
        assert service.last_update is None
        assert service.is_running is False

    def test_service_initialization_with_custom_config(self):
        """Service initializes with custom config."""
        config = MarketDataServiceConfig(
            update_interval=600,
            enable_defillama=False
        )

        service = MarketDataService(config=config)

        assert service.config.update_interval == 600
        assert service.config.enable_defillama is False

    @pytest.mark.asyncio
    async def test_get_market_data_returns_defaults_when_no_data(self):
        """get_market_data returns default data when not initialized."""
        service = MarketDataService()

        data = service.get_market_data()

        # Should return default MarketData
        assert isinstance(data, MarketData)
        assert data.current_eth_price == 0
        assert data.sentiment == 'unknown'

    @pytest.mark.asyncio
    async def test_calculate_volatility(self):
        """Service calculates volatility correctly."""
        service = MarketDataService()

        # Volatility formula: ((high - low) / current) * 100
        volatility = service._calculate_volatility(high=2600, low=2400, current=2500)

        expected = ((2600 - 2400) / 2500) * 100  # 8.0%
        assert volatility == expected

        # Zero current price
        volatility_zero = service._calculate_volatility(high=100, low=50, current=0)
        assert volatility_zero == 0

    @pytest.mark.asyncio
    async def test_detect_trend(self):
        """Service detects market trend correctly."""
        service = MarketDataService()

        # Strong uptrend (>15% in 7d)
        assert service._detect_trend(change_7d=20, change_24h=5) == 'strong_uptrend'

        # Uptrend (5-15% in 7d)
        assert service._detect_trend(change_7d=10, change_24h=2) == 'uptrend'

        # Sideways (-5% to +5%)
        assert service._detect_trend(change_7d=2, change_24h=0.5) == 'sideways'

        # Downtrend (-15% to -5%)
        assert service._detect_trend(change_7d=-10, change_24h=-3) == 'downtrend'

        # Strong downtrend (<-15%)
        assert service._detect_trend(change_7d=-20, change_24h=-8) == 'strong_downtrend'

    @pytest.mark.asyncio
    async def test_service_start_and_stop(self):
        """Service can start and stop properly."""
        service = MarketDataService()

        # Mock update to avoid actual API calls
        service._update_market_data = AsyncMock()

        # Start service
        await service.start()
        assert service.is_running is True
        assert service._task is not None

        # Wait a bit
        await asyncio.sleep(0.1)

        # Stop service
        await service.stop()
        assert service.is_running is False

    @pytest.mark.asyncio
    async def test_fetch_with_retry_success(self):
        """_fetch_with_retry returns data on success."""
        service = MarketDataService()

        # Mock successful response
        mock_json = {'price': 2500}

        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_json)

            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            result = await service._fetch_with_retry('https://example.com/api')

            assert result == mock_json

    @pytest.mark.asyncio
    async def test_fetch_with_retry_handles_rate_limit(self):
        """_fetch_with_retry retries on 429 rate limit."""
        service = MarketDataService(
            config=MarketDataServiceConfig(max_retries=2)
        )

        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            mock_response = AsyncMock()
            if call_count == 1:
                mock_response.status = 429  # Rate limited
            else:
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value={'success': True})

            return mock_response

        with patch('aiohttp.ClientSession') as mock_session:
            mock_context = AsyncMock()
            mock_context.__aenter__ = mock_get

            mock_session.return_value.__aenter__.return_value.get.return_value = mock_context

            result = await service._fetch_with_retry('https://example.com/api')

            # Should have retried and succeeded
            assert call_count == 2
            assert result == {'success': True}

    @pytest.mark.asyncio
    async def test_update_market_data_creates_valid_model(self):
        """_update_market_data creates valid MarketData model."""
        service = MarketDataService()

        # Mock all data sources
        service._get_defillama_price = AsyncMock(return_value=2500.0)
        service._get_coingecko_data = AsyncMock(return_value={
            'current_price': 2500.0,
            'price_change_24h': -5.2,
            'price_change_7d': -12.8,
            'volume_24h': 15000000000,
            'market_cap': 300000000000,
            'high_24h': 2580,
            'low_24h': 2420
        })
        service._get_fear_greed = AsyncMock(return_value={
            'value': 25,
            'classification': 'fear'
        })

        # Update market data
        await service._update_market_data()

        # Check MarketData was created
        assert service.market_data is not None
        assert isinstance(service.market_data, MarketData)

        # Validate fields
        assert service.market_data.current_eth_price == 2500.0
        assert service.market_data.price_change_24h == -5.2
        assert service.market_data.sentiment == 'fear'
        assert service.market_data.fear_greed_index == 25

    @pytest.mark.asyncio
    async def test_update_market_data_graceful_degradation_on_error(self):
        """_update_market_data uses defaults on API failure."""
        service = MarketDataService()

        # Mock all sources to fail
        service._get_defillama_price = AsyncMock(return_value=None)
        service._get_coingecko_data = AsyncMock(return_value={})
        service._get_fear_greed = AsyncMock(return_value={})

        # Update market data
        await service._update_market_data()

        # Should have created default MarketData (not None)
        assert service.market_data is not None
        assert service.market_data.current_eth_price >= 0  # Default or fallback


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
