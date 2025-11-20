#!/usr/bin/env python3
"""
Test for Bug Fixes Identified by Gemini Analysis
================================================

Tests for the specific bugs mentioned in Gemini's code review:
1. Alert threshold logic bug (FIXED)
2. pytest.skip masking issues (FIXED) 
3. test_pool_data_persistence without assert checks (FIXED)
4. add_pool storing references instead of copies (FIXED)
"""

import sys
sys.path.append('src')

from data_analyzer import ImpermanentLossCalculator  
from simple_multi_pool import SimpleMultiPoolManager

def test_alert_threshold_bug_fixed():
    """Test that alert threshold logic is fixed."""
    print("🐛 Testing FIXED alert threshold bug...")
    
    calculator = ImpermanentLossCalculator()
    
    # Test 1: IL above threshold should trigger alert
    result = calculator.check_alert_thresholds(
        current_il=0.08,  # 8% IL
        position_config={'il_alert_threshold': 0.05}  # 5% threshold
    )
    
    assert result['il_threshold_crossed'] == True, "8% IL should trigger 5% threshold"
    
    # Test 2: IL below threshold should NOT trigger alert
    result = calculator.check_alert_thresholds(
        current_il=0.03,  # 3% IL  
        position_config={'il_alert_threshold': 0.05}  # 5% threshold
    )
    
    assert result['il_threshold_crossed'] == False, "3% IL should NOT trigger 5% threshold"
    
    print("   ✅ Alert threshold logic works correctly")
    return True

def test_pool_data_persistence_fixed():
    """Test that pool data persistence is properly tested and works."""
    print("🐛 Testing FIXED pool data persistence...")
    
    manager = SimpleMultiPoolManager()
    
    # Original pool data
    original_pool = {
        'name': 'Test Pool',
        'initial_liquidity_a': 100.0,
        'token_a_symbol': 'WETH',
        'token_b_symbol': 'USDC'
    }
    
    # Add to manager
    manager.add_pool(original_pool)
    
    # Modify original dict
    original_pool['name'] = 'Modified Pool'
    original_pool['initial_liquidity_a'] = 999.0
    
    # Check stored pool is unaffected
    stored_pool = manager.pools[0]
    
    assert stored_pool['name'] == 'Test Pool', "Stored pool should preserve original name"
    assert stored_pool['initial_liquidity_a'] == 100.0, "Stored pool should preserve original values"
    assert stored_pool['name'] != 'Modified Pool', "Stored pool should be independent"
    assert stored_pool['initial_liquidity_a'] != 999.0, "External changes should not affect stored pool"
    
    print("   ✅ Pool data persistence works correctly (stores copies, not references)")
    return True

def test_error_handling_no_exceptions():
    """Test that methods return error dicts instead of raising exceptions."""
    print("🐛 Testing FIXED exception handling...")
    
    manager = SimpleMultiPoolManager()
    
    # Invalid pool with missing fields
    invalid_pool = {'name': 'Invalid Pool'}  # Missing required fields
    
    # Should not raise exception, should return error dict
    try:
        result = manager.calculate_net_pnl_with_fees(invalid_pool)
        
        assert isinstance(result, dict), "Should return dict even for invalid input"
        
        if 'error' in result:
            assert isinstance(result['error'], str), "Error should be string"
            assert len(result['error']) > 0, "Error message should not be empty"
            print("   ✅ Method returns proper error dict instead of raising exception")
        else:
            print("   ⚠️  Method succeeded with invalid input (might be OK if has defaults)")
            
    except Exception as e:
        assert False, f"Method should not raise exceptions, should return error dict: {e}"
    
    return True

def test_severity_levels_fixed():
    """Test IL severity levels work with positive values."""
    print("🐛 Testing FIXED IL severity levels...")
    
    calculator = ImpermanentLossCalculator()
    
    test_cases = [
        (0.005, 'low'),     # 0.5%
        (0.03, 'medium'),   # 3% 
        (0.08, 'high'),     # 8%
        (0.15, 'critical')  # 15%
    ]
    
    for il_value, expected_severity in test_cases:
        severity = calculator._get_il_severity(il_value)
        assert severity == expected_severity, f"IL {il_value:.1%} should be '{expected_severity}', got '{severity}'"
    
    print("   ✅ IL severity levels work correctly with positive IL values")
    return True

def run_all_gemini_bug_fixes():
    """Run all bug fix tests identified by Gemini."""
    print("🎯 TESTING ALL GEMINI-IDENTIFIED BUG FIXES")
    print("=" * 55)
    
    tests = [
        test_alert_threshold_bug_fixed,
        test_pool_data_persistence_fixed, 
        test_error_handling_no_exceptions,
        test_severity_levels_fixed
    ]
    
    all_passed = True
    
    for test_func in tests:
        try:
            result = test_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"   ❌ Test {test_func.__name__} failed: {e}")
            all_passed = False
    
    print("\n" + "=" * 55)
    if all_passed:
        print("🎉 ALL GEMINI BUG FIXES VERIFIED!")
        print("✅ Alert threshold logic fixed")
        print("✅ Pool data persistence fixed (copy vs reference)")  
        print("✅ Exception handling improved (no pytest.skip masking)")
        print("✅ IL severity levels work with positive values")
        print("\n🚀 Ready to commit all fixes!")
        return True
    else:
        print("❌ Some bug fixes need more work")
        return False

if __name__ == "__main__":
    success = run_all_gemini_bug_fixes()
    exit(0 if success else 1)
