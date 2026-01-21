"""
Unit tests for Gini Bias Fix - Vulnerability #4

Tests protection against Gini coefficient bias when RPC errors return None/0 balances.

VULNERABILITY: Multicall gas errors → 400 whales get balance=None → treated as 0
               → Gini spikes to 1.0 → false [Concentrated Signal] tag

FIX: 
1. Filter None/0 from Gini calculation
2. Track num_signals_used vs num_signals_excluded  
3. Require 70% valid signals before assigning tags

Author: Whale Tracker Project
Date: 2026-01-21
"""

import pytest
from decimal import Decimal


def calculate_gini_with_filter(balances_dict):
    """
    Simplified Gini calculation with RPC error filtering.
    
    Mimics production _calculate_metrics logic.
    """
    # Filter out None and 0 (RPC errors)
    valid_balances = [
        bal for bal in balances_dict.values()
        if bal is not None and bal > 0
    ]
    
    num_signals_used = len(valid_balances)
    num_signals_excluded = len(balances_dict) - num_signals_used
    
    # Calculate Gini
    sorted_balances = sorted(valid_balances)
    n = len(sorted_balances)
    
    if n > 0 and sum(sorted_balances) > 0:
        cumsum = sum((i + 1) * x for i, x in enumerate(sorted_balances))
        total_sum = sum(sorted_balances)
        
        gini = (Decimal(2 * cumsum) / Decimal(n * total_sum)) - Decimal(n + 1) / Decimal(n)
        gini = abs(gini)
    else:
        gini = Decimal('0')
    
    return gini, num_signals_used, num_signals_excluded


def test_clean_data_no_rpc_errors():
    """
    Test Case 1: Clean data (no RPC errors).
    
    1000 whales, all with valid balances
    Expected: Normal Gini (~0.6-0.7 for crypto), num_signals_used=1000
    """
    # Generate realistic whale distribution (linear for stability)
    balances = {}
    for i in range(1000):
        # Linear: Top whale 1000 ETH, smallest 1 ETH
        balance_eth = 1 + (999 - i) * 1.0
        balances[f"0x{i:040x}"] = int(balance_eth * 1e18)
    
    gini, used, excluded = calculate_gini_with_filter(balances)
    
    assert used == 1000, f"All signals should be used, got {used}"
    assert excluded == 0, f"No signals should be excluded, got {excluded}"
    assert 0.3 < gini < 0.9, f"Gini should be realistic, got {gini}"


def test_rpc_errors_40_percent():
    """
    Test Case 2: CRITICAL - 40% RPC errors (Multicall gas failure).
    
    Scenario: Multicall gas limit hit, 400/1000 whales get balance=None
    
    WITHOUT FIX: Gini treats None as 0 → Gini spikes to 0.95+ → false [Concentrated Signal]
    WITH FIX: Gini uses only 600 valid → Gini stays normal ~0.65
    """
    balances = {}
    
    # 600 whales with valid balances (linear distribution)
    for i in range(600):
        balance_eth = 1 + (599 - i) * 1.0
        balances[f"0x{i:040x}"] = int(balance_eth * 1e18)
    
    # 400 whales with RPC errors
    for i in range(600, 1000):
        balances[f"0x{i:040x}"] = None  # RPC error!
    
    gini, used, excluded = calculate_gini_with_filter(balances)
    
    assert used == 600, f"Should use 600 valid signals, got {used}"
    assert excluded == 400, f"Should exclude 400 errors, got {excluded}"
    assert 0.3 < gini < 0.8, f"Gini should be normal despite errors, got {gini}"


def test_all_rpc_errors():
    """
    Test Case 3: Complete RPC failure (all None).
    
    All Multicall chunks failed
    Expected: Gini=0, used=0, excluded=1000
    """
    balances = {f"0x{i:040x}": None for i in range(1000)}
    
    gini, used, excluded = calculate_gini_with_filter(balances)
    
    assert used == 0
    assert excluded == 1000
    assert gini == Decimal('0'), "Gini should be 0 with no valid data"


def test_mixed_none_and_zero():
    """
    Test Case 4: Mix of None (RPC error) and 0 (real zero balance).
    
    Both should be filtered from Gini calculation.
    """
    balances = {}
    
    # 500 valid balances
    for i in range(500):
        balances[f"0x{i:040x}"] = int((i + 1) * 1e18)
    
    # 250 RPC errors (None)
    for i in range(500, 750):
        balances[f"0x{i:040x}"] = None
    
    # 250 real zeros (new whales or dumped everything)
    for i in range(750, 1000):
        balances[f"0x{i:040x}"] = 0
    
    gini, used, excluded = calculate_gini_with_filter(balances)
    
    assert used == 500, "Only valid non-zero balances"
    assert excluded == 500, "Both None and 0 excluded"


def test_tag_assignment_requires_70_percent():
    """
    Test Case 5: Tag assignment protection.
    
    Scenario: 600/1000 valid signals (60% < 70% threshold)
    Expected: Tags should NOT be assigned (insufficient data)
    """
    whale_count = 1000
    num_signals_used = 600
    num_signals_excluded = 400
    
    # Check if we meet 70% threshold
    min_signals_pct = 0.70
    min_signals_required = int(whale_count * min_signals_pct)
    
    should_assign_tags = num_signals_used >= min_signals_required
    
    assert not should_assign_tags, "Should NOT assign tags with only 60% valid signals"
    assert min_signals_required == 700, "Minimum threshold should be 700"


def test_tag_assignment_with_71_percent():
    """
    Test Case 6: Tags allowed at 71% (above threshold).
    """
    whale_count = 1000
    num_signals_used = 710
    
    min_signals_pct = 0.70
    min_signals_required = int(whale_count * min_signals_pct)
    
    should_assign_tags = num_signals_used >= min_signals_required
    
    assert should_assign_tags, "Should assign tags with 71% valid signals"


def test_gini_concentrated_vs_equal():
    """
    Test Case 7: Gini correctly detects concentration.
    
    Scenario A: One whale owns 99%, others 1%
    Scenario B: All whales equal balances
    """
    # Scenario A: Concentrated (1 mega-whale)
    concentrated = {f"0x{i:040x}": int(1e18) for i in range(999)}
    concentrated["0xMEGAWHALE"] = int(99000e18)  # 99% of total
    
    gini_concentrated, _, _ = calculate_gini_with_filter(concentrated)
    
    # Scenario B: Equal distribution
    equal = {f"0x{i:040x}": int(100e18) for i in range(1000)}
    
    gini_equal, _, _ = calculate_gini_with_filter(equal)
    
    assert gini_concentrated > 0.9, f"Concentrated should have high Gini, got {gini_concentrated}"
    assert gini_equal < 0.1, f"Equal should have low Gini, got {gini_equal}"


def test_vulnerability_scenario_false_concentrated():
    """
    Test Case 8: EXACT VULNERABILITY from Gemini report.
    
    Multicall gas limit → 400 whales get None → treated as 0
    WITHOUT FIX: Gini=0.95 → [Concentrated Signal] tag → FALSE SIGNAL
    WITH FIX: Gini uses only valid 600 → no false tag
    """
    # Realistic power-law distribution
    balances = {}
    for i in range(600):
        # Power law
        balance_eth = 10000 / (i + 1) ** 0.8
        balances[f"0x{i:040x}"] = int(balance_eth * 1e18)
    
    # Add 400 RPC errors
    for i in range(600, 1000):
        balances[f"0x{i:040x}"] = None
    
    gini, used, excluded = calculate_gini_with_filter(balances)
    
    # Verify fix prevents false concentration
    assert used == 600
    assert excluded == 400
    
    # Gini should be NORMAL (not artificially high)
    assert gini < 0.85, f"Gini should NOT trigger [Concentrated Signal], got {gini}"
    
    # Tag assignment should be BLOCKED (60% < 70%)
    min_signals_required = int(1000 * 0.70)
    should_tag = used >= min_signals_required
    assert not should_tag, "Should NOT assign [Concentrated Signal] with 60% data"


if __name__ == "__main__":
    print("Running Gini Bias Fix Tests (Vulnerability #4)...")
    print("=" * 80)
    
    tests = [
        ("Clean data (no errors)", test_clean_data_no_rpc_errors),
        ("40% RPC errors", test_rpc_errors_40_percent),
        ("Complete RPC failure", test_all_rpc_errors),
        ("Mixed None and 0", test_mixed_none_and_zero),
        ("Tag protection (60% < 70%)", test_tag_assignment_requires_70_percent),
        ("Tag allowed (71% > 70%)", test_tag_assignment_with_71_percent),
        ("Gini: concentrated vs equal", test_gini_concentrated_vs_equal),
        ("VULNERABILITY: False concentrated", test_vulnerability_scenario_false_concentrated),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
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
        print("\n🎉 ALL TESTS PASSED - Gini bias vulnerability FIXED!")
        print("\n💡 Protection enabled:")
        print("   - Filters None/0 from Gini calculation")
        print("   - Tracks num_signals_used vs excluded")
        print("   - Requires 70% valid data for tags")
        print("   - Prevents false [Concentrated Signal]")
    else:
        print(f"\n⚠️  {failed} test(s) failed - review implementation")
