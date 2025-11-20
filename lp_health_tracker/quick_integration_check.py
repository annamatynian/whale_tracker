#!/usr/bin/env python3
"""
🚀 БЫСТРАЯ ПРОВЕРКА ИНТЕГРАЦИИ
=============================

Простой скрипт для проверки, что PriceStrategyManager
успешно интегрирован во все компоненты проекта.

Запуск: python quick_integration_check.py
"""

import sys
import os
from pathlib import Path

# Добавляем src в Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def check_integration():
    """Быстрая проверка интеграции."""
    print("🚀 БЫСТРАЯ ПРОВЕРКА ИНТЕГРАЦИИ PriceStrategyManager")
    print("=" * 60)
    
    checks_passed = 0
    total_checks = 6
    
    # Проверка 1: PriceStrategyManager доступен
    try:
        from src.price_strategy_manager import get_price_manager, PriceStrategyManager
        manager = get_price_manager()
        print("✅ 1/6: PriceStrategyManager доступен и работает")
        checks_passed += 1
    except Exception as e:
        print(f"❌ 1/6: Ошибка PriceStrategyManager: {e}")
    
    # Проверка 2: LPHealthMonitor интегрирован
    try:
        from src.lp_monitor_agent import LPHealthMonitor
        monitor = LPHealthMonitor()
        if hasattr(monitor, 'price_manager') and not hasattr(monitor, 'price_oracle'):
            print("✅ 2/6: LPHealthMonitor успешно интегрирован")
            checks_passed += 1
        else:
            print("❌ 2/6: LPHealthMonitor интеграция неполная")
    except Exception as e:
        print(f"❌ 2/6: Ошибка LPHealthMonitor: {e}")
    
    # Проверка 3: SimpleMultiPoolManager интегрирован
    try:
        from src.simple_multi_pool import SimpleMultiPoolManager
        pool_manager = SimpleMultiPoolManager()
        if hasattr(pool_manager, 'price_manager'):
            print("✅ 3/6: SimpleMultiPoolManager успешно интегрирован")
            checks_passed += 1
        else:
            print("❌ 3/6: SimpleMultiPoolManager интеграция неполная")
    except Exception as e:
        print(f"❌ 3/6: Ошибка SimpleMultiPoolManager: {e}")
    
    # Проверка 4: Старые классы удалены
    try:
        from src.defi_utils import PriceOracle
        print("❌ 4/6: PriceOracle все еще в defi_utils!")
    except ImportError:
        print("✅ 4/6: PriceOracle успешно удален из defi_utils")
        checks_passed += 1
    except Exception as e:
        print(f"❌ 4/6: Ошибка проверки defi_utils: {e}")
    
    # Проверка 5: LiveDataProvider удален
    try:
        from src.data_providers import LiveDataProvider
        print("❌ 5/6: LiveDataProvider все еще в data_providers!")
    except ImportError:
        print("✅ 5/6: LiveDataProvider успешно удален из data_providers")
        checks_passed += 1
    except Exception as e:
        print(f"❌ 5/6: Ошибка проверки data_providers: {e}")
    
    # Проверка 6: Обратная совместимость
    try:
        from src.price_strategy_manager import PriceOracle, LiveDataProvider
        oracle = PriceOracle()
        provider = LiveDataProvider()
        print("✅ 6/6: Wrapper классы для обратной совместимости работают")
        checks_passed += 1
    except Exception as e:
        print(f"❌ 6/6: Ошибка обратной совместимости: {e}")
    
    # Итоговый результат
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТ: {checks_passed}/{total_checks} проверок пройдено")
    
    if checks_passed == total_checks:
        print("🎉 ИНТЕГРАЦИЯ УСПЕШНА!")
        print("✅ Все компоненты обновлены")
        print("✅ PriceStrategyManager полностью интегрирован")
        print("✅ Система готова к работе")
        return True
    elif checks_passed >= total_checks - 1:
        print("⚠️ ПОЧТИ ГОТОВО!")
        print("🔧 Осталось исправить 1 проблему")
        return False
    else:
        print("❌ ТРЕБУЕТСЯ ДОРАБОТКА")
        print("🔧 Обнаружены критические проблемы")
        return False

if __name__ == "__main__":
    success = check_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("🎯 ИНТЕГРАЦИЯ ЗАВЕРШЕНА! МОЖНО РАБОТАТЬ! 🚀")
    else:
        print("🔧 НЕОБХОДИМЫ ДОПОЛНИТЕЛЬНЫЕ ИСПРАВЛЕНИЯ")
    print("=" * 60)
    
    # Дополнительные инструкции
    if success:
        print("\n📋 СЛЕДУЮЩИЕ ШАГИ:")
        print("   1. Запустите полные тесты: python test_integration_complete.py")
        print("   2. Проверьте работу в production: python main.py")
        print("   3. Обновите документацию проекта")
    else:
        print("\n🔧 НУЖНО ИСПРАВИТЬ:")
        print("   1. Запустите: python test_integration_complete.py")
        print("   2. Исправьте найденные проблемы")
        print("   3. Повторите проверку")
    
    sys.exit(0 if success else 1)
