#!/usr/bin/env python3
"""
Master Plan Этап 1 - Проверка интеграции
========================================

Тестирует полную реализацию Этапа 1 согласно fees_master_plan.txt:
1. Конфигурация позиций с gas_costs_usd и days_held_mock
2. DataProvider.get_pool_apr() реализация
3. NetPnLCalculator с fees и gas costs  
4. SimpleMultiPoolManager интеграция
"""

import sys
import os
sys.path.append('src')

def test_master_plan_stage1():
    """Полный тест Master Plan Этап 1."""
    print("🎯 Master Plan Stage 1 - Complete Integration Test")
    print("=" * 60)
    
    # 1. Тест конфигурации позиций
    print("\n1️⃣ Testing position configuration...")
    try:
        import json
        with open('data/positions.json', 'r') as f:
            positions = json.load(f)
        
        position = positions[0]  # Первая позиция
        
        # Проверяем наличие новых полей
        assert 'gas_costs_usd' in position, "Missing gas_costs_usd field"
        assert 'days_held_mock' in position, "Missing days_held_mock field"
        
        gas_costs = position['gas_costs_usd']
        days_held = position['days_held_mock']
        
        print(f"   ✅ gas_costs_usd: ${gas_costs}")
        print(f"   ✅ days_held_mock: {days_held} days")
        
    except Exception as e:
        print(f"   ❌ Position config test failed: {e}")
        return False
    
    # 2. Тест DataProvider APR
    print("\n2️⃣ Testing DataProvider APR...")
    try:
        from data_providers import MockDataProvider
        
        provider = MockDataProvider(scenario="mixed_volatility")
        pool_config = {'name': 'WETH-USDC'}
        
        apr = provider.get_pool_apr(pool_config)
        print(f"   ✅ APR for WETH-USDC: {apr:.1%}")
        
        assert apr > 0, "APR should be positive"
        assert isinstance(apr, float), "APR should be float"
        
    except Exception as e:
        print(f"   ❌ DataProvider APR test failed: {e}")
        return False
    
    # 3. Тест NetPnLCalculator
    print("\n3️⃣ Testing NetPnLCalculator...")
    try:
        from data_analyzer import NetPnLCalculator
        
        calculator = NetPnLCalculator()
        
        # Тест fees calculation
        initial_investment = 1000.0
        apr = 0.15  # 15%
        days_held = 30
        
        fees_earned = calculator.calculate_earned_fees(initial_investment, apr, days_held)
        expected_fees = initial_investment * (apr / 365) * days_held
        
        print(f"   ✅ Fees calculation: ${fees_earned:.2f}")
        print(f"   Expected: ${expected_fees:.2f}")
        
        assert abs(fees_earned - expected_fees) < 0.01, "Fees calculation incorrect"
        
        # Тест Net P&L
        current_lp_value = 1050.0
        gas_costs = 75.0
        
        net_pnl_data = calculator.calculate_net_pnl(
            current_lp_value, fees_earned, initial_investment, gas_costs
        )
        
        print(f"   ✅ Net P&L: ${net_pnl_data['net_pnl_usd']:.2f}")
        print(f"   Is profitable: {net_pnl_data['is_profitable']}")
        
        # Проверяем формулу: (Current LP + Fees) - (Initial + Gas)
        expected_net = (current_lp_value + fees_earned) - (initial_investment + gas_costs)
        assert abs(net_pnl_data['net_pnl_usd'] - expected_net) < 0.01, "Net P&L formula incorrect"
        
    except Exception as e:
        print(f"   ❌ NetPnLCalculator test failed: {e}")
        return False
    
    # 4. Тест SimpleMultiPoolManager интеграции
    print("\n4️⃣ Testing SimpleMultiPoolManager integration...")
    try:
        from simple_multi_pool import SimpleMultiPoolManager
        from data_providers import MockDataProvider
        
        # Создаем менеджер с MockDataProvider
        provider = MockDataProvider()
        manager = SimpleMultiPoolManager(provider)
        
        # Загружаем реальные позиции
        success = manager.load_positions_from_json('data/positions.json')
        assert success, "Failed to load positions"
        
        print(f"   ✅ Loaded {manager.count_pools()} positions")
        
        # Тестируем анализ первой позиции
        if manager.pools:
            first_pool = manager.pools[0]
            result = manager.calculate_net_pnl_with_fees(first_pool)
            
            assert 'net_pnl' in result, "Missing net_pnl in result"
            assert 'fees_analysis' in result, "Missing fees_analysis in result"
            
            net_pnl = result['net_pnl']['net_pnl_usd']
            fees_earned = result['current_status']['earned_fees_usd']
            
            print(f"   ✅ Analysis result - Net P&L: ${net_pnl:.2f}")
            print(f"   ✅ Fees earned: ${fees_earned:.2f}")
        
    except Exception as e:
        print(f"   ❌ SimpleMultiPoolManager test failed: {e}")
        return False
    
    # 5. Полный workflow тест
    print("\n5️⃣ Testing complete workflow...")
    try:
        # Анализируем все позиции
        results = manager.analyze_all_pools_with_fees()
        
        assert len(results) > 0, "No analysis results"
        
        # Проверяем что каждый результат содержит необходимые данные
        for i, result in enumerate(results):
            assert 'net_pnl' in result, f"Position {i} missing net_pnl"
            assert 'fees_analysis' in result, f"Position {i} missing fees_analysis"
            assert 'strategy_comparison' in result, f"Position {i} missing strategy_comparison"
        
        print(f"   ✅ Analyzed {len(results)} positions successfully")
        
    except Exception as e:
        print(f"   ❌ Workflow test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 MASTER PLAN STAGE 1 - FULLY IMPLEMENTED!")
    print("✅ All components working according to fees_master_plan.txt")
    print("🚀 Ready for Stage 2: Live Data Integration")
    print("=" * 60)
    
    return True

def show_stage1_summary():
    """Показать резюме что реализовано в Этапе 1."""
    print("\n📋 MASTER PLAN STAGE 1 - IMPLEMENTATION SUMMARY")
    print("-" * 50)
    
    print("\n✅ COMPLETED TASKS:")
    print("1. Position Configuration (data/positions.json):")
    print("   • gas_costs_usd field added")
    print("   • days_held_mock field added")
    
    print("\n2. DataProvider Architecture (src/data_providers.py):")
    print("   • Abstract get_pool_apr() method")
    print("   • MockDataProvider implementation with APR scenarios")
    print("   • APR rates: USDC-USDT(1.5%), WETH-USDC(15%), WETH-WBTC(12%)")
    
    print("\n3. NetPnLCalculator (src/data_analyzer.py):")
    print("   • calculate_earned_fees() - fees = investment * (APR/365) * days")
    print("   • calculate_net_pnl() - Net P&L = (LP + Fees) - (Investment + Gas)")
    print("   • analyze_position_with_fees() - complete position analysis")
    
    print("\n4. SimpleMultiPoolManager Integration:")
    print("   • Uses NetPnLCalculator")
    print("   • Loads positions with fee data")
    print("   • calculate_net_pnl_with_fees() implementation")
    print("   • analyze_all_pools_with_fees() for portfolio analysis")
    
    print("\n🎯 STAGE 1 RESULT:")
    print("Working demo showing IL, P&L, fees impact, gas costs, and Net P&L")
    print("All calculations use mock data without external API dependencies")
    
    print("\n🚀 NEXT: STAGE 2 - Live Data Integration")
    print("• Real prices from CoinGecko API")
    print("• Real APR from DeFi Llama API") 
    print("• Date parsing (replace days_held_mock)")
    print("• Robust error handling")

if __name__ == "__main__":
    # Запускаем полный тест
    success = test_master_plan_stage1()
    
    if success:
        show_stage1_summary()
    else:
        print("\n❌ Some tests failed. Stage 1 needs fixes before Stage 2.")
