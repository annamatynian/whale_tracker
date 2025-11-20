#!/usr/bin/env python3
"""
🎯 ФИНАЛЬНАЯ ПРОВЕРКА УНИФИЦИРОВАННОЙ СИСТЕМЫ ЦЕН
===============================================

Проверяет, что унификация завершена успешно:
✅ PriceStrategyManager работает
✅ Старые классы PriceOracle и LiveDataProvider удалены  
✅ YAML конфигурации настроены
✅ Обратная совместимость работает

Author: Generated for LP Health Tracker
"""

import sys
import os
from pathlib import Path

# Добавляем src в Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def banner(text):
    """Красивый баннер для вывода."""
    print("\n" + "="*60)
    print(f"🎯 {text}")
    print("="*60)

def success(text):
    """Вывод успеха."""
    print(f"✅ {text}")

def error(text):
    """Вывод ошибки."""
    print(f"❌ {text}")

def info(text):
    """Информационный вывод."""
    print(f"📋 {text}")

def test_old_classes_removed():
    """Проверка, что старые классы удалены."""
    banner("ПРОВЕРКА УДАЛЕНИЯ СТАРЫХ КЛАССОВ")
    
    passed = True
    
    # Проверяем defi_utils.py
    try:
        from defi_utils import PriceOracle
        error("PriceOracle все еще существует в defi_utils.py!")
        passed = False
    except ImportError:
        success("PriceOracle успешно удален из defi_utils.py")
    
    # Проверяем data_providers.py  
    try:
        from data_providers import LiveDataProvider
        error("LiveDataProvider все еще существует в data_providers.py!")
        passed = False
    except ImportError:
        success("LiveDataProvider успешно удален из data_providers.py")
    
    # Проверяем, что базовые классы остались
    try:
        from data_providers import DataProvider, MockDataProvider
        success("Базовые классы DataProvider и MockDataProvider сохранены")
    except ImportError as e:
        error(f"Базовые классы отсутствуют: {e}")
        passed = False
    
    return passed

def test_unified_system():
    """Проверка работы унифицированной системы."""
    banner("ПРОВЕРКА УНИФИЦИРОВАННОЙ СИСТЕМЫ")
    
    try:
        # Импорт основных компонентов
        from price_strategy_manager import (
            PriceStrategyManager, 
            get_price_manager,
            get_token_price_smart
        )
        success("Все компоненты PriceStrategyManager импортированы")
        
        # Создание менеджера
        manager = get_price_manager()
        success("PriceStrategyManager создан успешно")
        info(f"   Тип: {type(manager).__name__}")
        
        # Проверка методов
        methods = ['get_token_price', 'get_pool_apr', 'get_current_prices', 'get_multiple_prices']
        for method in methods:
            if hasattr(manager, method):
                success(f"Метод {method} доступен")
            else:
                error(f"Метод {method} отсутствует")
                return False
        
        # Тест базовой функциональности
        info("Тестирование базовой функциональности...")
        
        # Цена токена
        eth_price = manager.get_token_price('ETH')
        info(f"   ETH цена: ${eth_price}")
        
        # APR пула
        apr = manager.get_pool_apr('WETH-USDC') 
        info(f"   WETH-USDC APR: {apr:.4f} ({apr*100:.2f}%)")
        
        # Цены пары
        pool_config = {'name': 'WETH-USDC'}
        price_a, price_b = manager.get_current_prices(pool_config)
        info(f"   Цены пары: WETH=${price_a}, USDC=${price_b}")
        
        # Глобальная функция
        smart_price = get_token_price_smart('ETH')
        info(f"   Smart price: ${smart_price}")
        
        success("Все базовые функции работают!")
        return True
        
    except Exception as e:
        error(f"Ошибка в унифицированной системе: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backward_compatibility():
    """Тест обратной совместимости."""
    banner("ПРОВЕРКА ОБРАТНОЙ СОВМЕСТИМОСТИ")
    
    try:
        # Импорт wrapper классов
        from price_strategy_manager import PriceOracle, LiveDataProvider
        success("Wrapper классы PriceOracle и LiveDataProvider доступны")
        
        # Тест PriceOracle wrapper
        oracle = PriceOracle()
        success("PriceOracle wrapper создан")
        
        # Тест LiveDataProvider wrapper  
        provider = LiveDataProvider()
        pool_config = {'name': 'WETH-USDC'}
        prices = provider.get_current_prices(pool_config)
        success(f"LiveDataProvider wrapper работает: {prices}")
        
        success("Обратная совместимость обеспечена!")
        return True
        
    except Exception as e:
        error(f"Проблема с обратной совместимостью: {e}")
        return False

def test_yaml_config():
    """Проверка YAML конфигурации."""
    banner("ПРОВЕРКА YAML КОНФИГУРАЦИИ")
    
    try:
        import yaml
        
        config_file = project_root / "config" / "base.yaml"
        if not config_file.exists():
            error("config/base.yaml не найден")
            return False
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        success("base.yaml успешно прочитан")
        
        # Проверка ключевых секций
        required_sections = ['apis', 'blockchain', 'monitoring', 'notifications']
        for section in required_sections:
            if section in config:
                success(f"Секция '{section}' найдена")
            else:
                error(f"Секция '{section}' отсутствует")
                return False
        
        # Проверка API конфигурации
        if 'coingecko' in config.get('apis', {}):
            success("CoinGecko API настроен")
        else:
            error("CoinGecko API не настроен")
        
        success("YAML конфигурации корректны!")
        return True
        
    except Exception as e:
        error(f"Ошибка YAML конфигурации: {e}")
        return False

def main():
    """Главная функция финальной проверки."""
    banner("ФИНАЛЬНАЯ ПРОВЕРКА УНИФИЦИРОВАННОЙ СИСТЕМЫ")
    
    info("Проверяем завершение унификации системы управления ценами...")
    info("После удаления PriceOracle и LiveDataProvider")
    
    # Список тестов
    tests = [
        ("Удаление старых классов", test_old_classes_removed),
        ("Унифицированная система", test_unified_system), 
        ("Обратная совместимость", test_backward_compatibility),
        ("YAML конфигурации", test_yaml_config)
    ]
    
    passed = 0
    total = len(tests)
    
    # Запуск тестов
    for test_name, test_func in tests:
        info(f"\nЗапуск теста: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                error(f"Тест '{test_name}' не прошел")
        except Exception as e:
            error(f"Тест '{test_name}' упал с ошибкой: {e}")
    
    # Итоговый результат
    banner("ИТОГОВЫЙ РЕЗУЛЬТАТ")
    info(f"Пройдено тестов: {passed}/{total}")
    
    if passed == total:
        success("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        success("✅ Унификация завершена успешно")
        success("✅ PriceStrategyManager работает корректно")
        success("✅ Старые классы удалены без поломки системы")
        success("✅ YAML конфигурации настроены")
        success("✅ Обратная совместимость обеспечена")
        
        info("\n🚀 СИСТЕМА ГОТОВА К РАБОТЕ!")
        info("   Можно безопасно использовать новую унифицированную систему")
        info("   Старый код будет работать через wrapper'ы")
        
    else:
        error("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        error("🔧 Необходимо исправить обнаруженные проблемы")
        
        if passed >= total - 1:
            info("⚠️  Почти готово! Осталось исправить 1 проблему")
        elif passed >= total // 2:
            info("⚠️  Половина работы выполнена, продолжаем...")
        else:
            info("⚠️  Требуется серьезная доработка")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print("\n" + "="*60)
    if success:
        print("🎯 УНИФИКАЦИЯ СИСТЕМЫ ЦЕН ЗАВЕРШЕНА УСПЕШНО! 🎉")
    else:
        print("🔧 ТРЕБУЕТСЯ ДОРАБОТКА СИСТЕМЫ")
    print("="*60)
    
    sys.exit(0 if success else 1)
