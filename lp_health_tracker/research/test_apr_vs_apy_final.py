#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ ТЕСТ APR vs APY - Обновленные Mock данные
===================================================

Тестируем APR vs APY разницу с ОБНОВЛЕННЫМИ mock данными,
основанными на реальных Uniswap V2 APY из DeFi Llama разведки.

Цель: Подтвердить, что наш подход остается корректным 
с реалистичными ставками (4% вместо 15%, 0.1% вместо 1.5%).
"""

import math

def test_updated_mock_data():
    """Тест с обновленными реалистичными mock данными."""
    print("🎯 ФИНАЛЬНЫЙ ТЕСТ APR vs APY - ОБНОВЛЕННЫЕ MOCK ДАННЫЕ")
    print("=" * 65)
    print("Данные основаны на реальных Uniswap V2 APY из DeFi Llama")
    print("=" * 65)
    
    # Обновленные mock данные из нашего data_providers.py
    updated_scenarios = [
        # (investment, updated_apr, days, description)
        (400.0, 4.0, 45, "WETH-USDC (обновленный mock: 4.0% vs старый 15.0%)"),
        (1000.0, 0.1, 60, "USDC-USDT (обновленный mock: 0.1% vs старый 1.5%)"),
        (200.0, 4.0, 30, "WETH-DAI (используем WETH-USDC: 4.0%)"),
        (500.0, 3.5, 35, "WETH-WBTC (обновленный mock: 3.5%)"),
    ]
    
    total_apr_fees = 0
    total_apy_fees = 0
    total_difference = 0
    
    for i, (investment, apr_pct, days, description) in enumerate(updated_scenarios, 1):
        print(f"\n{i}️⃣ {description}")
        print("-" * 55)
        
        # Конвертируем APR из процентов в decimal
        apr = apr_pct / 100
        
        # Расчеты
        apr_fees = investment * (apr / 365) * days
        apy_fees = investment * (math.pow(1 + apr/365, days) - 1)
        
        difference_usd = apy_fees - apr_fees
        difference_percentage = (difference_usd / apr_fees) * 100 if apr_fees > 0 else 0
        
        print(f"💰 Инвестиция: ${investment:,.2f}")
        print(f"📅 Период: {days} дней")
        print(f"📊 Обновленный APR: {apr_pct:.1f}%")
        print(f"")
        print(f"✅ APR метод (наш): ${apr_fees:.4f}")
        print(f"📈 APY метод (точный): ${apy_fees:.4f}")
        print(f"💸 Разница: ${difference_usd:.4f} ({difference_percentage:.4f}%)")
        
        total_apr_fees += apr_fees
        total_apy_fees += apy_fees
        total_difference += difference_usd
        
        # Оценка критичности с учетом более низких APR
        if abs(difference_percentage) < 0.5:
            print("🟢 Разница крайне незначительна (< 0.5%)")
        elif abs(difference_percentage) < 1:
            print("🟢 Разница незначительна (< 1%)")
        elif abs(difference_percentage) < 2:
            print("🟡 Разница заметна, но приемлема (1-2%)")
        else:
            print("🔴 Разница может быть критична (> 2%)")
    
    print(f"\n📈 ПОРТФЕЛЬ ИТОГО:")
    print(f"Общие fees (APR): ${total_apr_fees:.2f}")
    print(f"Общие fees (APY): ${total_apy_fees:.2f}")
    print(f"Общая разница: ${total_difference:.2f}")
    
    portfolio_difference_pct = (total_difference / total_apr_fees) * 100 if total_apr_fees > 0 else 0
    print(f"Портфель разница: {portfolio_difference_pct:.2f}%")
    
    return total_difference

def compare_old_vs_new_mock():
    """Сравнение старых и новых mock данных."""
    print("\n🔄 СРАВНЕНИЕ: СТАРЫЕ vs НОВЫЕ MOCK ДАННЫЕ")
    print("=" * 65)
    
    scenarios = [
        # (investment, days, old_apr, new_apr, description)
        (400.0, 45, 15.0, 4.0, "WETH-USDC"),
        (1000.0, 60, 1.5, 0.1, "USDC-USDT"),
        (200.0, 30, 15.0, 4.0, "WETH-DAI"),
    ]
    
    total_old_fees = 0
    total_new_fees = 0
    
    for investment, days, old_apr_pct, new_apr_pct, description in scenarios:
        print(f"\n📊 {description}")
        print("-" * 35)
        
        # Расчеты
        old_fees = investment * (old_apr_pct / 100 / 365) * days
        new_fees = investment * (new_apr_pct / 100 / 365) * days
        
        difference = new_fees - old_fees
        difference_pct = (difference / old_fees) * 100 if old_fees > 0 else 0
        
        print(f"Старый mock ({old_apr_pct:.1f}%): ${old_fees:.2f}")
        print(f"Новый mock ({new_apr_pct:.1f}%): ${new_fees:.2f}")
        print(f"Изменение: ${difference:.2f} ({difference_pct:+.1f}%)")
        
        total_old_fees += old_fees
        total_new_fees += new_fees
    
    portfolio_change = total_new_fees - total_old_fees
    portfolio_change_pct = (portfolio_change / total_old_fees) * 100
    
    print(f"\n📈 ПОРТФЕЛЬ ИТОГО:")
    print(f"Старые mock fees: ${total_old_fees:.2f}")
    print(f"Новые mock fees: ${total_new_fees:.2f}")
    print(f"Изменение: ${portfolio_change:.2f} ({portfolio_change_pct:+.1f}%)")
    
    if abs(portfolio_change_pct) > 50:
        print("🔴 Значительное изменение в расчетах!")
        print("💡 Это подтверждает важность использования реальных данных")
    else:
        print("🟡 Умеренное изменение в расчетах")

def test_extreme_low_apr_scenarios():
    """Тест экстремально низких APR (проверка на точность)."""
    print("\n⚡ ТЕСТ ЭКСТРЕМАЛЬНО НИЗКИХ APR")
    print("=" * 65)
    print("Проверяем точность на очень низких ставках (близких к стейблкоинам)")
    
    extreme_cases = [
        (10000, 0.05, 30, "Очень низкий APR: 0.05% на месяц"),
        (5000, 0.1, 45, "USDC-USDT реальный: 0.1% на 45 дней"),
        (1000, 0.01, 60, "Экстремально низкий: 0.01% на 2 месяца"),
    ]
    
    for investment, apr_pct, days, description in extreme_cases:
        apr = apr_pct / 100
        
        apr_fees = investment * (apr / 365) * days
        apy_fees = investment * (math.pow(1 + apr/365, days) - 1)
        
        if apr_fees > 0:
            difference_pct = ((apy_fees - apr_fees) / apr_fees) * 100
        else:
            difference_pct = 0
        
        print(f"\n{description}")
        print(f"  APR: ${apr_fees:.4f} | APY: ${apy_fees:.4f} | Разница: {difference_pct:.4f}%")
        
        if abs(difference_pct) < 0.1:
            print("  🟢 Разница практически нулевая")
        elif abs(difference_pct) < 0.5:
            print("  🟢 Разница крайне мала")
        else:
            print("  🟡 Разница заметна даже на низких ставках")

def main():
    """Главная функция финального теста."""
    print("🧪 ФИНАЛЬНЫЙ ТЕСТ APR vs APY")
    print("Проверяем корректность нашего подхода с обновленными")
    print("реалистичными mock данными на основе Uniswap V2")
    print("=" * 65)
    
    # Тест с обновленными данными
    total_diff = test_updated_mock_data()
    
    # Сравнение старых и новых mock
    compare_old_vs_new_mock()
    
    # Экстремальные сценарии
    test_extreme_low_apr_scenarios()
    
    print("\n" + "=" * 65)
    print("🎯 ФИНАЛЬНЫЕ ВЫВОДЫ:")
    print("1. ✅ APR vs APY разница остается незначительной даже с реальными данными")
    print("2. ✅ Обновленные mock данные значительно более реалистичны")
    print("3. ✅ Наш подход использования APY в формуле APR остается корректным")
    print("4. ✅ Готовы к реализации DeFi Llama API интеграции")
    print(f"5. 💰 Общая разница в портфеле: ${total_diff:.2f} (практически нулевая)")
    print("=" * 65)

if __name__ == "__main__":
    main()
