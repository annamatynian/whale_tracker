#!/usr/bin/env python3
import sys
sys.path.append('src')
from data_analyzer import ImpermanentLossCalculator

calc = ImpermanentLossCalculator()

# Тест 1: 8% IL vs 5% threshold (должен сработать алерт)
result1 = calc.check_alert_thresholds(0.08, {'il_alert_threshold': 0.05})
print("Test 1 - IL 8% vs threshold 5%:")
print(f"  Alert triggered: {result1['il_threshold_crossed']}")
print(f"  Expected: True (8% > 5%)")
print(f"  Status: {'✅ PASS' if result1['il_threshold_crossed'] else '❌ FAIL'}")

# Тест 2: 3% IL vs 5% threshold (НЕ должен сработать алерт)  
result2 = calc.check_alert_thresholds(0.03, {'il_alert_threshold': 0.05})
print("\nTest 2 - IL 3% vs threshold 5%:")
print(f"  Alert triggered: {result2['il_threshold_crossed']}")
print(f"  Expected: False (3% < 5%)")
print(f"  Status: {'✅ PASS' if not result2['il_threshold_crossed'] else '❌ FAIL'}")

print(f"\n🎉 BUG FIX VERIFICATION COMPLETE!")
