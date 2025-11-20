#!/usr/bin/env python3
"""
Простая проверка унифицированной системы ценообразования
========================================================

Проверяет, что PriceStrategyManager работает корректно после
удаления старых классов PriceOracle и LiveDataProvider.
"""

import sys
import os
from pathlib import Path

# Добавляем src в Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_imports():
    """Тест импорта основных компонентов."""
    print("🧪 ТЕСТ ИМПОРТА КОМПОНЕНТОВ")
    print("-" * 40)
    
    try:
        # Проверяем импорт PriceStrategyManager
        from price_strategy_manager import PriceStrategyManager, get_price_manager
        print("✅ PriceStrategyManager импортирован успешно")
        
        # Проверяем, что старых классов больше нет
        try:
            from defi_utils import PriceOracle
            print("❌ PriceOracle все еще существует в defi_utils")
            return False
        except ImportError:
            print("✅ PriceOracle успешно удален из defi_utils")
        
        try:
            from data_providers import LiveDataProvider
            print("❌ LiveDataProvider все еще существует в data_providers")  
            return False
        except ImportError:
            print("✅ LiveDataProvider успешно удален из data_providers")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_price_manager_creation():
    """Тест создания экземпляра PriceStrategyManager."""
    print("\n🧪 ТЕСТ СОЗДАНИЯ PriceStrategyManager")
    print("-" * 40)
    
    try:
        from price_strategy_manager import get_price_manager
        
        # Создаем менеджер
        manager = get_price_manager()
        print("✅ PriceStrategyManager создан успешно")
        
        # Проверяем базовые атрибуты
        if hasattr(manager, 'get_token_price'):
            print("✅ Метод get_token_price доступен")
        else:
            print("❌ Метод get_token_price не найден")
            return False
            
        if hasattr(manager, 'get_pool_apr'):
            print("✅ Метод get_pool_apr доступен")
        else:
            print("❌ Метод get_pool_apr не найден")  
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания менеджера: {e}")
        return False

def test_basic_functionality():
    """Тест базовой функциональности."""
    print("\n🧪 ТЕСТ БАЗОВОЙ ФУНКЦИОНАЛЬНОСТИ")
    print("-" * 40)
    
    try:
        from price_strategy_manager import get_price_manager
        
        manager = get_price_manager()
        
        # Тест получения цены токена (мок режим)
        print("Тестируем получение цены ETH...")
        eth_price = manager.get_token_price('ETH')
        print(f"✅ ETH цена: ${eth_price}")
        
        # Тест получения APR
        print("Тестируем получение APR...")
        apr = manager.get_pool_apr('WETH-USDC')
        print(f"✅ WETH-USDC APR: {apr:.4f} ({apr*100:.2f}%)")
        
        # Тест цен пары
        print("Тестируем получение цен пары...")
        pool_config = {'name': 'WETH-USDC'}
        price_a, price_b = manager.get_current_prices(pool_config)
        print(f"✅ Цены пары: WETH=${price_a}, USDC=${price_b}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка функциональности: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_yaml_config():
    """Тест YAML конфигурации."""
    print("\n🧪 ТЕСТ YAML КОНФИГУРАЦИИ")
    print("-" * 40)
    
    try:
        import yaml
        
        # Проверяем базовую конфигурацию
        config_path = project_root / "config" / "base.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            print("✅ base.yaml прочитан успешно")
            
            # Проверяем ключевые секции
            if 'apis' in config:
                print("✅ Секция APIs найдена")
            if 'blockchain' in config:
                print("✅ Секция blockchain найдена")  
            if 'monitoring' in config:
                print("✅ Секция monitoring найдена")
                
            return True
        else:
            print("❌ config/base.yaml не найден")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка YAML: {e}")
        return False

def main():
    """Основная функция тестирования."""
    print("🚀 ПРОВЕРКА УНИФИЦИРОВАННОЙ СИСТЕМЫ ЦЕН")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_price_manager_creation,
        test_basic_functionality,
        test_yaml_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Тест {test.__name__} упал с ошибкой: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Унифицированная система готова к использованию")
        print("✅ Старые классы успешно удалены")
        print("✅ YAML конфигурации настроены")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        print("🔧 Необходимо исправить ошибки")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
