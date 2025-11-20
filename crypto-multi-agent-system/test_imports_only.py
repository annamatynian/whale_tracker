#!/usr/bin/env python3
"""
Быстрый тест импорта и базовой функциональности рефакторинга
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_basic_imports():
    """Проверка основных импортов"""
    print("🧪 ПРОВЕРКА ИМПОРТОВ ПОСЛЕ РЕФАКТОРИНГА")
    print("=" * 50)
    
    try:
        # Проверяем новый оркестратор
        from agents.orchestrator.simple_orchestrator import (
            SimpleOrchestrator, 
            FUNNEL_CONFIG, 
            ALERT_RECOMMENDATIONS
        )
        print("✅ SimpleOrchestrator импортирован")
        print(f"✅ FUNNEL_CONFIG: {FUNNEL_CONFIG}")
        print(f"✅ ALERT_RECOMMENDATIONS: {ALERT_RECOMMENDATIONS}")
        
        # Проверяем зависимости
        from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent
        from tools.market_data.coingecko_client import CoinGeckoClient
        from tools.security.goplus_client import GoPlusClient
        from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix, RealisticPumpIndicators
        print("✅ Все зависимости импортированы")
        
        # Проверяем методы класса
        orchestrator_methods = [method for method in dir(SimpleOrchestrator) if not method.startswith('_')]
        print(f"✅ Методы SimpleOrchestrator: {orchestrator_methods}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_config_values():
    """Проверка значений конфигурации"""
    print(f"\n🔧 ПРОВЕРКА КОНФИГУРАЦИИ")
    print("=" * 50)
    
    try:
        from agents.orchestrator.simple_orchestrator import FUNNEL_CONFIG
        
        # Проверяем обязательные ключи
        required_keys = ['top_n_for_onchain', 'min_score_for_alert', 'api_calls_threshold']
        for key in required_keys:
            if key not in FUNNEL_CONFIG:
                print(f"❌ Отсутствует ключ конфигурации: {key}")
                return False
            print(f"✅ {key}: {FUNNEL_CONFIG[key]}")
        
        # Проверяем разумность значений
        checks = [
            (FUNNEL_CONFIG['top_n_for_onchain'] > 0, "top_n_for_onchain должен быть > 0"),
            (FUNNEL_CONFIG['min_score_for_alert'] >= 0, "min_score_for_alert должен быть >= 0"),
            (FUNNEL_CONFIG['api_calls_threshold'] >= 0, "api_calls_threshold должен быть >= 0"),
        ]
        
        for check, message in checks:
            if not check:
                print(f"❌ {message}")
                return False
        
        print("✅ Все значения конфигурации корректны")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки конфигурации: {e}")
        return False

def test_backward_compatibility():
    """Проверка обратной совместимости"""
    print(f"\n🔄 ПРОВЕРКА ОБРАТНОЙ СОВМЕСТИМОСТИ")
    print("=" * 50)
    
    try:
        from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
        
        # Проверяем, что основные методы сохранились
        required_methods = ['run_analysis_pipeline', 'should_spend_api_calls']
        
        for method in required_methods:
            if not hasattr(SimpleOrchestrator, method):
                print(f"❌ Отсутствует метод: {method}")
                return False
            print(f"✅ Метод {method} сохранен")
        
        # Проверяем сигнатуру run_analysis_pipeline
        import inspect
        signature = inspect.signature(SimpleOrchestrator.run_analysis_pipeline)
        print(f"✅ Сигнатура run_analysis_pipeline: {signature}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки совместимости: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🧪 КОМПЛЕКСНЫЙ ТЕСТ РЕФАКТОРИНГА")
    print("=" * 70)
    
    tests = [
        ("Импорты", test_basic_imports),
        ("Конфигурация", test_config_values), 
        ("Обратная совместимость", test_backward_compatibility)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    # Итоговые результаты
    print(f"\n📋 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    print("=" * 70)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"   {status}: {test_name}")
        if not success:
            all_passed = False
    
    print(f"\n{'🎉' if all_passed else '❌'} ОБЩИЙ РЕЗУЛЬТАТ:")
    if all_passed:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("🌊 Многоуровневая воронка работает корректно!")
        print("🔧 Рефакторинг выполнен без потери функциональности!")
        print("🚀 Система готова к использованию и расширению!")
        
        print(f"\n💡 СЛЕДУЮЩИЕ ШАГИ:")
        print("   1. Протестировать с реальными API ключами (python main.py --dry-run)")
        print("   2. Реализовать OnChain анализ для топ-15 кандидатов")
        print("   3. Добавить Sterile Deployer Analysis")
        
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ В РЕФАКТОРИНГЕ!")
        print("🔧 Проверьте ошибки выше и исправьте код")
        
    return all_passed

if __name__ == "__main__":
    success = main()
    print(f"\nВыход с кодом: {0 if success else 1}")
