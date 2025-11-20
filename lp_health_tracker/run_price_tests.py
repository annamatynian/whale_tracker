#!/usr/bin/env python3
"""
Скрипт для запуска и проверки тестов PriceStrategyManager
"""

import sys
import os
import traceback

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_manual_tests():
    """Ручной запуск тестов без pytest для проверки."""
    
    print("🧪 ТЕСТИРОВАНИЕ PriceStrategyManager")
    print("=" * 50)
    
    try:
        # Импортируем нашу реализацию
        from price_strategy_manager import PriceStrategyManager
        
        print("✅ Импорт прошел успешно!")
        
        # ТЕСТ 1: test_price_fallback_strategy_creation
        print("\n1️⃣  ТЕСТ: test_price_fallback_strategy_creation")
        print("-" * 45)
        
        strategy = PriceStrategyManager([
            'on_chain_uniswap',  # Priority 1
            'coingecko_api',     # Priority 2  
            'coinmarketcap_api', # Priority 3
            'cached_prices'      # Priority 4
        ])
        
        # Базовые проверки (были в xfail тесте)
        assert strategy is not None
        assert len(strategy.sources) == 4
        
        # Дополнительные проверки (раз функция реализована)
        assert isinstance(strategy.sources, list)
        assert strategy.sources[0] == 'on_chain_uniswap'
        assert strategy.cache_hits == 0
        assert strategy.last_used_source is None
        assert hasattr(strategy, 'source_stats')
        
        print("✅ PASSED - Создание стратегии работает!")
        
        # ТЕСТ 2: test_price_fallback_when_primary_fails
        print("\n2️⃣  ТЕСТ: test_price_fallback_when_primary_fails")
        print("-" * 45)
        
        # Mock failing primary source and working secondary
        strategy = PriceStrategyManager(['failing_source', 'working_source'])
        
        # Should automatically fallback to working source
        price = strategy.get_token_price('ETH')
        assert price > 0
        assert price == 2000.0  # Наша тестовая цена
        assert strategy.last_used_source == 'working_source'
        
        # Проверяем статистику источников
        stats = strategy.get_source_reliability_report()
        assert stats['failing_source'] == 0.0  # 100% провалов
        assert stats['working_source'] == 1.0  # 100% успех
        
        print("✅ PASSED - Fallback механизм работает!")
        
        # ТЕСТ 3: test_price_caching_with_ttl
        print("\n3️⃣  ТЕСТ: test_price_caching_with_ttl")
        print("-" * 35)
        
        strategy = PriceStrategyManager(['working_source'])  # Используем рабочий источник
        
        # First call should fetch from source
        price1 = strategy.get_token_price('ETH')
        assert strategy.cache_hits == 0
        assert price1 == 2000.0  # Проверяем конкретную цену
        
        # Second call within TTL should use cache
        price2 = strategy.get_token_price('ETH')
        assert strategy.cache_hits == 1
        assert price1 == price2
        
        # Проверяем, что кеш работает правильно для разных токенов
        btc_price = strategy.get_token_price('BTC') 
        assert strategy.cache_hits == 1  # BTC не в кеше, cache_hits не увеличился
        
        print("✅ PASSED - Кеширование работает!")
        
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("=" * 50)
        print("📊 СТАТИСТИКА:")
        print("   ✅ 3/3 тестов прошли")
        print("   ✅ PriceStrategyManager полностью работает")
        print("   ✅ Трансформация xfail → обычный тест успешна!")
        
        return True
        
    except ImportError as e:
        print(f"❌ ОШИБКА ИМПОРТА: {e}")
        print("   Функция не найдена - нужно проверить пути!")
        return False
        
    except AssertionError as e:
        print(f"❌ ТЕСТ НЕ ПРОШЕЛ: {e}")
        print("   Реализация работает неправильно - нужно исправлять!")
        traceback.print_exc()
        return False
        
    except Exception as e:
        print(f"❌ НЕОЖИДАННАЯ ОШИБКА: {e}")
        traceback.print_exc()
        return False


def show_pytest_command():
    """Показать команду для запуска через pytest."""
    
    print("\n📋 КОМАНДЫ ДЛЯ PYTEST:")
    print("=" * 30)
    
    print("\n# Запустить все тесты PriceStrategyManager:")
    print("pytest tests/test_future_features.py::TestPriceStrategyManagerFuture -v")
    
    print("\n# Запустить один конкретный тест:")
    print("pytest tests/test_future_features.py::TestPriceStrategyManagerFuture::test_price_fallback_strategy_creation -v")
    
    print("\n# Запустить все тесты, включая xfail:")
    print("pytest tests/test_future_features.py -v")
    
    print("\n# Посмотреть статистику:")
    print("pytest tests/test_future_features.py --tb=short")


if __name__ == "__main__":
    success = run_manual_tests()
    
    if success:
        print("\n🎯 СЛЕДУЮЩИЙ ШАГ:")
        print("   Попробуйте запустить через pytest для официального подтверждения!")
        show_pytest_command()
    else:
        print("\n🔧 НУЖНО ИСПРАВИТЬ:")
        print("   1. Проверить код PriceStrategyManager")
        print("   2. Исправить ошибки") 
        print("   3. Запустить тесты снова")
