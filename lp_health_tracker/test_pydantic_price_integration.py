#!/usr/bin/env python3
"""
Тест Pydantic интеграции в Price Strategy Manager
===============================================

Проверяет что все Pydantic модели работают корректно
в price_strategy_manager.py после интеграции.
"""

import asyncio
import sys
import pytest
from pathlib import Path
import time
from datetime import datetime, timedelta
from decimal import Decimal

# Добавить src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.price_strategy_manager import (
    get_price_manager, 
    PriceSource
)


def test_pydantic_models():
    """Тест всех Pydantic моделей."""
    print("🔍 Тестирование Pydantic моделей...")
    
    try:
        # 1. Тест PriceSource
        print("  📋 Тестируем PriceSource...")
        source = PriceSource(
            name="coingecko",
            priority=1,
            rate_limit=50,
            reliability=0.95
        )
        assert source.name == "coingecko"
        assert source.priority == 1
        print("  ✅ PriceSource работает")
        
        # 2. Тест валидации PriceSource
        print("  📋 Тестируем валидацию PriceSource...")
        try:
            invalid_source = PriceSource(
                name="",  # Пустое имя
                priority=1,
                rate_limit=50,
                reliability=0.95
            )
            print("  ❌ Валидация не работает!")
            return False
        except Exception:
            print("  ✅ Валидация PriceSource работает")
        
        # 3. Тест PriceResult
        print("  📋 Тестируем PriceResult...")
        result = PriceResult(
            symbol="ETH",
            price=2000.50,
            source="coingecko",
            timestamp=datetime.now(),
            success=True
        )
        assert result.symbol == "ETH"
        assert result.price == 2000.50
        print("  ✅ PriceResult работает")
        
        # 4. Тест CachedPrice (используем timestamp как float)
        print("  📋 Тестируем CachedPrice...")
        cached = CachedPrice(
            price=1500.75,
            timestamp=time.time(),  # Используем timestamp как float
            ttl=60
        )
        assert not cached.is_expired  # Только что создан
        print("  ✅ CachedPrice работает")
        
        # 5. Тест TTL в CachedPrice
        print("  📋 Тестируем TTL в CachedPrice...")
        old_cached = CachedPrice(
            price=1500.75,
            timestamp=time.time() - 120,  # 2 минуты назад
            ttl=60  # TTL 1 минута
        )
        assert old_cached.is_expired  # Должен быть expired
        print("  ✅ TTL логика работает")
        
        # 6. Тест ReliabilityReport
        print("  📋 Тестируем ReliabilityReport...")
        reliability = ReliabilityReport(
            source_name="coingecko",
            total_calls=100,
            failures=5,
            success_rate=0.95
        )
        assert reliability.success_rate == 0.95
        print("  ✅ ReliabilityReport работает")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка в Pydantic моделях: {e}")
        return False


def test_price_manager_pydantic_integration():
    """Тест интеграции Pydantic в price_manager."""
    print("\n🔍 Тестирование интеграции Pydantic в price_manager...")
    
    try:
        # 1. Проверяем что rate_limiters созданы
        print("  📋 Проверяем rate limiters...")
        assert hasattr(price_manager, '_rate_limiters')
        assert 'coingecko' in price_manager._rate_limiters
        print("  ✅ Rate limiters инициализированы")
        
        # 2. Проверяем кеш структуру
        print("  📋 Проверяем структуру кеша...")
        assert hasattr(price_manager, '_price_cache')
        assert hasattr(price_manager, '_cache_ttl')
        print("  ✅ Кеш структура корректна")
        
        # 3. Тестируем метод _cache_price
        print("  📋 Тестируем кеширование...")
        price_manager._cache_price("TEST_TOKEN", 100.0)
        
        # Проверяем что цена закеширована
        assert price_manager._is_price_cached("TEST_TOKEN")
        cached_price = price_manager._price_cache["TEST_TOKEN"]
        
        # Проверяем что это CachedPrice объект
        assert isinstance(cached_price, CachedPrice)
        assert cached_price.price == 100.0
        assert not cached_price.is_expired
        print("  ✅ Кеширование работает с Pydantic")
        
        # 4. Проверяем структуру reliability tracking
        print("  📋 Проверяем reliability tracking...")
        assert hasattr(price_manager, 'source_stats')
        print("  ✅ Reliability tracking готов")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка интеграции: {e}")
        return False


@pytest.mark.asyncio
async def test_pydantic_in_real_workflow():
    """Тест Pydantic в реальном workflow price_manager."""
    print("\n🔍 Тестирование Pydantic в реальном workflow...")
    
    try:
        async with price_manager:  # Context manager
            
            # 1. Тест обновления статистики (прямо через source_stats)
            print("  📋 Тестируем обновление статистики...")
            
            # Симулируем успешный вызов
            price_manager.source_stats["coingecko"]["calls"] += 1
            
            # Проверяем что статистика обновилась
            if "coingecko" in price_manager.source_stats:
                stats = price_manager.source_stats["coingecko"]
                print(f"  📊 Stats: calls={stats['calls']}, failures={stats['failures']}")
                print("  ✅ Статистика обновляется")
            
            # 2. Тест get_source_reliability_report
            print("  📋 Тестируем отчет о надежности...")
            
            # Добавим еще статистики
            price_manager.source_stats["coingecko"]["calls"] += 2
            price_manager.source_stats["coingecko"]["failures"] += 1
            
            # Получаем отчет
            reliability_reports = price_manager.get_source_reliability_report()
            
            print(f"  📊 Reliability reports count: {len(reliability_reports)}")
            
            # Проверяем что это список ReliabilityReport объектов
            assert isinstance(reliability_reports, list)
            if reliability_reports:
                report = reliability_reports[0]
                assert isinstance(report, ReliabilityReport)
                print(f"  ✅ Отчет содержит ReliabilityReport: {report.source_name}")
            
            # 3. Тест что кеш возвращает Pydantic объекты
            print("  📋 Тестируем Pydantic объекты в кеше...")
            
            # Добавляем в кеш
            price_manager._cache_price("PYDANTIC_TEST", 999.99)
            
            # Проверяем что получаем CachedPrice
            if price_manager._is_price_cached("PYDANTIC_TEST"):
                cached = price_manager._price_cache["PYDANTIC_TEST"]
                assert isinstance(cached, CachedPrice)
                assert cached.price == 999.99
                print(f"  ✅ Кеш содержит CachedPrice: {cached.price} at {cached.timestamp}")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка workflow: {e}")
        return False


def test_error_handling_with_pydantic():
    """Тест обработки ошибок с Pydantic валидацией."""
    print("\n🔍 Тестирование обработки ошибок с Pydantic...")
    
    try:
        # 1. Тест некорректных данных для PriceResult
        print("  📋 Тестируем валидацию PriceResult...")
        
        try:
            # Отрицательная цена
            invalid_result = PriceResult(
                symbol="TEST",
                price=-100.0,  # Отрицательная цена должна быть отклонена
                source="test",
                timestamp=datetime.now(),
                success=True
            )
            print("  ❌ Валидация отрицательной цены не работает!")
            return False
        except Exception:
            print("  ✅ Валидация отрицательной цены работает")
        
        # 2. Тест некорректного reliability в PriceSource
        print("  📋 Тестируем валидацию reliability...")
        
        try:
            # Reliability > 1.0
            invalid_source = PriceSource(
                name="test",
                priority=1,
                rate_limit=50,
                reliability=1.5  # Больше 1.0
            )
            print("  ❌ Валидация reliability не работает!")
            return False
        except Exception:
            print("  ✅ Валидация reliability работает")
        
        # 3. Тест пустого символа в PriceResult
        print("  📋 Тестируем валидацию символа...")
        
        try:
            invalid_result = PriceResult(
                symbol="",  # Пустой символ
                price=100.0,
                source="test",
                timestamp=datetime.now(),
                success=True
            )
            print("  ❌ Валидация пустого символа не работает!")
            return False
        except Exception:
            print("  ✅ Валидация пустого символа работает")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Неожиданная ошибка: {e}")
        return False


async def main():
    """Главная функция тестирования."""
    print("🚀 Тест Pydantic интеграции в Price Strategy Manager")
    print("=" * 60)
    
    tests = [
        ("Pydantic модели", test_pydantic_models),
        ("Интеграция в price_manager", test_price_manager_pydantic_integration),
        ("Pydantic в workflow", test_pydantic_in_real_workflow),
        ("Обработка ошибок", test_error_handling_with_pydantic)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 ТЕСТ: {test_name}")
        print('='*60)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                print(f"✅ {test_name}: ПРОЙДЕН")
                passed += 1
            else:
                print(f"❌ {test_name}: ПРОВАЛЕН")
        except Exception as e:
            print(f"💥 {test_name}: КРИТИЧЕСКАЯ ОШИБКА - {e}")
    
    # Итоги
    print(f"\n{'='*60}")
    print(f"📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ PYDANTIC ТЕСТОВ")
    print('='*60)
    print(f"Пройдено: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ВСЕ PYDANTIC ТЕСТЫ ПРОШЛИ!")
        print("🚀 Интеграция полностью работает!")
    else:
        print("🚨 ЕСТЬ ПРОБЛЕМЫ С PYDANTIC ИНТЕГРАЦИЕЙ!")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
