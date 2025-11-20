#!/usr/bin/env python3
"""
Быстрая проверка исправлений тестов
"""
import sys
import os
sys.path.insert(0, 'src')

try:
    from src.data_analyzer import NetPnLCalculator
    
    print("✅ Тестируем исправления:")
    
    # 1. Проверяем что NetPnLCalculator существует
    calculator = NetPnLCalculator()
    print("✅ NetPnLCalculator создан успешно")
    
    # 2. Проверяем что calculate_earned_fees работает с правильными параметрами
    fees = calculator.calculate_earned_fees(
        initial_investment_usd=1000.0,
        apr=0.15,
        days_held=30
    )
    print(f"✅ calculate_earned_fees работает: ${fees:.2f}")
    
    # 3. Проверяем calculate_net_pnl
    net_pnl = calculator.calculate_net_pnl(
        current_lp_value_usd=1050.0,
        earned_fees_usd=fees,
        initial_investment_usd=1000.0,
        gas_costs_usd=50.0
    )
    print(f"✅ calculate_net_pnl работает: ${net_pnl['net_pnl_usd']:.2f}")
    
    print("\n🎉 ВСЕ ИСПРАВЛЕНИЯ РАБОТАЮТ!")
    print("Теперь тесты должны пройти без ошибок TypeError")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
