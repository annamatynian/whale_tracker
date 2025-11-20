#!/usr/bin/env python3
"""
Quick test for the fixed alert threshold bug
"""
import sys
import os
sys.path.append('src')

from data_analyzer import ImpermanentLossCalculator

def test_bug_fix():
    """Test that the alert threshold bug is fixed."""
    print("🧪 TESTING FIXED BUG: Alert Threshold Logic")
    print("=" * 50)
    
    calculator = ImpermanentLossCalculator()
    
    # Test 1: IL above threshold should trigger alert
    print("\n📊 Test 1: IL 8% vs threshold 5% (should trigger alert)")
    result = calculator.check_alert_thresholds(
        current_il=0.08,  # 8% IL (positive loss)
        position_config={'il_alert_threshold': 0.05}  # 5% threshold
    )
    
    print(f"   Alert triggered: {result['il_threshold_crossed']}")
    print(f"   Current IL: {result['current_il']:.1%}")
    print(f"   Threshold: {result['threshold']:.1%}")
    print(f"   Severity: {result['severity']}")
    
    if result['il_threshold_crossed']:
        print("   ✅ CORRECT: Alert triggered when IL > threshold")
    else:
        print("   ❌ BUG STILL EXISTS: Alert should trigger!")
        return False
    
    # Test 2: IL below threshold should NOT trigger alert  
    print("\n📊 Test 2: IL 3% vs threshold 5% (should NOT trigger)")
    result = calculator.check_alert_thresholds(
        current_il=0.03,  # 3% IL
        position_config={'il_alert_threshold': 0.05}  # 5% threshold
    )
    
    print(f"   Alert triggered: {result['il_threshold_crossed']}")
    print(f"   Current IL: {result['current_il']:.1%}")
    print(f"   Severity: {result['severity']}")
    
    if not result['il_threshold_crossed']:
        print("   ✅ CORRECT: Alert NOT triggered when IL < threshold")
    else:
        print("   ❌ ERROR: Alert should NOT trigger!")
        return False
    
    # Test 3: Severity levels
    print("\n📊 Test 3: Severity levels")
    test_cases = [
        (0.005, 'low'),
        (0.03, 'medium'),
        (0.08, 'high'),
        (0.15, 'critical')
    ]
    
    all_severity_correct = True
    for il_val, expected in test_cases:
        severity = calculator._get_il_severity(il_val)
        status = "✅" if severity == expected else "❌"
        print(f"   {status} IL {il_val:.1%} -> {severity} (expected: {expected})")
        if severity != expected:
            all_severity_correct = False
    
    if all_severity_correct:
        print("   ✅ All severity levels correct")
    else:
        print("   ❌ Some severity levels incorrect")
        return False
    
    print(f"\n🎉 SUCCESS: BUG IS FIXED!")
    print("✅ Alert threshold logic now works correctly")
    print("✅ IL values are properly handled as positive numbers")
    print("✅ Severity categorization works with positive IL values")
    
    return True

if __name__ == "__main__":
    success = test_bug_fix()
    if success:
        print(f"\n🚀 Ready to commit fix!")
        exit(0)
    else:
        print(f"\n❌ Bug fix needs more work")
        exit(1)
