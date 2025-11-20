#!/usr/bin/env python3
"""
Простые тесты для GasCostCalculator - запуск без pytest
=========================================================

Запустите командой: python test_gas_simple.py
"""

import sys
import os

# Добавляем src в PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'src'))

def test_web3_math_basic():
    """Тест 1: Базовая математика газа с Web3"""
    print("🧮 Тест 1: Базовая математика газа...")
    
    try:
        from web3 import Web3
        
        # Тестовые данные
        gas_used = 150000      # 150k газа (типично для добавления ликвидности)
        gas_price_gwei = 20    # 20 Gwei
        eth_price_usd = 3000.0 # $3000 за ETH
        
        # Шаг 1: Gwei -> Wei
        gas_price_wei = Web3.to_wei(gas_price_gwei, 'gwei')
        
        # Шаг 2: Общая стоимость в Wei
        total_cost_wei = gas_used * gas_price_wei
        
        # Шаг 3: Wei -> ETH
        cost_eth = float(Web3.from_wei(total_cost_wei, 'ether'))
        
        # Шаг 4: ETH -> USD
        cost_usd = cost_eth * eth_price_usd
        
        print(f"   ✅ {gas_used:,} газа × {gas_price_gwei} Gwei = {cost_eth:.6f} ETH = ${cost_usd:.2f}")
        
        # Проверка: ожидаем ~$9.00
        expected = 9.0
        if abs(cost_usd - expected) < 0.1:
            print("   ✅ ПРОЙДЕН: Математика корректна")
            return True
        else:
            print(f"   ❌ ПРОВАЛЕН: Ожидали ~${expected:.2f}, получили ${cost_usd:.2f}")
            return False
            
    except Exception as e:
        print(f"   ❌ ОШИБКА: {e}")
        return False

def test_gas_estimator_import():
    """Тест 2: Импорт GasEstimator"""
    print("\n📋 Тест 2: Импорт GasEstimator...")
    
    try:
        from src.gas_cost_calculator import GasEstimator
        
        # Получаем список операций
        operations = GasEstimator.get_supported_operations()
        
        print(f"   ✅ Найдено операций: {len(operations)}")
        
        # Показываем первые 3
        for i, op in enumerate(operations[:3]):
            print(f"   - {op}")
        
        # Проверяем наличие ключевых операций
        required_ops = ['uniswap_v2_add_liquidity', 'erc20_approve']
        missing = [op for op in required_ops if op not in operations]
        
        if not missing:
            print("   ✅ ПРОЙДЕН: Все необходимые операции присутствуют")
            return True
        else:
            print(f"   ❌ ПРОВАЛЕН: Отсутствуют операции: {missing}")
            return False
            
    except Exception as e:
        print(f"   ❌ ОШИБКА: {e}")
        return False

def test_gas_calculator_creation():
    """Тест 3: Создание GasCostCalculator с mock Web3Manager"""
    print("\n🏗️ Тест 3: Создание GasCostCalculator...")
    
    try:
        from src.gas_cost_calculator import GasCostCalculator
        from unittest.mock import Mock
        
        # Создаем mock Web3Manager
        mock_web3_manager = Mock()
        mock_web3_manager.get_transaction_receipt = Mock(return_value=None)
        
        # Создаем калькулятор
        calculator = GasCostCalculator(mock_web3_manager)
        
        print("   ✅ GasCostCalculator создан успешно")
        
        # Проверяем методы
        if hasattr(calculator, 'calculate_tx_cost_usd'):
            print("   ✅ Метод calculate_tx_cost_usd найден")
        else:
            print("   ❌ Метод calculate_tx_cost_usd НЕ найден")
            return False
            
        if hasattr(calculator, 'get_gas_cost_summary'):
            print("   ✅ Метод get_gas_cost_summary найден")
        else:
            print("   ❌ Метод get_gas_cost_summary НЕ найден")
            return False
        
        print("   ✅ ПРОЙДЕН: GasCostCalculator создается и имеет нужные методы")
        return True
        
    except Exception as e:
        print(f"   ❌ ОШИБКА: {e}")
        return False

def test_gas_cost_summary():
    """Тест 4: Функция summary для позиций"""
    print("\n📊 Тест 4: Gas cost summary...")
    
    try:
        from src.gas_cost_calculator import GasCostCalculator
        from unittest.mock import Mock
        
        # Создаем калькулятор
        mock_web3_manager = Mock()
        calculator = GasCostCalculator(mock_web3_manager)
        
        # Тестовые позиции
        positions = [
            {
                'name': 'Position 1',
                'gas_costs_usd': 25.0,
                'gas_costs_calculated': True
            },
            {
                'name': 'Position 2',
                'gas_costs_usd': 15.0,
                'gas_costs_calculated': False
            }
        ]
        
        # Получаем summary
        summary = calculator.get_gas_cost_summary(positions)
        
        print(f"   ✅ Summary получен: {len(summary)} полей")
        print(f"   - Всего позиций: {summary.get('total_positions', 'N/A')}")
        print(f"   - Рассчитанных: {summary.get('calculated_positions', 'N/A')}")
        print(f"   - Общая стоимость газа: ${summary.get('total_gas_costs_usd', 'N/A')}")
        
        # Проверки
        if summary.get('total_positions') == 2:
            print("   ✅ Правильное количество позиций")
        else:
            print("   ❌ Неправильное количество позиций")
            return False
            
        if summary.get('total_gas_costs_usd') == 40.0:  # 25 + 15
            print("   ✅ Правильная общая стоимость")
        else:
            print(f"   ❌ Неправильная общая стоимость: {summary.get('total_gas_costs_usd')}")
            return False
        
        print("   ✅ ПРОЙДЕН: Gas cost summary работает корректно")
        return True
        
    except Exception as e:
        print(f"   ❌ ОШИБКА: {e}")
        return False

def main():
    """Запуск всех тестов"""
    print("🚀 Запуск простых тестов GasCostCalculator...\n")
    print("=" * 60)
    
    tests = [
        test_web3_math_basic,
        test_gas_estimator_import,
        test_gas_calculator_creation,
        test_gas_cost_summary
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"   ❌ КРИТИЧЕСКАЯ ОШИБКА в {test_func.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"📊 ИТОГИ: {sum(results)}/{len(results)} тестов пройдено")
    
    if all(results):
        print("🎉 Все тесты ПРОЙДЕНЫ! GasCostCalculator готов к интеграции.")
        return 0
    else:
        print("❌ Некоторые тесты ПРОВАЛЕНЫ. Проверьте вывод выше.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\nКод завершения: {exit_code}")
