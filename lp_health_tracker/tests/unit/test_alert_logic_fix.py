#!/usr/bin/env python3
"""
Quick test script to verify Alert Logic fixes.
Tests Category 1: Alert Logic Bugs
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_analyzer import ImpermanentLossCalculator, RiskAssessment


def test_alert_threshold_boundary_cases():
    """Test the exact scenarios that were failing."""
    print("🔧 Testing: Alert Threshold Boundary Cases")
    
    calculator = ImpermanentLossCalculator()
    
    # Test case 1: IL равен порогу (should NOT alert)
    current_il = -0.05  # Точно -5%
    position_config = {"il_alert_threshold": 0.05}  # 5% порог
    
    result = calculator.check_alert_thresholds(current_il, position_config)
    
    expected_no_alert = False  # Should NOT alert when equal
    actual = result['il_threshold_crossed']
    
    print(f"   IL equal to threshold: IL=-5%, threshold=5%")
    print(f"   Expected alert: {expected_no_alert}, Got: {actual}")
    
    if actual == expected_no_alert:
        print("   ✅ PASS: No alert when IL equals threshold")
    else:
        print("   ❌ FAIL: Wrong alert behavior")
        return False
    
    # Test case 2: IL чуть больше порога (should alert)
    current_il = -0.0501  # Чуть больше -5%
    result = calculator.check_alert_thresholds(current_il, position_config)
    
    expected_alert = True  # Should alert when above threshold
    actual = result['il_threshold_crossed']
    
    print(f"   IL above threshold: IL=-5.01%, threshold=5%")
    print(f"   Expected alert: {expected_alert}, Got: {actual}")
    
    if actual == expected_alert:
        print("   ✅ PASS: Alert when IL above threshold")
        return True
    else:
        print("   ❌ FAIL: Should alert when IL above threshold")
        return False


def test_different_risk_category_thresholds():
    """Test different risk categories."""
    print("\n🔧 Testing: Different Risk Category Thresholds")
    
    calculator = ImpermanentLossCalculator()
    
    test_cases = [
        ("USDC", "USDT", -0.003, False, "0.3% IL vs 0.5% threshold"),
        ("USDC", "USDT", -0.007, True, "0.7% IL vs 0.5% threshold"),
        ("WETH", "USDC", -0.01, False, "1% IL vs 2% threshold"),
        ("WETH", "USDC", -0.03, True, "3% IL vs 2% threshold"),
    ]
    
    all_passed = True
    
    for token_a, token_b, current_il, should_alert, description in test_cases:
        # Get risk category and threshold
        risk_category = RiskAssessment.get_risk_category(token_a, token_b)
        threshold = RiskAssessment.get_recommended_il_threshold(risk_category)
        
        position_config = {"il_alert_threshold": threshold}
        result = calculator.check_alert_thresholds(current_il, position_config)
        
        actual_alert = result['il_threshold_crossed']
        
        print(f"   {token_a}-{token_b}: {description}")
        print(f"   Risk category: {risk_category}, Threshold: {threshold:.1%}")
        print(f"   Expected alert: {should_alert}, Got: {actual_alert}")
        
        if actual_alert == should_alert:
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL")
            all_passed = False
        print()
    
    return all_passed


def main():
    """Run all Category 1 tests."""
    print("🧪 TESTING CATEGORY 1: Alert Logic Bugs")
    print("=" * 50)
    
    # Test 1: Boundary cases
    test1_passed = test_alert_threshold_boundary_cases()
    
    # Test 2: Risk categories
    test2_passed = test_different_risk_category_thresholds()
    
    # Results
    print("=" * 50)
    print("📊 RESULTS:")
    print(f"   Alert Threshold Boundary Cases: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Risk Category Thresholds: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL CATEGORY 1 TESTS PASSED!")
        print("Ready to commit fix and move to Category 2.")
        return True
    else:
        print("\n💥 SOME TESTS STILL FAILING!")
        print("Need to investigate further.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
