"""
Unit Tests for stETH/ETH Rate Functionality in CoinGeckoProvider

Tests the new get_steth_eth_rate() method with:
- Successful rate fetching
- Caching behavior
- Error handling and fallback
- De-peg detection (warning triggers)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
import time
from aioresponses import aioresponses

from src.providers.coingecko_provider import CoinGeckoProvider


class TestStethRateFunctionality:
    """Test stETH/ETH rate fetching and caching."""

    @pytest.mark.asyncio
    async def test_get_steth_eth_rate_success(self):
        """
        Successfully fetch stETH rate from CoinGecko API.
        
        WHY: Normal case - rate should be fetched and returned as Decimal.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            # Mock CoinGecko API response
            m.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=staked-ether&vs_currencies=eth',
                payload={
                    'staked-ether': {'eth': 0.9987}
                }
            )
            
            rate = await provider.get_steth_eth_rate()
            
            assert rate == Decimal('0.9987')
            assert isinstance(rate, Decimal)

    @pytest.mark.asyncio
    async def test_get_steth_eth_rate_cached(self):
        """
        Second call within TTL should return cached value without API call.
        
        WHY: Reduces API load - stETH rate doesn't change every second.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            # First call - API hit
            m.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=staked-ether&vs_currencies=eth',
                payload={'staked-ether': {'eth': 0.9987}}
            )
            
            rate1 = await provider.get_steth_eth_rate()
            
            # Second call - should use cache (no new API call)
            rate2 = await provider.get_steth_eth_rate()
            
            assert rate1 == rate2 == Decimal('0.9987')
            # Verify only one API call was made
            # WHY: aioresponses groups by URL, need to count actual RequestCall objects
            total_calls = sum(len(calls) for calls in m.requests.values())
            assert total_calls == 1

    @pytest.mark.asyncio
    async def test_get_steth_eth_rate_cache_expiry(self):
        """
        After TTL expires, should make new API call.
        
        WHY: Ensures fresh data after cache timeout.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        provider._cache_ttl = 0.1  # 100ms for testing
        
        with aioresponses() as m:
            # First call
            m.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=staked-ether&vs_currencies=eth',
                payload={'staked-ether': {'eth': 0.9987}}
            )
            
            rate1 = await provider.get_steth_eth_rate()
            
            # Wait for cache to expire
            time.sleep(0.15)
            
            # Second call - new API call
            m.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=staked-ether&vs_currencies=eth',
                payload={'staked-ether': {'eth': 0.9990}}
            )
            
            rate2 = await provider.get_steth_eth_rate()
            
            assert rate1 == Decimal('0.9987')
            assert rate2 == Decimal('0.9990')
            # Verify two API calls were made
            # WHY: aioresponses groups by URL, need to count actual RequestCall objects
            total_calls = sum(len(calls) for calls in m.requests.values())
            assert total_calls == 2

    @pytest.mark.asyncio
    async def test_get_steth_eth_rate_api_error_fallback(self):
        """
        On API error, should return fallback 1.0 without crashing.
        
        WHY: Prevents system crashes when CoinGecko is down.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            # Mock API error
            m.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=staked-ether&vs_currencies=eth',
                status=500
            )
            
            rate = await provider.get_steth_eth_rate()
            
            assert rate == Decimal('1.0')

    @pytest.mark.asyncio
    async def test_get_steth_eth_rate_timeout_fallback(self):
        """
        On timeout, should return fallback 1.0.
        
        WHY: Network issues shouldn't crash whale tracking.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            # Mock timeout
            m.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=staked-ether&vs_currencies=eth',
                exception=TimeoutError('Request timeout')
            )
            
            rate = await provider.get_steth_eth_rate()
            
            assert rate == Decimal('1.0')

    @pytest.mark.asyncio
    async def test_get_steth_eth_rate_missing_data_fallback(self):
        """
        If API returns unexpected structure, should fallback to 1.0.
        
        WHY: Handles API schema changes gracefully.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            # Mock incomplete response
            m.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=staked-ether&vs_currencies=eth',
                payload={'wrong-key': {}}
            )
            
            rate = await provider.get_steth_eth_rate()
            
            assert rate == Decimal('1.0')

    @pytest.mark.asyncio
    async def test_get_steth_eth_rate_depeg_warning_low(self, caplog):
        """
        When rate < 0.98, should log de-peg warning.
        
        WHY: Alerts risk management - severe discount indicates protocol issues.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            # Mock severe de-peg
            m.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=staked-ether&vs_currencies=eth',
                payload={'staked-ether': {'eth': 0.95}}
            )
            
            with caplog.at_level('WARNING'):
                rate = await provider.get_steth_eth_rate()
            
            assert rate == Decimal('0.95')
            assert 'DE-PEG DETECTED' in caplog.text
            assert '0.95' in caplog.text

    @pytest.mark.asyncio
    async def test_get_steth_eth_rate_premium_warning_high(self, caplog):
        """
        When rate > 1.02, should log premium warning.
        
        WHY: Unusual premium suggests demand spike or liquidity issues.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            # Mock unusual premium
            m.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=staked-ether&vs_currencies=eth',
                payload={'staked-ether': {'eth': 1.05}}
            )
            
            with caplog.at_level('WARNING'):
                rate = await provider.get_steth_eth_rate()
            
            assert rate == Decimal('1.05')
            assert 'PREMIUM DETECTED' in caplog.text
            assert '1.05' in caplog.text

    @pytest.mark.asyncio
    async def test_get_steth_eth_rate_normal_range_no_warning(self, caplog):
        """
        Normal range (0.99-1.01) should not trigger warnings.
        
        WHY: Prevents alert fatigue from normal fluctuations.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            # Mock normal rate
            m.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=staked-ether&vs_currencies=eth',
                payload={'staked-ether': {'eth': 0.9995}}
            )
            
            with caplog.at_level('WARNING'):
                rate = await provider.get_steth_eth_rate()
            
            assert rate == Decimal('0.9995')
            assert 'DE-PEG' not in caplog.text
            assert 'PREMIUM' not in caplog.text

    @pytest.mark.asyncio
    async def test_get_steth_eth_rate_precision_decimal(self):
        """
        Rate should maintain Decimal precision for financial calculations.
        
        WHY: Prevents floating-point errors in large ETH amounts.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            m.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=staked-ether&vs_currencies=eth',
                payload={'staked-ether': {'eth': 0.998734567}}
            )
            
            rate = await provider.get_steth_eth_rate()
            
            # Should preserve full precision
            assert rate == Decimal('0.998734567')
            
            # Test with large amount
            steth_amount = Decimal('1000000')  # 1M stETH
            eth_equivalent = steth_amount * rate
            
            # Should not have floating-point rounding errors
            assert eth_equivalent == Decimal('998734.567')


class TestStethRateIntegration:
    """Integration tests for real-world usage patterns."""

    @pytest.mark.asyncio
    async def test_steth_conversion_workflow(self):
        """
        Test complete workflow: fetch rate -> convert stETH to ETH.
        
        WHY: Validates typical use case in whale tracking.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            m.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=staked-ether&vs_currencies=eth',
                payload={'staked-ether': {'eth': 0.9987}}
            )
            
            rate = await provider.get_steth_eth_rate()
            
            # Whale transfers 10,000 stETH
            steth_amount = Decimal('10000')
            eth_equivalent = steth_amount * rate
            
            assert eth_equivalent == Decimal('9987.0')

    @pytest.mark.asyncio
    async def test_multiple_concurrent_calls_use_cache(self):
        """
        Multiple concurrent calls should use cache after first completes.
        
        WHY: Prevents API rate limit issues during parallel whale checks.
        """
        provider = CoinGeckoProvider(api_key='test_key')
        
        with aioresponses() as m:
            m.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=staked-ether&vs_currencies=eth',
                payload={'staked-ether': {'eth': 0.9987}}
            )
            
            # Simulate multiple concurrent whale checks
            import asyncio
            rates = await asyncio.gather(*[
                provider.get_steth_eth_rate() for _ in range(5)
            ])
            
            assert all(r == Decimal('0.9987') for r in rates)
            # Should only make one API call despite 5 requests
            # WHY: aioresponses groups by URL, need to count actual RequestCall objects
            total_calls = sum(len(calls) for calls in m.requests.values())
            assert total_calls == 1
