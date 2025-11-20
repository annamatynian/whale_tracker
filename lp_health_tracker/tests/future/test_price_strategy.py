#!/usr/bin/env python3
"""
Тестирование активированных xfail тестов
======================================

Запускаем только наши 3 активированных теста:
1. test_price_fallback_strategy_creation
2. test_price_fallback_when_primary_fails  
3. test_price_caching_with_ttl
"""

import sys
import os
from pathlib import Path

# Настройка путей
project_dir = Path(__file__).parent
src_dir = project_dir / "src"
sys.path.insert(0, str(src_dir))

def test_price_fallback_strategy_creation():
    """Test creating price strategy with multiple fallback sources."""
    print("🧪 Тест 1: test_price_fallback_strategy_creation")
    
    try:
        from price_strategy_manager import PriceStrategyManager
        
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
        
        print("   ✅ Все проверки прошли")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_price_fallback_when_primary_fails():
    """Test automatic fallback when primary source fails."""
    print("🧪 Тест 2: test_price_fallback_when_primary_fails")
    
    try:
        from price_strategy_manager import PriceStrategyManager
        
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
        
        print("   ✅ Все проверки прошли")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_price_caching_with_ttl():
    """Test price caching with time-to-live (60 seconds)."""
    print("🧪 Тест 3: test_price_caching_with_ttl")
    
    try:
        from price_strategy_manager import PriceStrategyManager
        
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
        
        print("   ✅ Все проверки прошли")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Запуск всех активированных тестов."""
    
    print("🚀 ЗАПУСК АКТИВИРОВАННЫХ XFAIL ТЕСТОВ")
    print("=" * 60)
    print("📋 Тестируем 3 активированных теста PriceStrategyManager")
    print()
    
    tests = [
        test_price_fallback_strategy_creation,
        test_price_fallback_when_primary_fails,
        test_price_caching_with_ttl
    ]
    
    results = []
    for i, test_func in enumerate(tests, 1):
        success = test_func()
        results.append(success)
        print()
    
    # Подведение итогов
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 ВСЕ АКТИВИРОВАННЫЕ ТЕСТЫ ПРОШЛИ!")
        print("✨ Трансформация xfail → обычные тесты УСПЕШНА!")
        print()
        print("🎯 Что это означает:")
        print("   • PriceStrategyManager реализован корректно")
        print("   • Fallback механизм работает")  
        print("   • Кеширование функционирует")
        print("   • Статистика источников ведется")
        print()
        print("🚀 Готовы к следующему этапу:")
        print("   • Реализовать HistoricalDataManager")
        print("   • Активировать следующие xfail тесты")
        print("   • Добавить async версии методов")
        
        return True
    else:
        print("🚨 НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        print("🔧 Требуется доработка кода перед продолжением")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
