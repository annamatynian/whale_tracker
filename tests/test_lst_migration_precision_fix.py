"""
Unit tests for LST Migration Detection - Precision Vulnerability Fix

Tests the critical fix for floating point precision vulnerability identified by Gemini.
Validates that all calculations are performed in Wei (256-bit int) to avoid precision loss.

VULNERABILITY: Original code used absolute balances instead of deltas, causing false positives.
FIX: Calculate deltas in Wei, compare in Wei, convert to ETH only for display.

Author: Whale Tracker Project
Date: 2026-01-21
"""

import pytest
from decimal import Decimal
from typing import Dict

# Mock minimal dependencies
class MockLogger:
    def info(self, msg): pass
    def warning(self, msg): pass

class MockAccumulationScoreCalculator:
    """Minimal implementation for testing _detect_lst_migration logic."""
    
    def __init__(self):
        self.logger = MockLogger()
    
    async def _detect_lst_migration(
        self,
        addresses: list,
        eth_current: Dict[str, int],
        eth_historical: Dict[str, int],
        weth_current: Dict[str, int],
        steth_current: Dict[str, int],
        weth_historical: Dict[str, int],
        steth_historical: Dict[str, int],
        steth_rate: Decimal,
        time_window_hours: int = 1
    ) -> int:
        """Copy of fixed _detect_lst_migration for testing."""
        
        migration_count = 0
        gas_tolerance_wei = int(Decimal('0.01') * Decimal('1e18'))  # 0.01 ETH in Wei
        
        for address in addresses:
            # Get balances in Wei
            eth_now_wei = eth_current.get(address, 0) or 0
            eth_before_wei = eth_historical.get(address, 0) or 0
            weth_now_wei = weth_current.get(address, 0) or 0
            weth_before_wei = weth_historical.get(address, 0) or 0
            steth_now_wei = steth_current.get(address, 0) or 0
            steth_before_wei = steth_historical.get(address, 0) or 0
            
            # ✅ CRITICAL FIX: Calculate CHANGES in Wei
            eth_delta_wei = eth_now_wei - eth_before_wei
            weth_delta_wei = weth_now_wei - weth_before_wei
            
            # stETH conversion with Decimal precision
            steth_now_eth_wei = int(Decimal(str(steth_now_wei)) * steth_rate)
            steth_before_eth_wei = int(Decimal(str(steth_before_wei)) * steth_rate)
            steth_delta_wei = steth_now_eth_wei - steth_before_eth_wei
            
            # Total wealth change
            total_delta_wei = eth_delta_wei + weth_delta_wei + steth_delta_wei
            
            # Migration pattern: ETH↓, LST↑, net≈0
            if (eth_delta_wei < 0 and
                (weth_delta_wei > 0 or steth_delta_wei > 0) and
                abs(total_delta_wei) < gas_tolerance_wei):
                migration_count += 1
        
        return migration_count


@pytest.mark.asyncio
async def test_real_migration_detected():
    """
    Test Case 1: Real migration should be detected.
    
    Whale migrates 1000 ETH → 1000 stETH (1:1 rate)
    Expected: Migration detected (net change ≈ 0)
    """
    calc = MockAccumulationScoreCalculator()
    
    address = "0xWhale1"
    eth_before = 1000 * 10**18  # 1000 ETH in Wei
    eth_now = 0
    steth_before = 0
    steth_now = 1000 * 10**18  # 1000 stETH in Wei
    
    count = await calc._detect_lst_migration(
        addresses=[address],
        eth_current={address: eth_now},
        eth_historical={address: eth_before},
        weth_current={address: 0},
        steth_current={address: steth_now},
        weth_historical={address: 0},
        steth_historical={address: steth_before},
        steth_rate=Decimal('1.0')
    )
    
    assert count == 1, "Real migration (ETH→stETH 1:1) should be detected"


@pytest.mark.asyncio
async def test_purchase_not_migration():
    """
    Test Case 2: Purchase should NOT be detected as migration.
    
    Whale sells 500 ETH, buys 400 stETH (slippage)
    Expected: NOT a migration (net wealth decreased)
    """
    calc = MockAccumulationScoreCalculator()
    
    address = "0xWhale2"
    eth_before = 1000 * 10**18
    eth_now = 500 * 10**18  # Sold 500 ETH
    steth_before = 0
    steth_now = 400 * 10**18  # Bought 400 stETH (lost 100 ETH to slippage)
    
    count = await calc._detect_lst_migration(
        addresses=[address],
        eth_current={address: eth_now},
        eth_historical={address: eth_before},
        weth_current={address: 0},
        steth_current={address: steth_now},
        weth_historical={address: 0},
        steth_historical={address: steth_before},
        steth_rate=Decimal('1.0')
    )
    
    assert count == 0, "Purchase with slippage should NOT be detected as migration"


@pytest.mark.asyncio
async def test_precision_edge_case():
    """
    Test Case 3: Precision edge case - all 18 decimals.
    
    CRITICAL: Tests that 256-bit Wei prevents precision loss.
    ETH: 10000.123456789012345678 ETH (max precision)
    """
    calc = MockAccumulationScoreCalculator()
    
    address = "0xWhale3"
    # Max precision: 10000.123456789012345678 ETH
    eth_before_wei = 10000123456789012345678  # Exactly representable in Wei
    eth_now_wei = 123456789012345678  # Remaining after migration
    steth_before_wei = 0
    steth_now_wei = 10000000000000000000000  # 10000 stETH
    
    count = await calc._detect_lst_migration(
        addresses=[address],
        eth_current={address: eth_now_wei},
        eth_historical={address: eth_before_wei},
        weth_current={address: 0},
        steth_current={address: steth_now_wei},
        weth_historical={address: 0},
        steth_historical={address: steth_before_wei},
        steth_rate=Decimal('1.0')
    )
    
    # Calculate expected delta
    eth_delta = eth_now_wei - eth_before_wei  # Negative
    steth_delta = steth_now_wei - steth_before_wei  # Positive
    net_delta = eth_delta + steth_delta
    
    # Net delta should be within gas tolerance (0.01 ETH = 10^16 Wei)
    gas_tolerance = int(Decimal('0.01') * Decimal('1e18'))
    
    assert abs(net_delta) < gas_tolerance, f"Net delta {net_delta} should be < {gas_tolerance}"
    assert count == 1, "Migration with max precision should be detected (no precision loss!)"


@pytest.mark.asyncio
async def test_no_false_positive_with_existing_weth():
    """
    Test Case 4: CRITICAL - Whale with existing WETH should NOT trigger migration.
    
    This tests the OLD BUG:
    - Old code: weth_delta = weth_now / 1e18 (ALWAYS > 0 if WETH exists!)
    - New code: weth_delta = weth_now - weth_before (can be 0)
    
    Expected: NO migration detected (WETH unchanged, ETH unchanged)
    """
    calc = MockAccumulationScoreCalculator()
    
    address = "0xWhale4"
    eth_before = 5000 * 10**18
    eth_now = 5000 * 10**18  # Unchanged
    weth_before = 2000 * 10**18  # Already had WETH
    weth_now = 2000 * 10**18  # Still has same WETH
    
    count = await calc._detect_lst_migration(
        addresses=[address],
        eth_current={address: eth_now},
        eth_historical={address: eth_before},
        weth_current={address: weth_now},
        steth_current={address: 0},
        weth_historical={address: weth_before},  # ✅ NOW PROVIDED!
        steth_historical={address: 0},
        steth_rate=Decimal('1.0')
    )
    
    assert count == 0, "Whale with unchanged WETH should NOT trigger migration (old bug fixed!)"


@pytest.mark.asyncio
async def test_partial_migration():
    """
    Test Case 5: Partial migration (500 ETH → 500 stETH, keep 500 ETH).
    """
    calc = MockAccumulationScoreCalculator()
    
    address = "0xWhale5"
    eth_before = 1000 * 10**18
    eth_now = 500 * 10**18
    steth_before = 0
    steth_now = 500 * 10**18
    
    count = await calc._detect_lst_migration(
        addresses=[address],
        eth_current={address: eth_now},
        eth_historical={address: eth_before},
        weth_current={address: 0},
        steth_current={address: steth_now},
        weth_historical={address: 0},
        steth_historical={address: steth_before},
        steth_rate=Decimal('1.0')
    )
    
    assert count == 1, "Partial migration (500 ETH → 500 stETH) should be detected"


@pytest.mark.asyncio
async def test_steth_depeg_scenario():
    """
    Test Case 6: stETH depeg (0.98 rate).
    
    Whale migrates 1000 ETH → 1000 stETH, but stETH = 0.98 ETH
    Net wealth: -20 ETH (within gas tolerance? NO)
    """
    calc = MockAccumulationScoreCalculator()
    
    address = "0xWhale6"
    eth_before = 1000 * 10**18
    eth_now = 0
    steth_before = 0
    steth_now = 1000 * 10**18
    
    count = await calc._detect_lst_migration(
        addresses=[address],
        eth_current={address: eth_now},
        eth_historical={address: eth_before},
        weth_current={address: 0},
        steth_current={address: steth_now},
        weth_historical={address: 0},
        steth_historical={address: steth_before},
        steth_rate=Decimal('0.98')  # 2% depeg
    )
    
    # Net delta: -1000 ETH + (1000 stETH × 0.98) = -1000 + 980 = -20 ETH
    # 20 ETH > 0.01 ETH gas tolerance → NOT a migration
    assert count == 0, "Migration during depeg (net loss > tolerance) should NOT be detected"


@pytest.mark.asyncio
async def test_gas_cost_edge_case():
    """
    Test Case 7: Migration with exactly 0.01 ETH gas cost.
    
    Should be at the boundary of detection.
    """
    calc = MockAccumulationScoreCalculator()
    
    address = "0xWhale7"
    gas_cost_wei = int(Decimal('0.01') * Decimal('1e18'))  # Exactly 0.01 ETH
    
    eth_before = 1000 * 10**18
    eth_now = 0 - gas_cost_wei  # Negative (spent gas)
    steth_before = 0
    steth_now = 1000 * 10**18
    
    count = await calc._detect_lst_migration(
        addresses=[address],
        eth_current={address: eth_now},
        eth_historical={address: eth_before},
        weth_current={address: 0},
        steth_current={address: steth_now},
        weth_historical={address: 0},
        steth_historical={address: steth_before},
        steth_rate=Decimal('1.0')
    )
    
    # Net delta = -1000 - 0.01 + 1000 = -0.01 ETH (exactly at boundary)
    # abs(-0.01) < 0.01 → should NOT detect (boundary exclusive)
    assert count == 0, "Migration with exactly 0.01 ETH cost should be at boundary (not detected)"


if __name__ == "__main__":
    import asyncio
    
    print("Running LST Migration Detection Tests (Precision Vulnerability Fix)...")
    print("=" * 80)
    
    tests = [
        ("Real migration (1000 ETH → 1000 stETH)", test_real_migration_detected),
        ("Purchase with slippage (NOT migration)", test_purchase_not_migration),
        ("Precision edge case (18 decimals)", test_precision_edge_case),
        ("False positive fix (existing WETH)", test_no_false_positive_with_existing_weth),
        ("Partial migration (500 ETH → 500 stETH)", test_partial_migration),
        ("stETH depeg scenario (0.98 rate)", test_steth_depeg_scenario),
        ("Gas cost edge case (0.01 ETH)", test_gas_cost_edge_case),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            asyncio.run(test_func())
            print(f"✅ PASS: {name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {name}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"💥 ERROR: {name}")
            print(f"   Exception: {e}")
            failed += 1
    
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED - Precision vulnerability FIXED!")
    else:
        print(f"\n⚠️  {failed} test(s) failed - review implementation")
