"""
Unit Tests for Historical Price Functionality in CoinGeckoProvider

Tests the get_historical_price() method for Bullish Divergence detection:
- Fetching historical prices (24h, 48h, 72h ago)
- Caching behavior (6-hour TTL)
- Address to coin_id mapping
- Timestamp matching logic
- Error handling
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
import time
from aioresponses import aioresponses

from src.providers.coingecko_provider import CoinGeckoProvider


class TestHistoricalPriceFunctionality:
    """Test historical price fetching for divergence detection."""

    @pytest.mark.asyncio
    async def test_get_historical_price_success_24h(self):
        """
        Successfully fetch price from 24 hours ago.
        
        WHY: Basic case - get yesterday's price for comparison.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            # Mock CoinGecko market_chart API
            current_time_ms = time.time() * 1000
            target_time_ms = current_time_ms - (24 * 3600 * 1000)
            
            m.get(
                'https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=2',
                payload={
                    'prices': [
                        [target_time_ms - 3600000, 3200.0],  # 1h before
                        [target_time_ms, 3250.45],            # Target
                        [target_time_ms + 3600000, 3280.0],  # 1h after
                    ]
                }
            )
            
            # WETH address
            price = await provider.get_historical_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                hours_ago=24
            )
            
            assert price == Decimal('3250.45')
            assert isinstance(price, Decimal)

    @pytest.mark.asyncio
    async def test_get_historical_price_success_48h(self):
        """
        Successfully fetch price from 48 hours ago.
        
        WHY: Bullish Divergence primary window.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            current_time_ms = time.time() * 1000
            target_time_ms = current_time_ms - (48 * 3600 * 1000)
            
            m.get(
                'https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=3',
                payload={
                    'prices': [
                        [target_time_ms, 3100.50],
                        [target_time_ms + 3600000, 3120.0],
                    ]
                }
            )
            
            price = await provider.get_historical_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                hours_ago=48
            )
            
            assert price == Decimal('3100.50')

    @pytest.mark.asyncio
    async def test_get_historical_price_success_72h(self):
        """
        Successfully fetch price from 72 hours ago.
        
        WHY: Bullish Divergence extended window.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            current_time_ms = time.time() * 1000
            target_time_ms = current_time_ms - (72 * 3600 * 1000)
            
            m.get(
                'https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=4',
                payload={
                    'prices': [
                        [target_time_ms, 2950.75],
                    ]
                }
            )
            
            price = await provider.get_historical_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                hours_ago=72
            )
            
            assert price == Decimal('2950.75')

    @pytest.mark.asyncio
    async def test_get_historical_price_cached(self):
        """
        Second call within 6h TTL should use cache.
        
        WHY: Historical data doesn't change - aggressive caching.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            current_time_ms = time.time() * 1000
            target_time_ms = current_time_ms - (48 * 3600 * 1000)
            
            # Only one API response
            m.get(
                'https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=3',
                payload={'prices': [[target_time_ms, 3100.0]]}
            )
            
            # First call - API hit
            price1 = await provider.get_historical_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                hours_ago=48
            )
            
            # Second call - cache hit
            price2 = await provider.get_historical_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                hours_ago=48
            )
            
            assert price1 == price2 == Decimal('3100.0')
            # Verify only one API call
            total_calls = sum(len(calls) for calls in m.requests.values())
            assert total_calls == 1

    @pytest.mark.asyncio
    async def test_get_historical_price_steth(self):
        """
        Fetch historical price for stETH.
        
        WHY: Validates coin_id mapping for stETH.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            current_time_ms = time.time() * 1000
            target_time_ms = current_time_ms - (24 * 3600 * 1000)
            
            # stETH uses 'staked-ether' coin_id
            m.get(
                'https://api.coingecko.com/api/v3/coins/staked-ether/market_chart?vs_currency=usd&days=2',
                payload={'prices': [[target_time_ms, 3245.0]]}
            )
            
            # stETH address
            price = await provider.get_historical_price(
                '0xae7ab96520de3a18e5e111b5eaab095312d7fe84',
                hours_ago=24
            )
            
            assert price == Decimal('3245.0')

    @pytest.mark.asyncio
    async def test_get_historical_price_wbtc(self):
        """
        Fetch historical price for WBTC.
        
        WHY: Validates coin_id mapping for WBTC.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            current_time_ms = time.time() * 1000
            target_time_ms = current_time_ms - (48 * 3600 * 1000)
            
            # WBTC uses 'wrapped-bitcoin' coin_id
            m.get(
                'https://api.coingecko.com/api/v3/coins/wrapped-bitcoin/market_chart?vs_currency=usd&days=3',
                payload={'prices': [[target_time_ms, 95000.0]]}
            )
            
            # WBTC address
            price = await provider.get_historical_price(
                '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599',
                hours_ago=48
            )
            
            assert price == Decimal('95000.0')

    @pytest.mark.asyncio
    async def test_get_historical_price_unknown_token(self):
        """
        Unknown token address should return None with warning.
        
        WHY: Graceful handling of unmapped tokens.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        # Unknown address (not in mapping)
        price = await provider.get_historical_price(
            '0x1234567890abcdef1234567890abcdef12345678',
            hours_ago=24
        )
        
        assert price is None

    @pytest.mark.asyncio
    async def test_get_historical_price_api_error(self):
        """
        API error should return None without crashing.
        
        WHY: Network issues shouldn't break divergence detection.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            # Mock API error
            m.get(
                'https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=2',
                status=500
            )
            
            price = await provider.get_historical_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                hours_ago=24
            )
            
            assert price is None

    @pytest.mark.asyncio
    async def test_get_historical_price_empty_response(self):
        """
        Empty prices array should return None.
        
        WHY: Handles API schema changes gracefully.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            m.get(
                'https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=2',
                payload={'prices': []}
            )
            
            price = await provider.get_historical_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                hours_ago=24
            )
            
            assert price is None

    @pytest.mark.asyncio
    async def test_get_historical_price_hours_rounding(self):
        """
        47.5h and 48.2h should both use 48h cache entry.
        
        WHY: Cache efficiency - avoid near-duplicate entries.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            current_time_ms = time.time() * 1000
            target_time_ms = current_time_ms - (48 * 3600 * 1000)
            
            # Only one API mock
            m.get(
                'https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=3',
                payload={'prices': [[target_time_ms, 3100.0]]}
            )
            
            # Call with 47.5h (rounds to 48)
            price1 = await provider.get_historical_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                hours_ago=47.5
            )
            
            # Call with 48.2h (rounds to 48) - should use cache
            price2 = await provider.get_historical_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                hours_ago=48.2
            )
            
            assert price1 == price2 == Decimal('3100.0')
            # Only one API call due to rounding + cache
            total_calls = sum(len(calls) for calls in m.requests.values())
            assert total_calls == 1

    @pytest.mark.asyncio
    async def test_get_historical_price_closest_timestamp(self):
        """
        Should select closest timestamp when exact match not available.
        
        WHY: CoinGecko returns hourly data, may not have exact timestamp.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            current_time_ms = time.time() * 1000
            target_time_ms = current_time_ms - (48 * 3600 * 1000)
            
            # Timestamps don't exactly match target
            m.get(
                'https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=3',
                payload={
                    'prices': [
                        [target_time_ms - 1800000, 3090.0],  # 30min before (closer!)
                        [target_time_ms + 3600000, 3120.0],  # 1h after
                    ]
                }
            )
            
            price = await provider.get_historical_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                hours_ago=48
            )
            
            # Should pick 3090.0 (closer to target)
            assert price == Decimal('3090.0')

    @pytest.mark.asyncio
    async def test_get_historical_price_decimal_precision(self):
        """
        Historical price should maintain Decimal precision.
        
        WHY: Accurate price change calculations for divergence.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            current_time_ms = time.time() * 1000
            target_time_ms = current_time_ms - (48 * 3600 * 1000)
            
            m.get(
                'https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=3',
                payload={'prices': [[target_time_ms, 3250.456789]]}
            )
            
            price = await provider.get_historical_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                hours_ago=48
            )
            
            # Full precision maintained
            assert price == Decimal('3250.456789')
            
            # Test price change calculation
            current_price = Decimal('3300.0')
            price_change = ((current_price - price) / price) * 100
            
            # Should not have float errors
            assert isinstance(price_change, Decimal)


class TestBullishDivergenceWorkflow:
    """Integration tests for Bullish Divergence detection workflow."""

    @pytest.mark.asyncio
    async def test_bullish_divergence_detection_workflow(self):
        """
        Complete workflow: fetch current + 48h price -> detect divergence.
        
        WHY: Validates real-world Bullish Divergence use case.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            # Mock current price
            m.get(
                'https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses=0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2&vs_currencies=usd',
                payload={
                    '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': {'usd': 3250.0}
                }
            )
            
            # Mock 48h ago price
            current_time_ms = time.time() * 1000
            target_time_ms = current_time_ms - (48 * 3600 * 1000)
            m.get(
                'https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=3',
                payload={'prices': [[target_time_ms, 3280.0]]}
            )
            
            # Get current price
            current_price = await provider.get_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                'usd'
            )
            
            # Get 48h ago price
            price_48h = await provider.get_historical_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                hours_ago=48
            )
            
            # Calculate price change
            price_change_pct = ((current_price - price_48h) / price_48h) * 100
            
            # Bullish Divergence: price down but whales accumulating
            assert price_change_pct < 0  # Price decreased
            assert price_change_pct == Decimal('-0.9146341463414634146341463415')  # ~-0.91%
            
            # This would trigger Bullish Divergence tag if whales are accumulating

    @pytest.mark.asyncio
    async def test_multiple_timeframes_comparison(self):
        """
        Compare 24h, 48h, 72h prices for conviction scoring.
        
        WHY: High Conviction tag requires consistent accumulation.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            current_time_ms = time.time() * 1000
            
            # Mock all historical prices
            for hours in [24, 48, 72]:
                days = max(1, hours // 24 + 1)
                target_time_ms = current_time_ms - (hours * 3600 * 1000)
                
                m.get(
                    f'https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days={days}',
                    payload={'prices': [[target_time_ms, 3300.0 - hours]]}
                )
            
            # Fetch all timeframes
            price_24h = await provider.get_historical_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                hours_ago=24
            )
            price_48h = await provider.get_historical_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                hours_ago=48
            )
            price_72h = await provider.get_historical_price(
                '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                hours_ago=72
            )
            
            # Verify trend: prices declining over 3 days
            assert price_24h == Decimal('3276.0')
            assert price_48h == Decimal('3252.0')
            assert price_72h == Decimal('3228.0')
            
            # Downtrend confirmed - good for divergence detection
            assert price_24h > price_48h > price_72h
