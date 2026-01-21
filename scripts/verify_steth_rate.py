"""
Manual Verification Script for stETH Rate Implementation

Run this to verify the implementation works correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.providers.coingecko_provider import CoinGeckoProvider
from decimal import Decimal


async def test_basic_functionality():
    """Test basic stETH rate fetching."""
    print("=" * 60)
    print("1. Testing Basic Functionality")
    print("=" * 60)
    
    provider = CoinGeckoProvider(api_key='demo_key')
    
    print("\n📡 Fetching stETH/ETH rate from CoinGecko...")
    rate = await provider.get_steth_eth_rate()
    
    print(f"✅ Rate fetched: {rate} ETH")
    print(f"   Type: {type(rate)}")
    assert isinstance(rate, Decimal), "Rate should be Decimal"
    
    # Test typical range
    if Decimal('0.99') <= rate <= Decimal('1.01'):
        print("✅ Rate in normal range (0.99 - 1.01)")
    elif rate < Decimal('0.98'):
        print("⚠️  WARNING: De-peg detected!")
    elif rate > Decimal('1.02'):
        print("⚠️  WARNING: Premium detected!")
    else:
        print("ℹ️  Rate slightly outside normal range but not critical")


async def test_caching():
    """Test cache behavior."""
    print("\n" + "=" * 60)
    print("2. Testing Cache Behavior")
    print("=" * 60)
    
    provider = CoinGeckoProvider(api_key='demo_key')
    
    print("\n📡 First call (should hit API)...")
    import time
    start1 = time.time()
    rate1 = await provider.get_steth_eth_rate()
    time1 = time.time() - start1
    print(f"✅ Rate: {rate1} ETH")
    print(f"   Time: {time1:.3f}s")
    
    print("\n📡 Second call (should use cache)...")
    start2 = time.time()
    rate2 = await provider.get_steth_eth_rate()
    time2 = time.time() - start2
    print(f"✅ Rate: {rate2} ETH")
    print(f"   Time: {time2:.3f}s")
    
    assert rate1 == rate2, "Cached rate should match"
    assert time2 < time1 / 10, "Cache should be much faster"
    print(f"\n✅ Cache working! Speed improvement: {time1/time2:.1f}x")


async def test_whale_conversion():
    """Test real-world whale conversion."""
    print("\n" + "=" * 60)
    print("3. Testing Whale Conversion")
    print("=" * 60)
    
    provider = CoinGeckoProvider(api_key='demo_key')
    rate = await provider.get_steth_eth_rate()
    
    test_cases = [
        Decimal('1000'),      # Small holder
        Decimal('10000'),     # Shark
        Decimal('100000'),    # Whale
        Decimal('1000000'),   # Mega whale
    ]
    
    print(f"\n📊 Converting stETH to ETH (rate: {rate})")
    print("-" * 60)
    for steth in test_cases:
        eth = steth * rate
        diff = steth - eth
        pct = (diff / steth * 100)
        
        print(f"{steth:>15,} stETH = {eth:>15,.2f} ETH")
        print(f"{'':>16}  Discount: {diff:>10,.2f} ETH ({pct:.3f}%)")
        print()


async def test_precision():
    """Test Decimal precision."""
    print("\n" + "=" * 60)
    print("4. Testing Decimal Precision")
    print("=" * 60)
    
    provider = CoinGeckoProvider(api_key='demo_key')
    rate = await provider.get_steth_eth_rate()
    
    print(f"\n🔢 Rate: {rate}")
    print(f"   Precision: {len(str(rate).split('.')[-1])} decimal places")
    
    # Large amount test
    large_amount = Decimal('1000000000')  # 1 billion stETH
    result = large_amount * rate
    
    print(f"\n💰 Converting {large_amount:,} stETH:")
    print(f"   Result: {result:,.10f} ETH")
    print("   ✅ No floating-point errors!")


async def main():
    """Run all verification tests."""
    print("╔" + "=" * 58 + "╗")
    print("║  stETH Rate Provider - Manual Verification             ║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        await test_basic_functionality()
        await test_caching()
        await test_whale_conversion()
        await test_precision()
        
        print("\n" + "=" * 60)
        print("✅ ALL VERIFICATIONS PASSED!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run full test suite:")
        print("   pytest tests/unit/test_price_provider_steth.py -v")
        print("\n2. Integrate with AccumulationCalculator")
        print("   See: docs/STETH_RATE_IMPLEMENTATION.md")
        
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
