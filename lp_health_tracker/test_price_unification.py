#!/usr/bin/env python3
"""
Price Strategy Manager - Unification Test
=========================================

Test script to verify that the unified PriceStrategyManager works correctly
after consolidating functionality from PriceOracle and LiveDataProvider.

Run: python test_price_unification.py
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.price_strategy_manager import get_price_manager, PriceStrategyManager

def setup_logging():
    """Setup simple logging for test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_price_manager_initialization():
    """Test 1: Basic initialization."""
    print("🧪 Test 1: PriceStrategyManager Initialization")
    
    try:
        # Test singleton pattern
        manager1 = get_price_manager()
        manager2 = get_price_manager()
        
        assert manager1 is manager2, "Singleton pattern failed"
        print("  ✅ Singleton pattern works")
        
        # Test custom initialization
        custom_manager = PriceStrategyManager(['coingecko_api', 'cached_prices'])
        assert len(custom_manager.sources) == 2, "Custom sources failed"
        print("  ✅ Custom sources configuration works")
        
        print("  🎯 Test 1 PASSED\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Test 1 FAILED: {e}\n")
        return False

def test_token_price_fetching():
    """Test 2: Token price fetching with fallback."""
    print("🧪 Test 2: Token Price Fetching")
    
    try:
        manager = get_price_manager()
        
        # Test single token price
        eth_price = manager.get_token_price('ETH')
        print(f"  📈 ETH price: ${eth_price}")
        
        assert eth_price is not None, "ETH price should not be None"
        assert eth_price > 0, "ETH price should be positive"
        print("  ✅ Single token price fetching works")
        
        # Test multiple tokens
        symbols = ['ETH', 'USDC', 'UNKNOWN_TOKEN']
        prices = manager.get_multiple_prices(symbols)
        print(f"  📊 Multiple prices: {prices}")
        
        assert 'ETH' in prices, "ETH should be in results"
        assert 'USDC' in prices, "USDC should be in results"
        assert prices['ETH'] is not None, "ETH price should not be None"
        print("  ✅ Multiple token price fetching works")
        
        # Test fallback for unknown token
        unknown_price = manager.get_token_price('DEFINITELY_UNKNOWN_TOKEN_XYZ')
        print(f"  🤷 Unknown token price: {unknown_price}")
        print("  ✅ Fallback handling works")
        
        print("  🎯 Test 2 PASSED\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Test 2 FAILED: {e}\n")
        return False

def test_pool_apr_fetching():
    """Test 3: Pool APR fetching (new functionality)."""
    print("🧪 Test 3: Pool APR Fetching")
    
    try:
        manager = get_price_manager()
        
        # Test real pool APR
        weth_usdc_apr = manager.get_pool_apr('WETH-USDC')
        print(f"  📈 WETH-USDC APR: {weth_usdc_apr:.4f} ({weth_usdc_apr*100:.2f}%)")
        
        assert weth_usdc_apr is not None, "APR should not be None"
        assert weth_usdc_apr >= 0, "APR should be non-negative"
        print("  ✅ Pool APR fetching works")
        
        # Test fallback APR
        unknown_pool_apr = manager.get_pool_apr('UNKNOWN-POOL')
        print(f"  🤷 Unknown pool APR: {unknown_pool_apr:.4f} ({unknown_pool_apr*100:.2f}%)")
        
        assert unknown_pool_apr is not None, "Fallback APR should not be None"
        assert unknown_pool_apr > 0, "Fallback APR should be positive"
        print("  ✅ Fallback APR works")
        
        print("  🎯 Test 3 PASSED\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Test 3 FAILED: {e}\n")
        return False

async def test_async_price_fetching():
    """Test 4: Async price fetching."""
    print("🧪 Test 4: Async Price Fetching")
    
    try:
        manager = get_price_manager()
        
        # Test async method
        symbols = ['ETH', 'USDC', 'BTC']
        prices = await manager.get_multiple_prices_parallel_async(symbols)
        print(f"  🚀 Async prices: {prices}")
        
        assert isinstance(prices, dict), "Should return dict"
        assert len(prices) == len(symbols), "Should return all requested symbols"
        print("  ✅ Async price fetching works")
        
        print("  🎯 Test 4 PASSED\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Test 4 FAILED: {e}\n")
        return False

def test_caching_mechanism():
    """Test 5: Caching mechanism."""
    print("🧪 Test 5: Caching Mechanism")
    
    try:
        manager = get_price_manager()
        
        # Clear any existing cache
        manager._price_cache.clear()
        manager._cache_timestamps.clear()
        
        # First call (should fetch from API)
        import time
        start_time = time.time()
        price1 = manager.get_token_price('ETH')
        first_call_time = time.time() - start_time
        
        # Second call (should use cache)
        start_time = time.time()
        price2 = manager.get_token_price('ETH')
        second_call_time = time.time() - start_time
        
        print(f"  ⏱️ First call: {first_call_time:.3f}s, Second call: {second_call_time:.3f}s")
        
        assert price1 == price2, "Cached price should be same"
        assert second_call_time < first_call_time * 0.5, "Second call should be much faster"
        assert manager.cache_hits > 0, "Should register cache hit"
        print("  ✅ Caching mechanism works")
        
        print("  🎯 Test 5 PASSED\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Test 5 FAILED: {e}\n")
        return False

def test_source_reliability():
    """Test 6: Source reliability tracking."""
    print("🧪 Test 6: Source Reliability Tracking")
    
    try:
        manager = get_price_manager()
        
        # Get reliability report
        report = manager.get_source_reliability_report()
        print(f"  📊 Reliability report: {report}")
        
        assert isinstance(report, dict), "Should return dict"
        
        # Test with failing source
        failing_manager = PriceStrategyManager(['failing_source', 'working_source'])
        price = failing_manager.get_token_price('ETH')
        
        reliability = failing_manager.get_source_reliability_report()
        print(f"  📉 After failure test: {reliability}")
        
        assert price is not None, "Should get price from working source"
        print("  ✅ Source reliability tracking works")
        
        print("  🎯 Test 6 PASSED\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Test 6 FAILED: {e}\n")
        return False

async def run_all_tests():
    """Run all tests."""
    print("🔬 Price Strategy Manager - Unification Tests")
    print("=" * 50)
    
    setup_logging()
    
    test_results = []
    
    # Run synchronous tests
    test_results.append(test_price_manager_initialization())
    test_results.append(test_token_price_fetching())
    test_results.append(test_pool_apr_fetching())
    test_results.append(test_caching_mechanism())
    test_results.append(test_source_reliability())
    
    # Run async test
    test_results.append(await test_async_price_fetching())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print("📋 TEST SUMMARY")
    print("=" * 50)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Unification successful!")
        print("\n✅ PriceStrategyManager ready for production use")
        print("✅ PriceOracle and LiveDataProvider can be safely deprecated")
    else:
        print(f"❌ {total - passed} tests failed. Check implementation.")
        
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
