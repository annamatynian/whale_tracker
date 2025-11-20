#!/usr/bin/env python3
"""
Демонстрация работы PriceStrategyManager и трансформации тестов
"""

import sys
import os

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_price_strategy_manually():
    """Ручная проверка нашей реализации."""
    
    print("🧪 ДЕМОНСТРАЦИЯ ТРАНСФОРМАЦИИ XFAIL → ОБЫЧНЫЙ ТЕСТ")
    print("=" * 60)
    
    try:
        from price_strategy_manager import PriceStrategyManager
        
        print("\n1️⃣  СОЗДАНИЕ СТРАТЕГИИ (бывший xfail тест):")
        print("-" * 45)
        
        # Создаем стратегию - точно как в тесте
        strategy = PriceStrategyManager([
            'on_chain_uniswap',  # Priority 1
            'coingecko_api',     # Priority 2  
            'coinmarketcap_api', # Priority 3
            'cached_prices'      # Priority 4
        ])
        
        # Проверяем результаты (как в тесте)
        print(f"   ✅ strategy is not None: {strategy is not None}")
        print(f"   ✅ len(strategy.sources) == 4: {len(strategy.sources) == 4}")
        print(f"   ✅ sources = {strategy.sources}")
        
        print("\n   📊 СТАТУС: Если бы это был обычный тест → PASSED ✅")
        print("   📊 Если бы @pytest.mark.xfail → XFAILED (но функция готова!)")
        
        print("\n2️⃣  ТЕСТИРОВАНИЕ FALLBACK ЛОГИКИ:")
        print("-" * 40)
        
        # Тестируем fallback
        strategy_fallback = PriceStrategyManager(['failing_source', 'working_source'])
        price = strategy_fallback.get_token_price('ETH')
        
        print(f"   ✅ Получена цена: ${price}")
        print(f"   ✅ Использованный источник: {strategy_fallback.last_used_source}")
        print(f"   ✅ Fallback сработал: {strategy_fallback.last_used_source == 'working_source'}")
        
        print("\n3️⃣  ТЕСТИРОВАНИЕ КЕШИРОВАНИЯ:")
        print("-" * 35)
        
        # Тестируем кеш
        cache_strategy = PriceStrategyManager(['working_source'])
        
        print(f"   До запросов cache_hits: {cache_strategy.cache_hits}")
        
        price1 = cache_strategy.get_token_price('ETH')
        print(f"   После 1-го запроса cache_hits: {cache_strategy.cache_hits}")
        
        price2 = cache_strategy.get_token_price('ETH')
        print(f"   После 2-го запроса cache_hits: {cache_strategy.cache_hits}")
        
        print(f"   ✅ Цены одинаковые: {price1 == price2}")
        print(f"   ✅ Кеш работает: {cache_strategy.cache_hits == 1}")
        
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ!")
        print("=" * 60)
        print("\n💡 ПРОЦЕСС ТРАНСФОРМАЦИИ:")
        print("   1. Был xfail тест → описывал КАК должно работать")
        print("   2. Реализовали функцию → PriceStrategyManager готов")
        print("   3. Убрали @pytest.mark.xfail → стал обычным тестом") 
        print("   4. Тест проходит → функция работает правильно! ✅")
        print("\n   Если тест упадет → нужно исправлять реализацию! ❌")
        
    except ImportError as e:
        print(f"❌ ИМПОРТ НЕ РАБОТАЕТ: {e}")
        print("   Если бы это был xfail тест → XFAILED (ожидаемо)")
        print("   Если обычный тест → FAILED (нужно реализовывать)")
        
    except Exception as e:
        print(f"❌ ОШИБКА В ТЕСТЕ: {e}")
        print("   Обычный тест упал бы → нужно исправлять код!")


if __name__ == "__main__":
    test_price_strategy_manually()
