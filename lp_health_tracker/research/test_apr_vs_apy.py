#!/usr/bin/env python3
"""
APR vs APY Comparison Test
==========================

Тестирует разницу между простым процентом (APR) и сложным процентом (APY)
для понимания влияния на наши расчеты fees в LP Health Tracker.

Основной вопрос: Насколько критично использование APY вместо APR в формуле?
"""

import math

def calculate_simple_interest(principal, apr, days):
    """Расчет простого процента (наш текущий метод)."""
    return principal * (apr / 365) * days

def calculate_compound_interest(principal, apr, days):
    """Расчет сложного процента (теоретический APY)."""
    daily_rate = apr / 365
    return principal * (math.pow(1 + daily_rate, days) - 1)

def test_apr_vs_apy_comparison():
    """Основной тест сравнения APR vs APY."""
    print("🧪 APR vs APY COMPARISON TEST")
    print("=" * 50)
    
    test_scenarios = [
        # (investment, apr, days, description)
        (1000.0, 0.15, 30, "WETH-USDC: 30 дней, 15% APR"),
        (1000.0, 0.15, 45, "WETH-USDC: 45 дней, 15% APR"),
        (1000.0, 0.15, 365, "WETH-USDC: 1 год, 15% APR"),
        (1000.0, 0.50, 30, "Экстремальный: 30 дней, 50% APR"),
        (500.0, 0.015, 60, "Стейблкоин: 60 дней, 1.5% APR"),
    ]
    
    for i, (investment, apr, days, description) in enumerate(test_scenarios, 1):
        print(f"\n{i}️⃣ {description}")
        print("-" * 40)
        
        # Расчеты
        simple_earnings = calculate_simple_interest(investment, apr, days)
        compound_earnings = calculate_compound_interest(investment, apr, days)
        
        difference_usd = compound_earnings - simple_earnings
        difference_percentage = (difference_usd / simple_earnings) * 100 if simple_earnings > 0 else 0
        
        print(f"💰 Инвестиция: ${investment:,.2f}")
        print(f"📅 Период: {days} дней")
        print(f"📊 APR: {apr:.1%}")
        print(f"")
        print(f"✅ APR (простой процент): ${simple_earnings:,.4f}")
        print(f"📈 APY (сложный процент): ${compound_earnings:,.4f}")
        print(f"")
        print(f"💸 Разница: ${difference_usd:,.4f} ({difference_percentage:.4f}%)")
        
        # Оценка критичности
        if difference_percentage < 1:
            print("🟢 Разница незначительна (< 1%)")
        elif difference_percentage < 5:
            print("🟡 Разница заметна, но приемлема (1-5%)")
        else:
            print("🔴 Разница существенна (> 5%)")

def test_our_project_scenarios():
    """Тест на основе реальных данных из нашего проекта."""
    print("\n\n🎯 ТЕСТ НА ОСНОВЕ НАШЕГО ПРОЕКТА")
    print("=" * 50)
    
    # Данные из наших positions.json
    project_scenarios = [
        {
            "name": "WETH-USDC (текущий тест)",
            "investment": 400.0,  # initial_liquidity_a * price_a + initial_liquidity_b * price_b
            "apr": 0.15,          # Mock APR из нашего проекта
            "days": 45            # days_held_mock из конфигурации
        },
        {
            "name": "WETH-DAI (текущий тест)",
            "investment": 200.0,
            "apr": 0.15,          # Предполагаемый APR
            "days": 30
        },
        {
            "name": "USDC-USDT (текущий тест)",
            "investment": 1000.0,
            "apr": 0.015,         # Mock APR для стейблкоинов
            "days": 60
        }
    ]
    
    total_simple = 0
    total_compound = 0
    
    for scenario in project_scenarios:
        print(f"\n📊 {scenario['name']}")
        print("-" * 30)
        
        simple = calculate_simple_interest(scenario['investment'], scenario['apr'], scenario['days'])
        compound = calculate_compound_interest(scenario['investment'], scenario['apr'], scenario['days'])
        
        difference = compound - simple
        
        print(f"Fees (APR метод): ${simple:.2f}")
        print(f"Fees (APY метод): ${compound:.2f}")
        print(f"Разница: ${difference:.2f}")
        
        total_simple += simple
        total_compound += compound
    
    portfolio_difference = total_compound - total_simple
    
    print(f"\n📈 ПОРТФЕЛЬ ИТОГО:")
    print(f"Общие fees (APR): ${total_simple:.2f}")
    print(f"Общие fees (APY): ${total_compound:.2f}")
    print(f"Общая разница: ${portfolio_difference:.2f}")
    
    print(f"\n💡 Вывод для нашего проекта:")
    if portfolio_difference < 1:
        print("🟢 Использование APY вместо APR не критично для точности")
    else:
        print(f"🟡 Разница ${portfolio_difference:.2f} может быть заметна, но приемлема для MVP")

def test_extreme_scenarios():
    """Тест экстремальных сценариев для понимания границ."""
    print("\n\n🔥 ЭКСТРЕМАЛЬНЫЕ СЦЕНАРИИ")
    print("=" * 50)
    
    extreme_cases = [
        (10000, 1.0, 365, "Огромный APR: 100% на год"),
        (1000, 0.15, 1095, "Долгосрочно: 15% на 3 года"),
        (100, 0.50, 7, "Короткосрочно: 50% на неделю"),
    ]
    
    for investment, apr, days, description in extreme_cases:
        print(f"\n⚡ {description}")
        
        simple = calculate_simple_interest(investment, apr, days)
        compound = calculate_compound_interest(investment, apr, days)
        difference_pct = ((compound - simple) / simple) * 100
        
        print(f"APR: ${simple:.2f} | APY: ${compound:.2f} | Разница: {difference_pct:.1f}%")

def main():
    """Главная функция теста."""
    print("🧪 TESTING APR vs APY - Критичность для LP Health Tracker")
    print("=" * 65)
    print("Цель: Понять влияние использования APY вместо APR в расчетах fees")
    print("=" * 65)
    
    # Основные тесты
    test_apr_vs_apy_comparison()
    
    # Тесты на основе нашего проекта
    test_our_project_scenarios()
    
    # Экстремальные сценарии
    test_extreme_scenarios()
    
    print("\n" + "=" * 65)
    print("🎯 ЗАКЛЮЧЕНИЕ:")
    print("Для коротких периодов (30-60 дней) разница между APR и APY")
    print("незначительна и не влияет на практическую точность расчетов.")
    print("Использование APY из DeFi Llama API в формуле APR приемлемо для MVP.")
    print("=" * 65)

if __name__ == "__main__":
    main()
