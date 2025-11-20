#!/usr/bin/env python3
"""
🎯 ТЕСТ ПОЛНОЙ ИНТЕГРАЦИИ PriceStrategyManager
============================================

Проверяет, что PriceStrategyManager успешно интегрирован во все компоненты:
✅ lp_monitor_agent.py - замена PriceOracle
✅ simple_multi_pool.py - замена LiveDataProvider
✅ Все методы работают корректно
✅ Обратная совместимость сохранена

Author: Generated for LP Health Tracker Integration
"""

import sys
import os
import asyncio
from pathlib import Path

# Добавляем src в Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def banner(text):
    """Красивый баннер."""
    print(f"\n{'='*70}")
    print(f"🎯 {text}")
    print('='*70)

def success(text):
    """Вывод успеха."""
    print(f"✅ {text}")

def error(text):
    """Вывод ошибки."""
    print(f"❌ {text}")

def info(text):
    """Информационный вывод."""
    print(f"📋 {text}")

def test_price_manager_integration():
    """Тест базовой интеграции PriceStrategyManager."""
    banner("ТЕСТ БАЗОВОЙ ИНТЕГРАЦИИ PriceStrategyManager")
    
    try:
        from src.price_strategy_manager import get_price_manager
        
        manager = get_price_manager()
        success("PriceStrategyManager создан и доступен")
        
        # Тест базовых методов
        eth_price = manager.get_token_price('ETH')
        success(f"Получена цена ETH: ${eth_price}")
        
        prices = manager.get_multiple_prices(['ETH', 'USDC'])
        success(f"Получены множественные цены: {prices}")
        
        apr = manager.get_pool_apr('WETH-USDC')
        success(f"Получен APR пула: {apr:.4f}")
        
        return True
        
    except Exception as e:
        error(f"Ошибка в базовой интеграции: {e}")
        return False

def test_lp_monitor_integration():
    """Тест интеграции в LPHealthMonitor."""
    banner("ТЕСТ ИНТЕГРАЦИИ В LP MONITOR AGENT")
    
    try:
        # Импорт должен работать без ошибок
        from src.lp_monitor_agent import LPHealthMonitor
        success("LPHealthMonitor импортирован успешно")
        
        # Создание экземпляра
        monitor = LPHealthMonitor()
        success("LPHealthMonitor создан успешно")
        
        # Проверяем, что price_manager есть в атрибутах
        if hasattr(monitor, 'price_manager'):
            success("price_manager правильно инициализирован в monitor")
        else:
            error("price_manager отсутствует в monitor")
            return False
        
        # Проверяем, что старого price_oracle больше нет
        if hasattr(monitor, 'price_oracle'):
            error("Старый price_oracle все еще присутствует!")
            return False
        else:
            success("Старый price_oracle успешно удален")
        
        return True
        
    except ImportError as e:
        error(f"Ошибка импорта LPHealthMonitor: {e}")
        return False
    except Exception as e:
        error(f"Ошибка в интеграции LP Monitor: {e}")
        return False

def test_simple_multi_pool_integration():
    """Тест интеграции в SimpleMultiPoolManager."""
    banner("ТЕСТ ИНТЕГРАЦИИ В SIMPLE MULTI POOL MANAGER")
    
    try:
        # Импорт должен работать без ошибок
        from src.simple_multi_pool import SimpleMultiPoolManager
        success("SimpleMultiPoolManager импортирован успешно")
        
        # Создание экземпляра
        manager = SimpleMultiPoolManager()
        success("SimpleMultiPoolManager создан успешно")
        
        # Проверяем, что price_manager есть в атрибутах
        if hasattr(manager, 'price_manager'):
            success("price_manager правильно инициализирован в manager")
        else:
            error("price_manager отсутствует в manager")
            return False
        
        # Проверяем обратную совместимость
        if hasattr(manager, 'data_provider'):
            success("data_provider сохранен для обратной совместимости")
        else:
            error("data_provider отсутствует (нарушена обратная совместимость)")
            return False
        
        # Тест базовой функциональности
        test_pool = {
            'name': 'Test Integration Pool',
            'token_a_symbol': 'ETH',
            'token_b_symbol': 'USDC',
            'initial_price_a_usd': 3000.0,
            'initial_price_b_usd': 1.0,
            'initial_liquidity_a': 1.0,
            'initial_liquidity_b': 3000.0,
            'gas_costs_usd': 50.0,
            'days_held_mock': 30
        }
        
        manager.add_pool(test_pool)
        success("Тестовый пул добавлен успешно")
        
        # Тест расчета Net P&L с новым менеджером
        result = manager.calculate_net_pnl_with_fees(test_pool)
        if 'error' not in result:
            success("Net P&L расчет работает с новым price_manager")
            net_pnl = result.get('net_pnl', {}).get('net_pnl_usd', 0)
            info(f"   Рассчитанный Net P&L: ${net_pnl:.2f}")
        else:
            error(f"Ошибка в расчете Net P&L: {result['error']}")
            return False
        
        return True
        
    except ImportError as e:
        error(f"Ошибка импорта SimpleMultiPoolManager: {e}")
        return False
    except Exception as e:
        error(f"Ошибка в интеграции Simple Multi Pool: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_async_integration():
    """Тест асинхронной интеграции."""
    banner("ТЕСТ АСИНХРОННОЙ ИНТЕГРАЦИИ")
    
    try:
        from src.lp_monitor_agent import LPHealthMonitor
        
        monitor = LPHealthMonitor()
        success("LPHealthMonitor создан для async теста")
        
        # Создаем тестовую позицию
        test_position = {
            'name': 'Test Async Position',
            'token_a_symbol': 'ETH',
            'token_b_symbol': 'USDC',
            'initial_price_a_usd': 3000.0,
            'initial_price_b_usd': 1.0,
            'il_alert_threshold': 0.05
        }
        
        # Тест асинхронного получения цен через monitor
        prices = await monitor.price_manager.get_multiple_prices_async(['ETH', 'USDC'])
        success(f"Асинхронные цены получены: ETH=${prices.get('ETH', 0)}, USDC=${prices.get('USDC', 0)}")
        
        return True
        
    except Exception as e:
        error(f"Ошибка в async интеграции: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_cleanup():
    """Тест чистоты импортов."""
    banner("ТЕСТ ЧИСТОТЫ ИМПОРТОВ")
    
    try:
        # Проверяем, что старые классы больше не импортируются напрямую
        try:
            from src.defi_utils import PriceOracle
            error("PriceOracle все еще импортируется из defi_utils!")
            return False
        except ImportError:
            success("PriceOracle успешно удален из defi_utils")
        
        try:
            from src.data_providers import LiveDataProvider
            error("LiveDataProvider все еще импортируется из data_providers!")
            return False
        except ImportError:
            success("LiveDataProvider успешно удален из data_providers")
        
        # Проверяем, что wrapper классы доступны через price_strategy_manager
        try:
            from src.price_strategy_manager import PriceOracle, LiveDataProvider
            success("Wrapper классы доступны через price_strategy_manager (обратная совместимость)")
        except ImportError:
            error("Wrapper классы недоступны!")
            return False
        
        return True
        
    except Exception as e:
        error(f"Ошибка в проверке импортов: {e}")
        return False

async def main():
    """Основная функция тестирования интеграции."""
    banner("ПОЛНЫЙ ТЕСТ ИНТЕГРАЦИИ PriceStrategyManager")
    
    info("Проверяем, что унифицированная система полностью интегрирована...")
    
    # Список тестов
    sync_tests = [
        ("Базовая интеграция PriceStrategyManager", test_price_manager_integration),
        ("Интеграция в LP Monitor Agent", test_lp_monitor_integration),
        ("Интеграция в Simple Multi Pool Manager", test_simple_multi_pool_integration),
        ("Чистота импортов", test_import_cleanup)
    ]
    
    async_tests = [
        ("Асинхронная интеграция", test_async_integration)
    ]
    
    passed = 0
    total = len(sync_tests) + len(async_tests)
    
    # Запуск синхронных тестов
    for test_name, test_func in sync_tests:
        info(f"\nЗапуск теста: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                error(f"Тест '{test_name}' не прошел")
        except Exception as e:
            error(f"Тест '{test_name}' упал с ошибкой: {e}")
    
    # Запуск асинхронных тестов
    for test_name, test_func in async_tests:
        info(f"\nЗапуск async теста: {test_name}")
        try:
            if await test_func():
                passed += 1
            else:
                error(f"Async тест '{test_name}' не прошел")
        except Exception as e:
            error(f"Async тест '{test_name}' упал с ошибкой: {e}")
    
    # Итоговый результат
    banner("ИТОГОВЫЙ РЕЗУЛЬТАТ ИНТЕГРАЦИИ")
    info(f"Пройдено тестов: {passed}/{total}")
    
    if passed == total:
        success("🎉 ВСЯ ИНТЕГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        success("✅ PriceStrategyManager полностью интегрирован в проект")
        success("✅ Все компоненты обновлены")
        success("✅ Обратная совместимость сохранена")
        success("✅ Старые классы корректно удалены")
        
        info("\n🚀 СИСТЕМА ГОТОВА К РАБОТЕ!")
        info("   Все компоненты используют унифицированный PriceStrategyManager")
        info("   Старый код продолжит работать через wrapper'ы")
        info("   Цены и APR получаются из единого источника")
        
    else:
        error("❌ ИНТЕГРАЦИЯ НЕ ЗАВЕРШЕНА")
        error("🔧 Обнаружены проблемы, требующие исправления")
        
        if passed >= total - 1:
            info("⚠️  Почти готово! Осталось исправить 1 проблему")
        elif passed >= total // 2:
            info("⚠️  Половина интеграции выполнена")
        else:
            info("⚠️  Требуется значительная доработка")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    print("\n" + "="*70)
    if success:
        print("🎯 ИНТЕГРАЦИЯ PriceStrategyManager ЗАВЕРШЕНА! 🎉")
    else:
        print("🔧 ТРЕБУЕТСЯ ДОРАБОТКА ИНТЕГРАЦИИ")
    print("="*70)
    
    sys.exit(0 if success else 1)
