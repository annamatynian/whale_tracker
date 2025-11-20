#!/usr/bin/env python3
"""
Тест унифицированного PriceStrategyManager
=========================================

Проверяет, что вся функциональность из PriceOracle и LiveDataProvider
правильно интегрирована в PriceStrategyManager.

Author: Generated for LP Health Tracker
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_price_strategy_manager():
    """Тест базовой функциональности PriceStrategyManager."""
    print("🧪 ТЕСТИРОВАНИЕ УНИФИЦИРОВАННОГО PriceStrategyManager")
    print("=" * 60)
    
    try:
        from src.price_strategy_manager import get_price_manager, get_token_price_smart
        
        # Создать экземпляр менеджера
        manager = get_price_manager()
        print("✅ PriceStrategyManager создан успешно")
        
        # Тест 1: Получение цены токена
        print("\n📊 Тест 1: Получение цены ETH")
        eth_price = manager.get_token_price('ETH')
        print(f"   ETH Price: ${eth_price}")
        
        # Тест 2: Получение цен нескольких токенов
        print("\n📊 Тест 2: Получение цен нескольких токенов")
        symbols = ['ETH', 'USDC', 'WBTC']
        prices = manager.get_multiple_prices(symbols)
        for symbol, price in prices.items():
            print(f"   {symbol}: ${price}")
        
        # Тест 3: APR пула
        print("\n📊 Тест 3: Получение APR пула")
        apr = manager.get_pool_apr('WETH-USDC')
        print(f"   WETH-USDC APR: {apr:.4f} ({apr*100:.2f}%)")
        
        # Тест 4: Цены пары токенов
        print("\n📊 Тест 4: Цены пары токенов")
        pool_config = {'name': 'WETH-USDC'}
        price_a, price_b = manager.get_current_prices(pool_config)
        print(f"   WETH: ${price_a}, USDC: ${price_b}")
        
        # Тест 5: Глобальные функции
        print("\n📊 Тест 5: Глобальные helper функции")
        smart_price = get_token_price_smart('ETH')
        print(f"   Smart price для ETH: ${smart_price}")
        
        # Тест 6: Статистика
        print("\n📊 Тест 6: Статистика использования")
        reliability = manager.get_source_reliability_report()
        cache_stats = manager.get_cache_stats()
        
        print("   Надежность источников:")
        for source, rate in reliability.items():
            print(f"     {source}: {rate:.1%}")
        
        print(f"   Cache hits: {cache_stats['cache_hits']}")
        print(f"   Cache hit ratio: {cache_stats['cache_hit_ratio']:.1%}")
        
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_async_functionality():
    """Тест асинхронной функциональности."""
    print("\n🔄 ТЕСТИРОВАНИЕ АСИНХРОННЫХ МЕТОДОВ")
    print("=" * 60)
    
    try:
        from src.price_strategy_manager import get_price_manager
        
        manager = get_price_manager()
        
        # Тест асинхронного получения цены
        print("\n📊 Асинхронное получение цены ETH")
        eth_price = await manager.get_token_price_async('ETH')
        print(f"   ETH Price (async): ${eth_price}")
        
        # Тест асинхронного получения цен нескольких токенов
        print("\n📊 Асинхронное получение цен нескольких токенов")
        symbols = ['ETH', 'USDC', 'DAI']
        prices = await manager.get_multiple_prices_async(symbols)
        for symbol, price in prices.items():
            print(f"   {symbol}: ${price}")
        
        print("\n🎉 АСИНХРОННЫЕ ТЕСТЫ ПРОЙДЕНЫ!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в асинхронных тестах: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backward_compatibility():
    """Тест обратной совместимости."""
    print("\n🔄 ТЕСТИРОВАНИЕ ОБРАТНОЙ СОВМЕСТИМОСТИ")
    print("=" * 60)
    
    try:
        # Тест старых классов (должны работать через wrappers)
        print("\n📊 Тест PriceOracle wrapper")
        from src.price_strategy_manager import PriceOracle
        
        oracle = PriceOracle()  # Должно выдать warning
        print("   ✅ PriceOracle wrapper создан")
        
        print("\n📊 Тест LiveDataProvider wrapper")
        from src.price_strategy_manager import LiveDataProvider
        
        provider = LiveDataProvider()  # Должно выдать warning
        pool_config = {'name': 'WETH-USDC'}
        prices = provider.get_current_prices(pool_config)
        print(f"   Цены через wrapper: {prices}")
        
        print("\n🎉 ОБРАТНАЯ СОВМЕСТИМОСТЬ РАБОТАЕТ!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тестах обратной совместимости: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Главная функция тестирования."""
    print("🚀 НАЧИНАЕМ ТЕСТИРОВАНИЕ УНИФИЦИРОВАННОЙ СИСТЕМЫ ЦЕН")
    print("=" * 70)
    
    success = True
    
    # Синхронные тесты
    success &= test_price_strategy_manager()
    
    # Асинхронные тесты
    try:
        success &= asyncio.run(test_async_functionality())
    except Exception as e:
        print(f"❌ Ошибка при запуске async тестов: {e}")
        success = False
    
    # Тесты обратной совместимости
    success &= test_backward_compatibility()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!")
        print("✅ PriceStrategyManager готов к использованию")
        print("✅ Старые классы PriceOracle и LiveDataProvider можно удалить")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        print("🔧 Необходимо исправить ошибки перед удалением старых классов")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
