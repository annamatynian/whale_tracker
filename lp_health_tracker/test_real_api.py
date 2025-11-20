#!/usr/bin/env python3
"""
LIVE API TEST для Price Strategy Manager
=======================================

🚨 ВНИМАНИЕ: Этот тест делает РЕАЛЬНЫЕ API вызовы!
- Тестирует CoinGecko API
- Проверяет fallback механизм
- Валидирует Pydantic модели с реальными данными

"""

import asyncio
import sys
import pytest
import time
from pathlib import Path
from typing import Dict, Any

# Добавить src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.price_strategy_manager import get_price_manager


@pytest.mark.asyncio
async def test_single_token_price():
    """Тест получения цены одного токена через реальный API."""
    print("🔍 Тестирование получения цены одного токена...")
    
    try:
        # Get price manager instance
        price_manager = get_price_manager()
        
        # Тестируем популярные токены
        test_tokens = ['ETH', 'BTC', 'USDC']
        
        for token in test_tokens:
            print(f"\n📡 Запрашиваем цену {token}...")
            start_time = time.time()
            
            price = await price_manager.get_token_price(token)
            
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # в миллисекундах
            
            if price is not None:
                print(f"✅ {token}: ${price:,.2f} (latency: {latency:.0f}ms)")
            else:
                print(f"❌ {token}: не удалось получить цену")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка получения цены: {e}")
        return False


@pytest.mark.asyncio
async def test_parallel_price_fetching():
    """Тест параллельного получения цен нескольких токенов."""
    print("\n🔍 Тестирование параллельного получения цен...")
    
    try:
        # Get price manager instance
        price_manager = get_price_manager()
        
        # Список токенов для тестирования (как в реальном LP проекте)
        tokens_to_test = [
            ('ETH', None),
            ('USDC', None), 
            ('BTC', None),
            ('UNI', None),
            ('AAVE', None)
        ]
        
        print(f"📡 Запрашиваем {len(tokens_to_test)} токенов параллельно...")
        start_time = time.time()
        
        # Используем метод как в main.py
        results = await price_manager.get_multiple_prices_parallel(tokens_to_test)
        
        end_time = time.time()
        total_latency = (end_time - start_time) * 1000
        
        print(f"\n📊 Результаты параллельных запросов (общее время: {total_latency:.0f}ms):")
        
        success_count = 0
        for symbol, address in tokens_to_test:
            price = results.get(symbol)
            if price is not None:
                print(f"✅ {symbol}: ${price:,.2f}")
                success_count += 1
            else:
                print(f"❌ {symbol}: не получен")
        
        success_rate = success_count / len(tokens_to_test) * 100
        print(f"\n📈 Success rate: {success_rate:.1f}% ({success_count}/{len(tokens_to_test)})")
        
        # Считаем тест успешным если получили хотя бы 60% цен
        return success_rate >= 60.0
        
    except Exception as e:
        print(f"❌ Ошибка параллельного получения: {e}")
        return False


@pytest.mark.asyncio
async def test_cache_performance():
    """Тест производительности кеширования."""
    print("\n🔍 Тестирование производительности кеша...")
    
    try:
        # Get price manager instance
        price_manager = get_price_manager()
        
        token = 'ETH'
        
        # Первый запрос (должен идти к API)
        print("📡 Первый запрос (к API)...")
        start_time = time.time()
        price1 = await price_manager.get_token_price(token)
        api_latency = (time.time() - start_time) * 1000
        
        # Второй запрос (должен идти из кеша)
        print("⚡ Второй запрос (из кеша)...")
        start_time = time.time()
        price2 = await price_manager.get_token_price(token)
        cache_latency = (time.time() - start_time) * 1000
        
        if price1 is not None and price2 is not None:
            print(f"✅ API latency: {api_latency:.0f}ms")
            print(f"✅ Cache latency: {cache_latency:.0f}ms")
            print(f"🚀 Cache speedup: {api_latency/cache_latency:.1f}x")
            
            # Цены должны быть одинаковые (из кеша)
            if abs(price1 - price2) < 0.01:
                print("✅ Кеш возвращает ту же цену")
                return True
            else:
                print(f"❌ Разные цены: {price1} vs {price2}")
                return False
        else:
            print("❌ Не удалось получить цены для теста кеша")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка теста кеша: {e}")
        return False


@pytest.mark.asyncio
async def test_error_handling():
    """Тест обработки ошибок и fallback механизма."""
    print("\n🔍 Тестирование обработки ошибок...")
    
    try:
        # Get price manager instance
        price_manager = get_price_manager()
        
        # Тест с несуществующим токеном
        print("🔍 Тестируем несуществующий токен...")
        price = await price_manager.get_token_price("NONEXISTENT_TOKEN_XYZ")
        
        if price is None:
            print("✅ Несуществующий токен корректно возвращает None")
        else:
            print(f"❌ Несуществующий токен вернул цену: {price}")
            return False
        
        # Тест с пустой строкой
        print("🔍 Тестируем пустой символ...")
        try:
            price = await price_manager.get_token_price("")
            if price is None:
                print("✅ Пустой символ корректно обработан")
            else:
                print(f"❌ Пустой символ вернул цену: {price}")
                return False
        except Exception:
            print("✅ Пустой символ вызвал ожидаемую ошибку")
        
        return True
        
    except Exception as e:
        print(f"❌ Неожиданная ошибка в тесте ошибок: {e}")
        return False


@pytest.mark.asyncio
async def test_reliability_tracking():
    """Тест отслеживания надежности источников."""
    print("\n🔍 Тестирование отслеживания надежности...")
    
    try:
        # Get price manager instance
        price_manager = get_price_manager()
        
        # Сделаем несколько запросов чтобы набрать статистику
        test_tokens = ['ETH', 'BTC', 'USDC']
        
        for token in test_tokens:
            await price_manager.get_token_price(token)
        
        # Получим отчет о надежности
        reliability_reports = price_manager.get_source_reliability_report()
        
        print("📊 Отчет о надежности источников:")
        for report in reliability_reports:
            print(f"  {report.source_name}: {report.success_rate:.1%} ({report.total_calls - report.failures}/{report.total_calls})")
        
        # Проверим что хотя бы один источник работает
        if any(report.total_calls > 0 for report in reliability_reports):
            print("✅ Источники показывают активность")
            return True
        else:
            print("❌ Ни один источник не показывает активности")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка теста надежности: {e}")
        return False


@pytest.mark.asyncio
async def simulate_real_lp_scenario():
    """Симуляция реального сценария из LP Health Tracker."""
    print("\n🎯 СИМУЛЯЦИЯ РЕАЛЬНОГО LP СЦЕНАРИЯ...")
    
    try:
        # Get price manager instance
        price_manager = get_price_manager()
        
        # Имитируем данные позиции как в main.py
        mock_position = {
            'name': 'ETH-USDC Test Position',
            'token_a_symbol': 'ETH',
            'token_b_symbol': 'USDC',
            'token_a_address': None,  # Для тестов пока без адреса
            'token_b_address': None
        }
        
        print(f"🏊‍♂️ Обрабатываем позицию: {mock_position['name']}")
        
        # Точно так же как в _process_position()
        tokens_to_fetch = [
            (mock_position['token_a_symbol'], mock_position.get('token_a_address')),
            (mock_position['token_b_symbol'], mock_position.get('token_b_address'))
        ]
        
        print("📡 Получаем цены в параллельном режиме...")
        current_prices = await price_manager.get_multiple_prices_parallel(tokens_to_fetch)
        
        token_a_price = current_prices.get(mock_position['token_a_symbol'])
        token_b_price = current_prices.get(mock_position['token_b_symbol'])
        
        if token_a_price is not None and token_b_price is not None:
            price_ratio = token_a_price / token_b_price
            
            print(f"✅ {mock_position['token_a_symbol']}: ${token_a_price:,.2f}")
            print(f"✅ {mock_position['token_b_symbol']}: ${token_b_price:,.2f}")
            print(f"📊 Price Ratio: {price_ratio:,.2f}")
            
            # Создаем market_data как в main.py
            market_data = {
                'token_a_price': token_a_price,
                'token_b_price': token_b_price, 
                'price_ratio': price_ratio,
                'source': 'price_strategy_manager'
            }
            
            print("✅ Market data создан для IL расчетов:")
            for key, value in market_data.items():
                print(f"  {key}: {value}")
            
            return True
        else:
            print("❌ Не удалось получить цены для LP позиции")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка симуляции LP сценария: {e}")
        return False


async def main():
    """Главная функция LIVE API тестирования."""
    print("🚀 LIVE API ТЕСТ Price Strategy Manager")
    print("=" * 50)
    print("⚠️  ВНИМАНИЕ: Делаем реальные API запросы!")
    print("💡 Убедитесь что у вас есть интернет\n")
    
    # Список всех тестов
    tests = [
        ("Одиночный токен", test_single_token_price),
        ("Параллельные запросы", test_parallel_price_fetching), 
        ("Производительность кеша", test_cache_performance),
        ("Обработка ошибок", test_error_handling),
        ("Отслеживание надежности", test_reliability_tracking),
        ("LP симуляция", simulate_real_lp_scenario)
    ]
    
    passed = 0
    total = len(tests)
    
    async with price_manager:  # Используем context manager
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"🧪 ТЕСТ: {test_name}")
            print('='*60)
            
            try:
                if await test_func():
                    print(f"✅ {test_name}: ПРОЙДЕН")
                    passed += 1
                else:
                    print(f"❌ {test_name}: ПРОВАЛЕН")
            except Exception as e:
                print(f"💥 {test_name}: КРИТИЧЕСКАЯ ОШИБКА - {e}")
    
    # Итоги
    print(f"\n{'='*60}")
    print(f"📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
    print('='*60)
    print(f"Пройдено тестов: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ! API полностью работает!")
        print("🚀 Price Strategy Manager готов к production!")
    elif passed >= total * 0.8:  # 80%+
        print("🟡 Большинство тестов прошли. Система работоспособна.")
        print("⚠️  Рекомендуется исследовать failed тесты.")
    else:
        print("🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ С API!")
        print("🔧 Требуется диагностика перед использованием.")
    
    return passed >= total * 0.8  # Считаем успехом если 80%+ тестов прошли


if __name__ == "__main__":
    print("🎯 Запускается LIVE API тест...")
    print("⏳ Это может занять 30-60 секунд...\n")
    
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 API тест завершен успешно!")
        sys.exit(0)
    else:
        print("\n🚨 API тест выявил проблемы!")
        sys.exit(1)
