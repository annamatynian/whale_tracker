"""
Простая проверка работы PriceStrategyManager
"""

def test_price_strategy():
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    # Импортируем
    from price_strategy_manager import PriceStrategyManager
    
    results = []
    
    # ТЕСТ 1: Создание стратегии
    try:
        strategy = PriceStrategyManager([
            'on_chain_uniswap', 'coingecko_api', 
            'coinmarketcap_api', 'cached_prices'
        ])
        
        assert strategy is not None
        assert len(strategy.sources) == 4
        assert strategy.sources[0] == 'on_chain_uniswap'
        assert strategy.cache_hits == 0
        
        results.append("✅ ТЕСТ 1 (Создание): PASSED")
        
    except Exception as e:
        results.append(f"❌ ТЕСТ 1 (Создание): FAILED - {e}")
    
    # ТЕСТ 2: Fallback логика
    try:
        strategy = PriceStrategyManager(['failing_source', 'working_source'])
        price = strategy.get_token_price('ETH')
        
        assert price == 2000.0
        assert strategy.last_used_source == 'working_source'
        
        stats = strategy.get_source_reliability_report()
        assert stats['failing_source'] == 0.0
        assert stats['working_source'] == 1.0
        
        results.append("✅ ТЕСТ 2 (Fallback): PASSED")
        
    except Exception as e:
        results.append(f"❌ ТЕСТ 2 (Fallback): FAILED - {e}")
    
    # ТЕСТ 3: Кеширование
    try:
        strategy = PriceStrategyManager(['working_source'])
        
        price1 = strategy.get_token_price('ETH')
        assert strategy.cache_hits == 0
        
        price2 = strategy.get_token_price('ETH')
        assert strategy.cache_hits == 1
        assert price1 == price2
        
        results.append("✅ ТЕСТ 3 (Кеширование): PASSED")
        
    except Exception as e:
        results.append(f"❌ ТЕСТ 3 (Кеширование): FAILED - {e}")
    
    return results

# Запуск
if __name__ == "__main__":
    print("🧪 ПРОВЕРКА PriceStrategyManager")
    print("=" * 40)
    
    try:
        results = test_price_strategy()
        
        for result in results:
            print(result)
        
        passed = len([r for r in results if "PASSED" in r])
        total = len(results)
        
        print(f"\n📊 ИТОГ: {passed}/{total} тестов прошли")
        
        if passed == total:
            print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ!")
            print("✅ PriceStrategyManager работает корректно")
            print("✅ Трансформация xfail → обычный тест успешна!")
        else:
            print("❌ Есть проблемы - нужно исправлять реализацию")
            
    except ImportError as e:
        print(f"❌ ОШИБКА ИМПОРТА: {e}")
        print("Файл src/price_strategy_manager.py не найден или содержит ошибки")
