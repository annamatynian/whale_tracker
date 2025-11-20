"""
Comprehensive test for Volume Ratio Health Check implementation
Tests the "Golden Middle" logic from "Liquidity and volume corrected.docx"
"""

import sys
sys.path.insert(0, r'C:\Users\annam\Documents\DeFi-RAG-Project\crypto-multi-agent-system')

from agents.discovery.volume_metrics_extension import (
    calculate_volume_metrics_from_daily_data,
    apply_volume_filters
)


def test_volume_ratio_health_check():
    """
    Test the Volume Ratio Health Check implementation.
    
    Tests cover:
    1. ✅ Healthy ratio (0.5 < ratio < 3.0) → Should PASS with bonus
    2. ⚠️ Overheated ratio (ratio > 3.0) → Should PASS with warning
    3. ❌ Dead token (ratio < 0.5) → Should FAIL
    4. No acceleration → Should FAIL (even with healthy ratio)
    """
    
    print("=" * 80)
    print("VOLUME RATIO HEALTH CHECK - COMPREHENSIVE TEST")
    print("=" * 80)
    print("\nBased on: 'Liquidity and volume corrected.docx'")
    print("Golden Middle Logic: 0.5 < volume_ratio < 3.0 → Healthy (+5 pts)")
    print("=" * 80)
    
    # ========================================
    # Test Case 1: IDEAL SCENARIO
    # ========================================
    print("\n" + "─" * 80)
    print("TEST CASE 1: ✅ IDEAL - Healthy Ratio + Acceleration")
    print("─" * 80)
    print("Setup: volume=$100k (7d avg), volume=$50k (30d avg), liquidity=$50k")
    print("Expected: ratio=2.0, acceleration=2.0x, should PASS with +20 pts")
    
    mock_data_ideal = [
        {'date': 30 - i, 'dailyVolumeUSD': 100000 if i < 7 else 50000, 'totalLiquidityUSD': 50000}
        for i in range(30)
    ]
    
    metrics_ideal = calculate_volume_metrics_from_daily_data(mock_data_ideal)
    
    print(f"\nCalculated Metrics:")
    print(f"  avg_volume_7d:        ${metrics_ideal['avg_volume_last_7_days']:,.0f}")
    print(f"  avg_volume_30d:       ${metrics_ideal['avg_volume_last_30_days']:,.0f}")
    print(f"  acceleration_factor:  {metrics_ideal['acceleration_factor']:.2f}x")
    print(f"  is_accelerating:      {metrics_ideal['is_accelerating']}")
    print(f"  volume_ratio:         {metrics_ideal['volume_ratio']:.3f}")
    
    print(f"\nRatio Classification:")
    print(f"  ✅ ratio_healthy:     {metrics_ideal['volume_ratio_healthy']}")
    print(f"  ⚠️  ratio_overheated: {metrics_ideal['volume_ratio_overheated']}")
    print(f"  ❌ ratio_dead:        {metrics_ideal['volume_ratio_dead']}")
    
    passed, reason = apply_volume_filters(metrics_ideal)
    print(f"\n{'✓' if passed else '✗'} Filter Result: {'PASS' if passed else 'FAIL'}")
    print(f"  Reason: {reason}")
    
    expected_bonus = 20  # 15 for acceleration + 5 for healthy ratio
    print(f"\n💰 Expected Bonus Points: {expected_bonus}")
    print(f"  - Acceleration bonus: ~15 pts")
    print(f"  - Healthy ratio bonus: +5 pts")
    
    assert passed == True, "Test 1 should PASS"
    assert metrics_ideal['volume_ratio_healthy'] == True
    assert metrics_ideal['is_accelerating'] == True
    print("\n✅ Test Case 1: PASSED")
    
    # ========================================
    # Test Case 2: OVERHEATED (WARNING)
    # ========================================
    print("\n" + "─" * 80)
    print("TEST CASE 2: ⚠️ OVERHEATED - High Ratio (> 3.0) but with Acceleration")
    print("─" * 80)
    print("Setup: volume=$200k (7d), volume=$100k (30d), liquidity=$50k")
    print("Expected: ratio=4.0, should PASS but with warning (no bonus for ratio)")
    
    mock_data_overheated = [
        {'date': 30 - i, 'dailyVolumeUSD': 200000 if i < 7 else 100000, 'totalLiquidityUSD': 50000}
        for i in range(30)
    ]
    
    metrics_overheat = calculate_volume_metrics_from_daily_data(mock_data_overheated)
    
    print(f"\nCalculated Metrics:")
    print(f"  volume_ratio:         {metrics_overheat['volume_ratio']:.3f}")
    print(f"  acceleration_factor:  {metrics_overheat['acceleration_factor']:.2f}x")
    
    print(f"\nRatio Classification:")
    print(f"  ✅ ratio_healthy:     {metrics_overheat['volume_ratio_healthy']}")
    print(f"  ⚠️  ratio_overheated: {metrics_overheat['volume_ratio_overheated']}")
    print(f"  ❌ ratio_dead:        {metrics_overheat['volume_ratio_dead']}")
    
    passed, reason = apply_volume_filters(metrics_overheat)
    print(f"\n{'✓' if passed else '✗'} Filter Result: {'PASS' if passed else 'FAIL'}")
    print(f"  Reason: {reason}")
    
    print(f"\n💰 Expected Bonus Points: ~20 (acceleration only, no ratio bonus)")
    
    assert passed == True, "Test 2 should PASS (with warning)"
    assert metrics_overheat['volume_ratio_overheated'] == True
    assert metrics_overheat['volume_ratio_healthy'] == False
    print("\n✅ Test Case 2: PASSED")
    
    # ========================================
    # Test Case 3: DEAD TOKEN (CRITICAL FAIL)
    # ========================================
    print("\n" + "─" * 80)
    print("TEST CASE 3: ❌ DEAD TOKEN - Low Ratio (< 0.5)")
    print("─" * 80)
    print("Setup: volume=$10k (7d), volume=$5k (30d), liquidity=$50k")
    print("Expected: ratio=0.2, should FAIL immediately (critical red flag)")
    
    mock_data_dead = [
        {'date': 30 - i, 'dailyVolumeUSD': 10000 if i < 7 else 5000, 'totalLiquidityUSD': 50000}
        for i in range(30)
    ]
    
    metrics_dead = calculate_volume_metrics_from_daily_data(mock_data_dead)
    
    print(f"\nCalculated Metrics:")
    print(f"  volume_ratio:         {metrics_dead['volume_ratio']:.3f}")
    print(f"  acceleration_factor:  {metrics_dead['acceleration_factor']:.2f}x")
    
    print(f"\nRatio Classification:")
    print(f"  ✅ ratio_healthy:     {metrics_dead['volume_ratio_healthy']}")
    print(f"  ⚠️  ratio_overheated: {metrics_dead['volume_ratio_overheated']}")
    print(f"  ❌ ratio_dead:        {metrics_dead['volume_ratio_dead']}")
    
    passed, reason = apply_volume_filters(metrics_dead)
    print(f"\n{'✓' if passed else '✗'} Filter Result: {'PASS' if passed else 'FAIL'}")
    print(f"  Reason: {reason}")
    
    print(f"\n💀 Token is DEAD - should be excluded from candidates")
    
    assert passed == False, "Test 3 should FAIL"
    assert metrics_dead['volume_ratio_dead'] == True
    print("\n✅ Test Case 3: PASSED")
    
    # ========================================
    # Test Case 4: NO ACCELERATION (FAIL)
    # ========================================
    print("\n" + "─" * 80)
    print("TEST CASE 4: NO ACCELERATION - Healthy ratio but flat volume")
    print("─" * 80)
    print("Setup: volume=$50k (constant), liquidity=$50k")
    print("Expected: ratio=1.0 (healthy), but no acceleration → should FAIL")
    
    mock_data_flat = [
        {'date': 30 - i, 'dailyVolumeUSD': 50000, 'totalLiquidityUSD': 50000}
        for i in range(30)
    ]
    
    metrics_flat = calculate_volume_metrics_from_daily_data(mock_data_flat)
    
    print(f"\nCalculated Metrics:")
    print(f"  volume_ratio:         {metrics_flat['volume_ratio']:.3f}")
    print(f"  acceleration_factor:  {metrics_flat['acceleration_factor']:.2f}x")
    print(f"  is_accelerating:      {metrics_flat['is_accelerating']}")
    
    print(f"\nRatio Classification:")
    print(f"  ✅ ratio_healthy:     {metrics_flat['volume_ratio_healthy']}")
    
    passed, reason = apply_volume_filters(metrics_flat)
    print(f"\n{'✓' if passed else '✗'} Filter Result: {'PASS' if passed else 'FAIL'}")
    print(f"  Reason: {reason}")
    
    print(f"\n📊 Strategy requires BOTH healthy ratio AND acceleration")
    
    assert passed == False, "Test 4 should FAIL (no acceleration)"
    assert metrics_flat['volume_ratio_healthy'] == True
    assert metrics_flat['is_accelerating'] == False
    print("\n✅ Test Case 4: PASSED")
    
    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nSummary of Volume Ratio Health Check Logic:")
    print("  1. ✅ 0.5 < ratio < 3.0 + acceleration → PASS with +5 bonus")
    print("  2. ⚠️  ratio > 3.0 + acceleration → PASS with warning (no bonus)")
    print("  3. ❌ ratio < 0.5 → IMMEDIATE FAIL (dead token)")
    print("  4. No acceleration → FAIL (regardless of ratio)")
    print("\nImplementation Status: COMPLETE ✅")
    print("=" * 80)


if __name__ == "__main__":
    test_volume_ratio_health_check()
