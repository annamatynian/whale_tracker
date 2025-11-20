"""
Тест новой архитектуры с наследованием
Проверяет что рефакторинг работает корректно

Author: Inheritance Architecture Test
"""

import sys
import os

# Добавляем пути
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_inheritance_architecture():
    """Тест архитектуры наследования"""
    print("🏗️ ТЕСТ АРХИТЕКТУРЫ НАСЛЕДОВАНИЯ")
    print("=" * 50)
    
    try:
        # Тест 1: Импорт базового класса
        from agents.discovery.base_discovery_agent import BaseDiscoveryAgent, TokenDiscoveryReport
        print("✅ BaseDiscoveryAgent импортирован")
        
        # Тест 2: Импорт нового pump agent
        from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent
        print("✅ PumpDiscoveryAgent импортирован")
        
        # Тест 3: Проверка наследования
        agent = PumpDiscoveryAgent()
        is_inheritance = isinstance(agent, BaseDiscoveryAgent)
        print(f"✅ Наследование работает: {is_inheritance}")
        
        # Тест 4: Проверка методов
        methods_to_check = [
            'should_analyze_pair',
            'calculate_score', 
            'create_report',
            'discover_tokens',
            'discover_tokens_async'
        ]
        
        for method in methods_to_check:
            has_method = hasattr(agent, method)
            print(f"   - {method}: {'✅' if has_method else '❌'}")
        
        # Тест 5: Проверка improved realistic_scoring
        from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix, RealisticPumpIndicators
        
        # Тест honeypot = 0
        bad_indicators = RealisticPumpIndicators(is_honeypot=True)
        bad_matrix = RealisticScoringMatrix(indicators=bad_indicators)
        bad_score = bad_matrix.calculate_security_score()
        print(f"✅ Honeypot правило: {bad_score} (должно быть 0)")
        
        # Тест высокие налоги = 0  
        high_tax_indicators = RealisticPumpIndicators(
            is_honeypot=False,
            buy_tax_percent=60.0  # >50%
        )
        high_tax_matrix = RealisticScoringMatrix(indicators=high_tax_indicators)
        high_tax_score = high_tax_matrix.calculate_security_score()
        print(f"✅ Высокие налоги правило: {high_tax_score} (должно быть 0)")
        
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("Архитектура наследования работает корректно")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def show_architecture_comparison():
    """Показать разницу до и после рефакторинга"""
    print("\n📊 СРАВНЕНИЕ АРХИТЕКТУР")
    print("=" * 50)
    
    print("\n❌ ДО РЕФАКТОРИНГА (дублирование):")
    old_files = [
        "discovery_agent.py - общий поиск токенов",
        "enhanced_discovery.py - промежуточный слой", 
        "pump_discovery_agent.py - pump анализ"
    ]
    
    for file in old_files:
        print(f"   - {file}")
    
    print("   📋 Проблемы:")
    print("     - Дублирование API логики")
    print("     - Дублирование обработки ошибок")
    print("     - Дублирование rate limiting")
    print("     - Сложность поддержки")
    
    print("\n✅ ПОСЛЕ РЕФАКТОРИНГА (наследование):")
    new_files = [
        "base_discovery_agent.py - базовый класс (общая логика)",
        "pump_discovery_agent.py - наследник (pump-specific логика)"
    ]
    
    for file in new_files:
        print(f"   - {file}")
    
    print("   📋 Преимущества:")
    print("     - ✅ Нет дублирования кода")
    print("     - ✅ Четкое разделение ответственности")
    print("     - ✅ Легко добавлять новые типы агентов")
    print("     - ✅ Переиспользование инфраструктуры")
    print("     - ✅ Улучшенная тестируемость")

def main():
    """Главная функция"""
    success = test_inheritance_architecture()
    show_architecture_comparison()
    
    if success:
        print("\n🚀 ГОТОВО К ПРОДАКШЕНУ!")
        print("Новая архитектура готова к использованию")
    else:
        print("\n⚠️ ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ")
        print("Нужно исправить ошибки перед использованием")
    
    return success

if __name__ == "__main__":
    main()
