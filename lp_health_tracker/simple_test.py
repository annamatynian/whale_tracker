import sys
sys.path.insert(0, r'C:\Users\annam\Documents\DeFi-RAG-Project\lp_health_tracker\src')

try:
    from price_strategy_manager import PriceStrategyManager
    
    print("✅ Импорт успешен!")
    
    # Создаем стратегию
    strategy = PriceStrategyManager(['working_source'])
    print(f"✅ Объект создан: {type(strategy)}")
    
    # Тестируем получение цены
    price = strategy.get_token_price('ETH')
    print(f"✅ Получена цена: ${price}")
    
    # Тестируем кеш
    price2 = strategy.get_token_price('ETH')
    print(f"✅ Cache hits: {strategy.cache_hits}")
    
    print("🎉 БАЗОВАЯ ФУНКЦИОНАЛЬНОСТЬ РАБОТАЕТ!")
    
except Exception as e:
    print(f"❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
