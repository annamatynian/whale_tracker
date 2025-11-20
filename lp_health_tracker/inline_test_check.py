#!/usr/bin/env python3
"""
Встроенная проверка PriceStrategyManager 
======================================

Прямая проверка без внешних вызовов.
"""

import sys
import os

# Настройка путей
project_dir = r"C:\Users\annam\Documents\DeFi-RAG-Project\lp_health_tracker"
src_dir = os.path.join(project_dir, "src")
sys.path.insert(0, src_dir)

print("🔍 ВСТРОЕННАЯ ПРОВЕРКА PRICESTRATEGYMANAGER")
print("=" * 55)

try:
    # Импортируем прямо здесь
    exec(open(os.path.join(src_dir, "price_strategy_manager.py")).read())
    print("✅ Файл price_strategy_manager.py успешно загружен")
    
    # Создаем менеджер
    manager = PriceStrategyManager(['working_source'])
    print("✅ PriceStrategyManager создан")
    
    # Проверяем атрибуты
    print(f"   📊 Источников: {len(manager.sources)}")
    print(f"   📊 Cache hits: {manager.cache_hits}")
    print(f"   📊 Last used source: {manager.last_used_source}")
    
    # Тестируем получение цены
    price = manager.get_token_price('ETH')
    print(f"✅ Получена цена ETH: {price}")
    
    if price == 2000.0:
        print("✅ Цена соответствует ожидаемой")
        
        # Проверяем кеш
        price2 = manager.get_token_price('ETH')
        if manager.cache_hits == 1:
            print("✅ Кеширование работает")
            
            # Проверяем fallback
            fallback_manager = PriceStrategyManager(['failing_source', 'working_source'])
            fallback_price = fallback_manager.get_token_price('ETH')
            
            if fallback_price == 2000.0 and fallback_manager.last_used_source == 'working_source':
                print("✅ Fallback механизм работает")
                
                print("\n🎉 ВСЕ ОСНОВНЫЕ ПРОВЕРКИ ПРОШЛИ!")
                print("💫 PriceStrategyManager готов к работе!")
                
                # Записываем результат в файл
                with open(os.path.join(project_dir, "test_result_success.txt"), "w") as f:
                    f.write("SUCCESS: All tests passed!\n")
                    f.write(f"Price obtained: {price}\n")
                    f.write(f"Cache hits: {manager.cache_hits}\n")
                    f.write(f"Fallback works: {fallback_manager.last_used_source}\n")
                    
                print("\n📄 Результаты записаны в test_result_success.txt")
                
            else:
                print("❌ Fallback механизм не работает")
        else:
            print("❌ Кеширование не работает")
    else:
        print(f"❌ Неожиданная цена: {price}")
        
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    
    # Записываем ошибку в файл
    with open(os.path.join(project_dir, "test_result_error.txt"), "w") as f:
        f.write(f"ERROR: {e}\n")
        f.write("TRACEBACK:\n")
        traceback.print_exc(file=f)
    
    print("\n📄 Ошибка записана в test_result_error.txt")

print("\n" + "=" * 55)
print("🏁 ПРОВЕРКА ЗАВЕРШЕНА")
